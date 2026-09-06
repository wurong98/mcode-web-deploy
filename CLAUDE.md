# CLAUDE.md for mcode-web-deploy

This file provides guidance to Claude Code and other AI coding assistants when working on this project.

## Project Overview
`mcode-web-deploy` is a lightweight, zero-LLM/zero-token tool for publishing static websites to MiniMax (mcode) space hosting directly via backend APIs.

## Architecture
- `mcode_web_deploy/deployer.py`: Core deployment logic (packaging, pre-signed OSS URL requests, OSS direct uploads, CDN registration/updating).
- `mcode_web_deploy/cli.py`: Command-line interface with `--json`, `--quiet`, `--update`, and auto-detection features.
- `bin/mcode-web-deploy`: Standalone executable entry script.
- `tests/test_deployer.py`: Unit tests using standard Python `unittest`.

## Commands
- Run tests: `python3 -m unittest discover tests`
- Run CLI locally: `python3 bin/mcode-web-deploy --help`
- Run with JSON output: `python3 bin/mcode-web-deploy <path> --json`
