# Agent Directives: Web Deployment (mcode-web-deploy)

This project / workspace is equipped with `mcode-web-deploy`, a zero-LLM-token static web deployment tool that publishes sites directly to the public MiniMax CDN space (`https://<id>.space.mcode.cn`).

Any AI agent (Claude Code, Codex, agy, Cursor, Windsurf, Cline) can trigger web deployment for the user.

---

## Trigger Conditions
Use this capability whenever the user asks to:
- Deploy, publish, host, or share a website ("部署网页", "发布网站", "生成在线分享链接", "给我一个公网链接")
- Preview or verify the built web application on a public URL

---

## Standard Workflow

### 1. Detect & Run Build (if applicable)
- Check `package.json`: if there is a `build` script and build artifacts (`dist/`, `build/`, `out/`) are missing or outdated, run the build command first:
  ```bash
  npm run build # or pnpm build / yarn build
  ```
- If the project is pure static HTML/CSS/JS (e.g., `index.html` at the project root), skip the build step.

### 2. Execute Deployment
Run `mcode-web-deploy` via bash with `--json` for machine-readable output:
```bash
mcode-web-deploy . --json
```

- **In-place update**: If updating an existing site (or user provided a `node_id`), pass `--update`:
  ```bash
  mcode-web-deploy . --update <node_id> --json
  ```
- **Custom build output**: If build artifacts are in a non-standard folder:
  ```bash
  mcode-web-deploy . --dist <path_to_dist> --json
  ```

### 3. Handle Output
The command returns JSON to stdout:
```json
{
  "success": true,
  "url": "https://xxx.space.mcode.cn",
  "node_id": "node_9876543210",
  "project_name": "my-demo-site",
  "is_update": false
}
```
- Present the public `url` as a clickable Markdown link to the user.
- Show the `node_id` so the user or agent can update the site in-place later.
