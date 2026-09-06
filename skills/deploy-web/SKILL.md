---
name: deploy-web
description: Build and deploy the project's static website to MiniMax space CDN using mcode-web-deploy, returning a public URL. Triggers on "deploy", "publish website", "share link", "发布网站", "部署网页", "上线".
---

# Deploy Web Skill

Deploy the static web project or build artifacts to MiniMax public CDN via `mcode-web-deploy`.

## When to use
Use this skill whenever the user asks to deploy, publish, host, or share a web application, demo, or static page.

## Workflow

1. **Verify or Run Build**:
   - Check if the project requires a build step (e.g. React/Vue/Vite/Next.js export).
   - If `package.json` contains a `build` script and the build folder (`dist/`, `build/`, `out/`) does not exist or is outdated, run the build command (e.g. `npm run build` or `pnpm build`).
   - If the project is a pure static HTML/CSS/JS directory (with `index.html` at root), no build step is needed.

2. **Execute Deployment**:
   Execute `mcode-web-deploy` using the Bash tool with `--json`:
   ```bash
   mcode-web-deploy . --json
   ```

   - **Updating an existing site**: If user provides a `node_id` or there is a known previous deployment, run:
     ```bash
     mcode-web-deploy . --update <node_id> --json
     ```
   - **Custom output directory**: If the build directory is non-standard, use `--dist`:
     ```bash
     mcode-web-deploy . --dist <path_to_dist> --json
     ```

3. **Handle Response**:
   The command outputs JSON:
   ```json
   {
     "success": true,
     "url": "https://xxx.space.mcode.cn",
     "node_id": "node_xxx",
     "project_name": "my-app",
     "is_update": false
   }
   ```
   - On success: Output the live public `url` (formatted as a clickable Markdown link) and report the `node_id`.
   - On error: Report the error message clearly to the user.
