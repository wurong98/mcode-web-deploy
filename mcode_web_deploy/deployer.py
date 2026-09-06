import io
import json
import os
import sys
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Set, Tuple

DEFAULT_BASE_URL = "https://agent.minimax.cn"
DEFAULT_USER_AGENT = "MiniMaxAgent"

DEFAULT_IGNORE_NAMES: Set[str] = {
    ".git",
    "node_modules",
    ".DS_Store",
    ".env",
    ".env.local",
    "dist",
    ".next",
    ".turbo",
    "__pycache__",
    ".venv",
    ".idea",
    ".vscode",
}


class DeployError(Exception):
    """Raised when a deployment step fails."""

    def __init__(self, message: str, code: Optional[int] = None, detail: Optional[str] = None):
        super().__init__(message)
        self.code = code
        self.detail = detail


@dataclass
class DeployResult:
    success: bool
    url: str
    node_id: str
    project_name: str
    is_update: bool
    dist_size: int
    source_size: int

    def to_dict(self):
        return {
            "success": self.success,
            "url": self.url,
            "node_id": self.node_id,
            "project_name": self.project_name,
            "is_update": self.is_update,
            "dist_size": self.dist_size,
            "source_size": self.source_size,
        }


def load_access_token() -> str:
    """
    Load access token from environment variables or local auth configuration files.
    """
    # 1. Check environment variables
    env_token = os.environ.get("MINIMAX_ACCESS_TOKEN") or os.environ.get("MCODE_TOKEN")
    if env_token and env_token.strip():
        return env_token.strip()

    # 2. Check candidate local auth paths
    candidate_paths = [
        os.path.expanduser("~/.minimax/local-runtime.auth.json"),
        os.path.expanduser("~/.minimax/cli-auth/prod/cn/local-runtime.auth.json"),
        os.path.expanduser("~/.minimax/cli-auth/prod/global/local-runtime.auth.json"),
    ]

    for auth_path in candidate_paths:
        if os.path.exists(auth_path):
            try:
                with open(auth_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    token = data.get("auth", {}).get("accessToken")
                    if token and token.strip():
                        return token.strip()
            except Exception:
                continue

    raise DeployError(
        "No MiniMax authentication token found. "
        "Please login via 'mcode login' or set MINIMAX_ACCESS_TOKEN environment variable."
    )


def zip_directory(directory_path: Path, ignore_set: Optional[Set[str]] = None) -> bytes:
    """
    Pack directory into in-memory zip bytes.
    """
    buffer = io.BytesIO()
    dir_path = directory_path.resolve()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for root, dirs, files in os.walk(dir_path):
            if ignore_set:
                dirs[:] = [d for d in dirs if d not in ignore_set and not d.startswith(".git")]
            for file in files:
                if ignore_set and file in ignore_set:
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, dir_path)
                zf.write(full_path, rel_path)

    return buffer.getvalue()


def _request_json(url: str, payload: dict, token: str, timeout: int = 30) -> dict:
    headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8") if e.fp else ""
        raise DeployError(f"HTTP {e.code} request failed: {err_body}", code=e.code, detail=err_body)
    except Exception as e:
        raise DeployError(f"Network request error: {e}")


def get_upload_url(
    filename: str, size_bytes: int, token: str, base_url: str = DEFAULT_BASE_URL
) -> Tuple[str, str]:
    url = f"{base_url}/mavis/api/v1/mcp/get_upload_url"
    payload = {
        "filename": filename,
        "mime_type": "application/zip",
        "size_bytes": size_bytes,
        "category": "website",
    }
    resp = _request_json(url, payload, token)
    if resp.get("code", 0) != 0 or not resp.get("put_url") or not resp.get("oss_key"):
        msg = resp.get("message") or resp.get("error") or "Failed to get upload URL"
        raise DeployError(f"get_upload_url failed: {msg}")
    return resp["put_url"], resp["oss_key"]


def upload_to_oss(put_url: str, zip_bytes: bytes, timeout: int = 60):
    req = urllib.request.Request(
        put_url,
        data=zip_bytes,
        method="PUT",
        headers={
            "Content-Type": "application/zip",
            "Content-Length": str(len(zip_bytes)),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status not in (200, 204):
                raise DeployError(f"OSS upload returned unexpected HTTP status: {resp.status}")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8") if e.fp else ""
        raise DeployError(f"OSS upload failed HTTP {e.code}: {err_body}", code=e.code, detail=err_body)
    except Exception as e:
        raise DeployError(f"OSS upload network error: {e}")


def resolve_project_and_dist(
    project_dir: Path, dist_option: Optional[str] = None
) -> Tuple[Path, Path]:
    project_dir = project_dir.resolve()
    if not project_dir.is_dir():
        raise DeployError(f"Project directory does not exist: {project_dir}")

    if dist_option:
        dist_dir = Path(dist_option)
        if not dist_dir.is_absolute():
            dist_dir = project_dir / dist_dir
    else:
        # Check standard default build folders
        candidates = [project_dir / "dist", project_dir / "build", project_dir / "out", project_dir / "public"]
        dist_dir = None
        for cand in candidates:
            if cand.is_dir() and (cand / "index.html").is_file():
                dist_dir = cand
                break

        if not dist_dir:
            # Check if root directory contains index.html
            if (project_dir / "index.html").is_file():
                dist_dir = project_dir
            else:
                dist_dir = project_dir / "dist"

    if not dist_dir.is_dir():
        raise DeployError(
            f"Build output directory not found: {dist_dir}\n"
            f"Hint: Run 'npm run build' first, or specify directory with --dist."
        )

    if not (dist_dir / "index.html").is_file():
        raise DeployError(
            f"Missing index.html in: {dist_dir}\n"
            f"Make sure your build artifact or static directory contains index.html."
        )

    return project_dir, dist_dir


def detect_project_name(project_dir: Path, explicit_name: Optional[str] = None) -> str:
    if explicit_name and explicit_name.strip():
        return explicit_name.strip()

    pkg_file = project_dir / "package.json"
    if pkg_file.is_file():
        try:
            with open(pkg_file, "r", encoding="utf-8") as f:
                name = json.load(f).get("name")
                if name and isinstance(name, str):
                    return name.strip()
        except Exception:
            pass

    return project_dir.name or "my-website"


def deploy(
    project_dir: Path,
    dist_dir: Optional[str] = None,
    name: Optional[str] = None,
    update_node_id: Optional[str] = None,
    token: Optional[str] = None,
    base_url: str = DEFAULT_BASE_URL,
    on_progress: Optional[callable] = None,
) -> DeployResult:
    """
    Deploy or update a website without running an LLM.
    """
    def log(stage: str, msg: str):
        if on_progress:
            on_progress(stage, msg)

    if not token:
        token = load_access_token()

    proj_dir, build_dist_dir = resolve_project_and_dist(project_dir, dist_dir)
    project_name = detect_project_name(proj_dir, name)

    log("pack_dist", f"Zipping build directory: {build_dist_dir}")
    site_zip = zip_directory(build_dist_dir)

    log("pack_source", f"Zipping project source: {proj_dir}")
    source_zip = zip_directory(proj_dir, ignore_set=DEFAULT_IGNORE_NAMES)

    log("upload_dist", f"Uploading build archive ({len(site_zip):,} bytes)...")
    dist_put_url, dist_oss_key = get_upload_url(f"{project_name}-site.zip", len(site_zip), token, base_url)
    upload_to_oss(dist_put_url, site_zip)

    log("upload_source", f"Uploading source archive ({len(source_zip):,} bytes)...")
    src_put_url, src_oss_key = get_upload_url(f"{project_name}-source.zip", len(source_zip), token, base_url)
    upload_to_oss(src_put_url, source_zip)

    log("register", "Publishing website to MiniMax CDN...")
    if update_node_id:
        endpoint = f"{base_url}/mavis/api/v1/drive/websites/update_archive"
        payload = {
            "node_id": str(update_node_id),
            "oss_key": dist_oss_key,
            "source_oss_key": src_oss_key,
            "project_name": project_name,
        }
    else:
        endpoint = f"{base_url}/mavis/api/v1/drive/websites/publish_archive"
        payload = {
            "oss_key": dist_oss_key,
            "source_oss_key": src_oss_key,
            "project_name": project_name,
        }

    resp = _request_json(endpoint, payload, token)

    code = resp.get("base_resp", {}).get("status_code", resp.get("code", 0))
    if code != 0:
        msg = resp.get("base_resp", {}).get("status_msg", resp.get("message", "Publish request failed"))
        raise DeployError(f"Publish failed (code {code}): {msg}", code=code)

    node_data = resp.get("node") or resp
    cdn_url = node_data.get("cdn_url") or resp.get("cdn_url") or ""
    final_node_id = node_data.get("node_id") or resp.get("node_id") or (update_node_id or "")

    return DeployResult(
        success=True,
        url=cdn_url,
        node_id=str(final_node_id),
        project_name=project_name,
        is_update=bool(update_node_id),
        dist_size=len(site_zip),
        source_size=len(source_zip),
    )
