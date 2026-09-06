---
name: deploy-web
description: Build and deploy the project's static website to MiniMax space CDN using mcode-web-deploy, returning a public URL. Triggers on "deploy", "publish website", "share link", "发布网站", "部署网页", "上线".
---

# Deploy Web Skill

Deploy the static web project or build artifacts to MiniMax public CDN via `mcode-web-deploy`.

## Workflow

1. **Detect Build System & Build**:
   - If `package.json` has a `build` script, run `npm run build` (or `pnpm run build` / `yarn build`).
   - If it's a pure static project (already has `index.html`), skip building.

2. **Execute Deployment**:
   Run `mcode-web-deploy` with `--json` for machine-readable output:
   ```bash
   mcode-web-deploy . --json
   ```

   - If updating an existing site, pass `--update <node_id>`.
   - If the build output is in a custom directory, pass `--dist <path>`.

3. **Parse & Present**:
   - Parse the JSON output from stdout.
   - Extract `url` and `node_id`.
   - Present the deployment result cleanly to the user with a clickable link and node ID for future updates.
