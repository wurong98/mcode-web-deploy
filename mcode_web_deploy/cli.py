import argparse
import json
import sys
from pathlib import Path

from .deployer import DeployError, deploy


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="mcode-deploy",
        description="Zero-Token Direct Static Web Deploy Tool for MiniMax (mcode) space hosting.",
    )
    parser.add_argument(
        "project_dir",
        nargs="?",
        default=".",
        help="Project directory (default: current working directory)",
    )
    parser.add_argument(
        "--dist",
        help="Build output directory (default auto-detected: dist, build, out, public, or project root)",
    )
    parser.add_argument(
        "--name",
        help="Project display name (defaults to 'name' in package.json or directory name)",
    )
    parser.add_argument(
        "--update",
        help="Existing node_id to update in-place (keeps the public URL unchanged)",
    )
    parser.add_argument(
        "--token",
        help="Explicit MiniMax access token (defaults to MINIMAX_ACCESS_TOKEN env or local auth)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result strictly in JSON format (ideal for Agent/automation integration)",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress progress messages, only print final URL",
    )

    args = parser.parse_args(argv)

    def log_progress(stage, msg):
        if not args.json and not args.quiet:
            print(f"[{stage}] {msg}")

    try:
        if not args.json and not args.quiet:
            print("🚀 mcode-deploy: Direct Web Deploy (Zero-Token)")

        result = deploy(
            project_dir=Path(args.project_dir),
            dist_dir=args.dist,
            name=args.name,
            update_node_id=args.update,
            token=args.token,
            on_progress=log_progress,
        )

        if args.json:
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        elif args.quiet:
            print(result.url)
        else:
            print("\n" + "=" * 50)
            print("🎉 DEPLOYMENT SUCCESSFUL! (Tokens Consumed: 0)")
            print(f"🌐 Public URL: {result.url}")
            print(f"🆔 Node ID:    {result.node_id}")
            print(f"📁 Name:       {result.project_name}")
            print("=" * 50)
            if not result.is_update:
                print("Tip: Update this site later with:")
                print(f"  mcode-deploy {args.project_dir} --update {result.node_id}")

        sys.exit(0)

    except DeployError as e:
        if args.json:
            err_dict = {"success": False, "error": str(e), "code": e.code, "detail": e.detail}
            print(json.dumps(err_dict, ensure_ascii=False, indent=2), file=sys.stderr)
        else:
            print(f"\n❌ [Deploy Error]: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        if args.json:
            print(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False), file=sys.stderr)
        else:
            print(f"\n❌ [Unexpected Error]: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
