# mcode-web-deploy

> 🚀 **零 LLM Token 消耗、极速（< 2s）直连 MiniMax（mcode）静态网页发布工具**。
> 专门解决：**在拥有 `mcode` 环境的前提下，让其他 AI Agent（Claude Code, Cursor, Windsurf, Cline 等）、开发者或 CI/CD 流水线，能够极速、确定性地将静态网站发布到公网并生成在线分享链接。**

---

## 💡 为什么需要这个工具？

在默认的 MiniMax `mcode` 工具链中，如果要发布网页，传统的脚本通常是让大模型自己跑（例如调用 `mcode exec` 启动一个 headless Agent）：
- ❌ **白白浪费 Token**：每次发布都需要经历大模型上下文组装、思考、Tool Call，白白浪费 2,000 ~ 3,000 大模型 Token；
- ❌ **速度慢**：耗时 10 ~ 15 秒以上；
- ❌ **易被拦截**：自动化/非交互终端环境下可能遭遇权限拦截或模型幻觉导致发布失败；
- ❌ **外部 Agent 无法复用**：如果开发者正在使用 **Claude Code**、**Cursor**、**Windsurf** 等其他 Agent，无法简单轻便地让这些 Agent 一键帮自己发布网页并拿到公网链接。

### ✨ 本工具的解决方案
通过对底层协议的逆向还原，剥离大模型中间层，直接与后端 API 进行纯 HTTP/OSS 交互：
- ⚡ **0 Token 消耗**：完全不经过任何大模型推理；
- ⚡ **极速发布**：全流程（打包 -> 获取签名 -> OSS 直传 -> CDN 注册）从 15 秒缩短至 **2 秒以内**；
- ⚡ **零第三方依赖**：纯 Python 3 原生标准库（`urllib`, `zipfile`, `json`），开箱即用；
- ⚡ **Agent 友好**：提供 `--json` 规范输出和单行 Bash 指令，其他 Agent 调它就像调 `curl` 一样稳定可靠；
- ⚡ **支持原地更新**：传入 `--update <node_id>` 即可无缝覆盖更新网站，保持公网 URL 不变；
- ⚡ **双命令支持**：标准命令 `mcode-web-deploy`（无歧义），同时提供短别名 `mcode-deploy`。

---

## 🛠️ 底层协议原理

```
[ 本地项目 / 构建产物 ]
          │
          ▼ (1) POST /mavis/api/v1/mcp/get_upload_url
[ 获取 OSS 预签名上传链接 ]
          │
          ▼ (2) PUT 二进制流直传阿里云 OSS
[ dist.zip & source.zip 极速上传 ]
          │
          ▼ (3) POST /mavis/api/v1/drive/websites/publish_archive (或 update_archive)
[ MiniMax CDN 节点注册/绑定 ]
          │
          ▼
🎉 生成公网访问地址 (https://xxx.space.mcode.cn)
```

---

## 📦 安装与配置

### 方式 1：全局安装（推荐）
在项目目录下执行：
```bash
git clone https://github.com/wurong98/mcode-web-deploy.git
cd mcode-web-deploy
./install.sh
```
该脚本会自动在 `/usr/local/bin` 安装主命令 `mcode-web-deploy` 与短别名 `mcode-deploy`。

### 方式 2：Python pip 安装
```bash
pip install .
```

### 方式 3：单文件直接运行（免安装）
```bash
python3 /path/to/mcode-web-deploy/bin/mcode-web-deploy [options]
```

---

## 🔑 认证凭证配置

本工具支持以下两种免登录认证模式：

1. **自动复用本机 mcode 登录凭证（最省心）**：
   - 只要你的电脑上曾经执行过 `mcode login`，本工具会自动检测并读取 `~/.minimax/local-runtime.auth.json`。
   - 无需进行任何额外配置，直接运行！
2. **环境变量模式（适用于 CI/CD 或 Docker）**：
   ```bash
   export MINIMAX_ACCESS_TOKEN="your_access_token_here"
   ```

---

## 🚀 使用指南

### 1. 命令行快速使用

```bash
# 1. 部署当前目录下的网站（自动寻找 dist/build/out 或当前目录下的 index.html）
mcode-web-deploy

# 2. 部署指定项目目录
mcode-web-deploy ./my-vue-project

# 3. 指定构建目录与自定义项目名称
mcode-web-deploy ./my-app --dist dist --name "Awesome App"

# 4. 原地更新已有站点（保持 URL 不变）
mcode-web-deploy ./my-app --update <node_id>

# 5. 纯静音模式（只输出最终 URL，方便管道组合）
mcode-web-deploy -q
```

> 💡 **提示**：所有命令中的 `mcode-web-deploy` 均可缩写为 `mcode-deploy`。

### 2. 参数一览

| 参数 | 说明 |
| :--- | :--- |
| `project_dir` | 项目目录路径（默认为当前目录 `.`） |
| `--dist <dir>` | 产物目录（默认自动探测 `dist`, `build`, `out`, `public` 或根目录） |
| `--name <name>` | 站点项目名（默认优先读取 `package.json` 中的 `name`，其次为文件夹名） |
| `--update <id>` | 指定要更新的 `node_id`，实现原地更新且 URL 不变 |
| `--token <token>` | 手动传入 MiniMax Access Token |
| `--json` | 输出机器可读的 JSON 格式（Agent 必选） |
| `-q, --quiet` | 静音模式，仅打印最终的公网访问 URL |

---

## 🤖 让 Claude Code 等 AI Agent 接入

为了让 **Claude Code**、**Cursor**、**Windsurf**、**Cline** 等 Agent 能够自动识别意图并在需要时自动调用部署，推荐以下两种接入方式：

### 方案 A：配置为 Claude Code 专用 Skill（最丝滑推荐 ⭐⭐⭐⭐⭐）

Claude Code 原生支持 **Skills**（技能机制）。只需在当前项目（或全局用户目录）添加 `deploy-web` skill，当你对 Claude Code 说“把网页发布一下”、“部署上线”、“生成分享链接”时，Claude 会自动按最佳流程执行：

#### 1. 全局配置（所有项目随时可用）
```bash
# 创建全局技能目录并复制 Skill
mkdir -p ~/.claude/skills
cp -r skills/deploy-web ~/.claude/skills/
```

#### 2. 项目级配置（随当前代码库分发）
本项目已内置 `.claude/skills/deploy-web.md`，你也可以直接复制到其他工程的 `.claude/skills/` 中。

> **效果体验**：你在 Claude Code 里直接说：
> > “帮我把做好的网站部署上线”
> 
> Claude 会自动触发 `deploy-web` 技能，先探测或执行 build，然后调用 `mcode-web-deploy . --json`，并把生成的公网 URL 以 Markdown 链接展示给你！

---

### 方案 B：写入规则文件（支持 Claude / Cursor / Windsurf / Cline 通用）

在任意项目根目录的 `CLAUDE.md` 或 `.cursorrules` 中加入：

```markdown
## 网页发布与分享 (Web Deployment)
本项目配置了 `mcode-web-deploy` 工具，用于将静态网页极速发布到 MiniMax 托管空间：
- **构建后发布**：`npm run build && mcode-web-deploy --json`
- **单 HTML 快速发布**：`mcode-web-deploy . --json`
- **原地更新站点**：`mcode-web-deploy . --update <node_id> --json`
- **命令输出解析**：`--json` 会返回 `{"success": true, "url": "...", "node_id": "..."}`，请将 `url` 展示给用户。
```

### Agent 调用示例与 JSON 返回结构

执行：
```bash
mcode-web-deploy ./dist-project --json
```

返回（直接在标准输出解析）：
```json
{
  "success": true,
  "url": "https://xyz123.space.mcode.cn",
  "node_id": "node_9876543210",
  "project_name": "my-demo-site",
  "is_update": false,
  "dist_size": 245100,
  "source_size": 892140
}
```

---

## 🐍 Python SDK 调用方式

除了 CLI，你还可以在你自己的 Python 脚本中直接导入：

```python
from pathlib import Path
from mcode_web_deploy import deploy

result = deploy(
    project_dir=Path("./my-app"),
    dist_dir="dist",
    name="my-app",
    # update_node_id="node_xxx" # 可选：原地更新
)

if result.success:
    print(f"站点已上线: {result.url}")
    print(f"节点 ID: {result.node_id}")
```

---

## 📄 开源许可证

MIT License.
