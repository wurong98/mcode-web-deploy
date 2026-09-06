#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="/usr/local/bin"

if [ ! -w "$TARGET_DIR" ]; then
    echo "Requires root permission to install to $TARGET_DIR. Using sudo..."
    sudo ln -sf "$DIR/bin/mcode-deploy" "$TARGET_DIR/mcode-deploy"
else
    ln -sf "$DIR/bin/mcode-deploy" "$TARGET_DIR/mcode-deploy"
fi

echo "✅ Successfully linked 'mcode-deploy' to $TARGET_DIR/mcode-deploy"
echo "You can now run 'mcode-deploy --help' from any terminal or Agent workspace."
