#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="/usr/local/bin"

install_link() {
    local src="$1"
    local dest="$2"
    if [ ! -w "$TARGET_DIR" ]; then
        sudo ln -sf "$src" "$dest"
    else
        ln -sf "$src" "$dest"
    fi
}

echo "1. Installing mcode-web-deploy CLI to $TARGET_DIR..."
install_link "$DIR/bin/mcode-web-deploy" "$TARGET_DIR/mcode-web-deploy"
install_link "$DIR/bin/mcode-web-deploy" "$TARGET_DIR/mcode-deploy"
echo "   ✅ $TARGET_DIR/mcode-web-deploy (primary)"
echo "   ✅ $TARGET_DIR/mcode-deploy (alias)"

echo ""
echo "2. Installing Universal Skill to Agent environments..."
SKILL_DIR="$DIR/skills/deploy-web"

# (A) Claude Code (~/.claude/skills)
if [ -d "$HOME/.claude" ]; then
    mkdir -p "$HOME/.claude/skills"
    cp "$SKILL_DIR/SKILL.md" "$HOME/.claude/skills/deploy-web.md"
    echo "   ✅ Claude Code: ~/.claude/skills/deploy-web.md"
fi

# (B) Codex (~/.codex/skills)
if [ -d "$HOME/.codex" ]; then
    mkdir -p "$HOME/.codex/skills/deploy-web"
    cp "$SKILL_DIR/SKILL.md" "$HOME/.codex/skills/deploy-web/SKILL.md"
    echo "   ✅ Codex:       ~/.codex/skills/deploy-web/SKILL.md"
fi

# (C) General Agent Skills directory (~/.local/share/agent-skills)
mkdir -p "$HOME/.local/share/agent-skills/deploy-web"
cp "$SKILL_DIR/SKILL.md" "$HOME/.local/share/agent-skills/deploy-web/SKILL.md"
echo "   ✅ Generic:     ~/.local/share/agent-skills/deploy-web/SKILL.md"

echo ""
echo "🎉 Setup completed successfully!"
echo "All coding agents (Claude Code, Codex, agy, Cursor, etc.) can now use 'mcode-web-deploy'."
