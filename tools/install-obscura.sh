#!/usr/bin/env bash
# Installs Obscura v0.2.5 (stock no-render build, default settings) into ./bin
set -euo pipefail
VER=v0.2.5
ASSET=obscura-x86_64-linux-no-render.tar.gz
SHA=405b7d1b79a94f89be1dcad03edab3c48858568b5cb03b90d9e7dcbfda449b12
DIR="$(cd "$(dirname "$0")/.." && pwd)/bin"
mkdir -p "$DIR"
curl -sSL -o "$DIR/$ASSET" "https://github.com/h4ckf0r0day/obscura/releases/download/$VER/$ASSET"
echo "$SHA  $DIR/$ASSET" | sha256sum -c
tar xzf "$DIR/$ASSET" -C "$DIR" && rm "$DIR/$ASSET"
"$DIR/obscura" --version
