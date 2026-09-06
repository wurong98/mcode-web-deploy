#!/usr/bin/env bash
# ==============================================================================
# install.sh - Robust installer for mcode-web-deploy CLI and Agent Skills
#
# Design principles (aligned with modern CLI installers like uv / rustup):
#  1. Safe defaults: Installs to ~/.local/bin by default (no root / no sudo).
#  2. Custom prefix: Respects PREFIX (installed to $PREFIX/bin) or BIN_DIR.
#  3. Safe copy: Default to copying full package/binary, not fragile symlinks.
#  4. Non-destructive: Existing files are NOT overwritten unless --force is given.
#  5. Dual-mode ready: Works both as repo-local install and curl | bash remote install.
#  6. Environment checks: Inspects PATH and gives clear remediation instructions.
# ==============================================================================
set -euo pipefail

REPO_RAW_URL="https://raw.githubusercontent.com/wurong98/mcode-web-deploy/master"
FORCE=0
SYMLINK=0

usage() {
    cat <<EOF
Usage: install.sh [OPTIONS]

Options:
  --force           Overwrite existing installed files
  --symlink         Install via symlink to repo (repo-local mode only, for development)
  --prefix <DIR>    Set base installation prefix (binary goes to <DIR>/bin)
  --bin-dir <DIR>   Set explicit binary installation directory
  -h, --help        Show this help message

Environment Variables:
  PREFIX            Base prefix directory (default: ~/.local)
  BIN_DIR           Explicit binary directory (overrides PREFIX/bin)
  FORCE             Set to 1 to force overwrite existing files
EOF
    exit 0
}

# Parse CLI arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --force|-f)
            FORCE=1
            shift
            ;;
        --symlink|-s)
            SYMLINK=1
            shift
            ;;
        --prefix)
            PREFIX="$2"
            shift 2
            ;;
        --bin-dir)
            BIN_DIR="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Error: Unknown option '$1'" >&2
            echo "Run 'install.sh --help' for usage." >&2
            exit 1
            ;;
    esac
done

if [[ "${FORCE:-0}" == "1" ]]; then
    FORCE=1
fi

# Detect whether running repo-locally or piped via curl
IS_LOCAL=0
SCRIPT_DIR=""
if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
    # Resolve physical directory of the script
    SOURCE_PATH="${BASH_SOURCE[0]}"
    while [ -h "$SOURCE_PATH" ]; do
        TARGET="$(readlink "$SOURCE_PATH")"
        if [[ "$TARGET" == /* ]]; then
            SOURCE_PATH="$TARGET"
        else
            SOURCE_PATH="$(dirname "$SOURCE_PATH")/$TARGET"
        fi
    done
    SCRIPT_DIR="$(cd -P "$(dirname "$SOURCE_PATH")" && pwd)"
    if [ -f "$SCRIPT_DIR/mcode_web_deploy/__init__.py" ]; then
        IS_LOCAL=1
    fi
fi

# Determine target binary directory
if [ -n "${BIN_DIR:-}" ]; then
    TARGET_BIN="$BIN_DIR"
elif [ -n "${PREFIX:-}" ]; then
    TARGET_BIN="$PREFIX/bin"
else
    TARGET_BIN="${HOME}/.local/bin"
fi

echo "=================================================="
echo "  Installing mcode-web-deploy"
echo "=================================================="
echo "• Target bin dir: $TARGET_BIN"
if [ "$IS_LOCAL" -eq 1 ]; then
    echo "• Mode:           Local repository ($SCRIPT_DIR)"
else
    echo "• Mode:           Remote standalone (curl | bash)"
fi
echo ""

# Ensure target bin directory exists
mkdir -p "$TARGET_BIN"

TARGET_FILE="$TARGET_BIN/mcode-web-deploy"

# Function to safely install a file (honoring --force)
safe_install_file() {
    local src="$1"
    local dest="$2"
    local mode="${3:-644}"

    if [ -e "$dest" ] || [ -L "$dest" ]; then
        if [ "$FORCE" -ne 1 ]; then
            echo "   ⚠️  Skipping '$dest' (already exists, use --force to overwrite)"
            return 0
        fi
    fi

    mkdir -p "$(dirname "$dest")"
    cp -f "$src" "$dest"
    chmod "$mode" "$dest"
    echo "   ✅ $dest"
}

# Function to safely create a symlink (honoring --force)
safe_symlink_file() {
    local src="$1"
    local dest="$2"

    if [ -e "$dest" ] || [ -L "$dest" ]; then
        if [ "$FORCE" -ne 1 ]; then
            echo "   ⚠️  Skipping '$dest' (already exists, use --force to overwrite)"
            return 0
        fi
        rm -f "$dest"
    fi

    mkdir -p "$(dirname "$dest")"
    ln -sf "$src" "$dest"
    echo "   ✅ $dest (symlink -> $src)"
}

# 1. Install CLI
echo "1. Installing CLI executable..."

if [ "$IS_LOCAL" -eq 1 ]; then
    if [ "$SYMLINK" -eq 1 ]; then
        safe_symlink_file "$SCRIPT_DIR/bin/mcode-web-deploy" "$TARGET_FILE"
    else
        # Package into a standalone self-contained executable (zipapp)
        TEMP_ZIPAPP="$(mktemp /tmp/mcode-web-deploy.XXXXXX)"
        python3 -c "
import zipfile, os, sys
from pathlib import Path

script_dir = Path('$SCRIPT_DIR').resolve()
temp_file = Path('$TEMP_ZIPAPP')

with zipfile.ZipFile(temp_file, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
    # write package files
    pkg_dir = script_dir / 'mcode_web_deploy'
    for f in pkg_dir.rglob('*.py'):
        zf.write(f, arcname=f.relative_to(script_dir))
    # write entry point __main__.py
    entry = 'from mcode_web_deploy.cli import main\nif __name__ == \"__main__\":\n    main()\n'
    zf.writestr('__main__.py', entry)

# Prepend shebang
data = temp_file.read_bytes()
temp_file.write_bytes(b'#!/usr/bin/env python3\n' + data)
"
        safe_install_file "$TEMP_ZIPAPP" "$TARGET_FILE" 755
        rm -f "$TEMP_ZIPAPP"
    fi
else
    # Remote curl | bash mode: download the repository archive or package
    TEMP_DIR="$(mktemp -d /tmp/mcode-web-deploy-install.XXXXXX)"
    echo "   ⬇️  Fetching source package from GitHub..."
    ARCHIVE_URL="https://github.com/wurong98/mcode-web-deploy/archive/refs/heads/master.tar.gz"

    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "$ARCHIVE_URL" -o "$TEMP_DIR/repo.tar.gz"
    elif command -v wget >/dev/null 2>&1; then
        wget -q "$ARCHIVE_URL" -O "$TEMP_DIR/repo.tar.gz"
    else
        echo "Error: curl or wget is required for remote installation." >&2
        rm -rf "$TEMP_DIR"
        exit 1
    fi

    tar -xzf "$TEMP_DIR/repo.tar.gz" -C "$TEMP_DIR"
    EXTRACTED_DIR="$TEMP_DIR/mcode-web-deploy-master"

    # Build zipapp
    TEMP_ZIPAPP="$(mktemp /tmp/mcode-web-deploy.XXXXXX)"
    python3 -c "
import zipfile, os
from pathlib import Path

src_dir = Path('$EXTRACTED_DIR')
temp_file = Path('$TEMP_ZIPAPP')

with zipfile.ZipFile(temp_file, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
    pkg_dir = src_dir / 'mcode_web_deploy'
    for f in pkg_dir.rglob('*.py'):
        zf.write(f, arcname=f.relative_to(src_dir))
    entry = 'from mcode_web_deploy.cli import main\nif __name__ == \"__main__\":\n    main()\n'
    zf.writestr('__main__.py', entry)

data = temp_file.read_bytes()
temp_file.write_bytes(b'#!/usr/bin/env python3\n' + data)
"
    safe_install_file "$TEMP_ZIPAPP" "$TARGET_FILE" 755
    rm -f "$TEMP_ZIPAPP"

    # Re-point SCRIPT_DIR for skill installation
    SCRIPT_DIR="$EXTRACTED_DIR"
fi

# 2. Install Universal Skills
echo ""
echo "2. Installing Universal Skill to Agent environments..."
SKILL_SRC="$SCRIPT_DIR/skills/mcode-web-deploy/SKILL.md"

# Backward compatibility with older branches/archives where it was skills/deploy-web
if [ ! -f "$SKILL_SRC" ] && [ -f "$SCRIPT_DIR/skills/deploy-web/SKILL.md" ]; then
    SKILL_SRC="$SCRIPT_DIR/skills/deploy-web/SKILL.md"
fi

if [ -f "$SKILL_SRC" ]; then
    # (A) Claude Code (~/.claude/skills)
    if [ -d "$HOME/.claude" ]; then
        safe_install_file "$SKILL_SRC" "$HOME/.claude/skills/mcode-web-deploy/SKILL.md" 644
    fi

    # (B) Codex (~/.codex/skills)
    if [ -d "$HOME/.codex" ]; then
        safe_install_file "$SKILL_SRC" "$HOME/.codex/skills/mcode-web-deploy/SKILL.md" 644
    fi

    # (C) General Agent Skills directory (~/.local/share/agent-skills)
    safe_install_file "$SKILL_SRC" "$HOME/.local/share/agent-skills/mcode-web-deploy/SKILL.md" 644
else
    echo "   ⚠️  Skill definition file not found at $SKILL_SRC, skipping."
fi

# Clean up remote temp dir if allocated
if [ -n "${TEMP_DIR:-}" ] && [ -d "$TEMP_DIR" ]; then
    rm -rf "$TEMP_DIR"
fi

# 3. Environment and PATH inspection
echo ""
echo "=================================================="
echo "🎉 Installation completed!"
echo "=================================================="

# Check whether TARGET_BIN is in PATH
if [[ ":$PATH:" != *":$TARGET_BIN:"* ]]; then
    echo "⚠️  WARNING: '$TARGET_BIN' is not in your current PATH."
    echo "   To use 'mcode-web-deploy' directly from your shell, add this to your profile:"
    echo ""
    if [ -f "$HOME/.zshrc" ]; then
        echo "   echo 'export PATH=\"$TARGET_BIN:\$PATH\"' >> ~/.zshrc && source ~/.zshrc"
    else
        echo "   echo 'export PATH=\"$TARGET_BIN:\$PATH\"' >> ~/.bashrc && source ~/.bashrc"
    fi
    echo ""
else
    echo "✅ Executable directory '$TARGET_BIN' is already in your PATH."
fi

echo "You can test the installation with:"
echo "   $TARGET_BIN/mcode-web-deploy --help"
