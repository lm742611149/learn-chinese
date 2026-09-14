#!/usr/bin/env bash
# 出站点击(Preply / Facebook)查询 —— 数据在 CF D1 readmandarin-clicks,
# 由 functions/api/click.js 写入。wrangler 要 node 22,这里自己切。
#
#   ./clicks.sh            近 7 天,按位置聚合
#   ./clicks.sh 30         近 30 天
#   ./clicks.sh 7 raw      近 7 天的明细
set -euo pipefail
cd "$(dirname "$0")"
export NVM_DIR="$HOME/.nvm"; . "$NVM_DIR/nvm.sh" >/dev/null 2>&1; nvm use 22 >/dev/null 2>&1

DAYS="${1:-7}"
MODE="${2:-summary}"
SINCE="date('now','-${DAYS} days')"

if [ "$MODE" = "raw" ]; then
  SQL="SELECT ts, dest, placement, path, level, country, device FROM clicks
       WHERE day >= $SINCE ORDER BY id DESC LIMIT 200"
else
  SQL="SELECT placement, dest, COUNT(*) AS clicks,
              SUM(CASE WHEN device='m' THEN 1 ELSE 0 END) AS mobile
       FROM clicks WHERE day >= $SINCE
       GROUP BY placement, dest ORDER BY clicks DESC"
fi

npx --yes wrangler@latest d1 execute CLICKS --remote --json --command "$SQL" \
  | python3 -c '
import json,sys
rows = json.load(sys.stdin)[0]["results"]
if not rows:
    print("近期没有点击记录"); raise SystemExit
cols = list(rows[0].keys())
w = [max(len(c), *(len(str(r[c])) for r in rows)) for c in cols]
print("  ".join(c.ljust(w[i]) for i,c in enumerate(cols)))
print("  ".join("-"*x for x in w))
for r in rows:
    print("  ".join(str(r[c]).ljust(w[i]) for i,c in enumerate(cols)))
'
