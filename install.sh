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

echo "Installing mcode-web-deploy to $TARGET_DIR..."
install_link "$DIR/bin/mcode-web-deploy" "$TARGET_DIR/mcode-web-deploy"
install_link "$DIR/bin/mcode-web-deploy" "$TARGET_DIR/mcode-deploy"

echo "✅ Successfully installed:"
echo "   - $TARGET_DIR/mcode-web-deploy (primary)"
echo "   - $TARGET_DIR/mcode-deploy (alias)"
echo "You can now run 'mcode-web-deploy --help' from any terminal or Agent workspace."
