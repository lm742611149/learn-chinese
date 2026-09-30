#!/usr/bin/env bash
# 查 CF 外部来源(ChatGPT/Bing/Perplexity…)。wrangler 的 OAuth token 要 node22 刷新。
set -euo pipefail
cd "$(dirname "$0")"
export NVM_DIR="$HOME/.nvm"; . "$NVM_DIR/nvm.sh" >/dev/null 2>&1; nvm use 22 >/dev/null 2>&1
npx --yes wrangler@latest whoami >/dev/null 2>&1 || true
TOKEN=$(grep '^oauth_token' ~/Library/Preferences/.wrangler/config/default.toml | cut -d'"' -f2)
python3 cf_referrers.py "$TOKEN"
