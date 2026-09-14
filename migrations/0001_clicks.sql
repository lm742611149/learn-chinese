-- 出站点击(Preply / Facebook)。不存 IP、不存 UA、不存 referrer 全文 ——
-- 只存"从哪个页面的哪个位置点去了哪儿",够回答"哪个海报位有效"就行。
CREATE TABLE IF NOT EXISTS clicks (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  ts        TEXT NOT NULL,              -- ISO8601 UTC
  day       TEXT NOT NULL,              -- YYYY-MM-DD,方便按天聚合
  dest      TEXT NOT NULL,              -- preply | facebook
  placement TEXT NOT NULL,              -- poster-home-top / poster-reader-bottom / nav / footer ...
  path      TEXT NOT NULL,              -- 点击发生在哪一页
  level     TEXT,                       -- 课文页的 HSK 等级(1-6),其它页为 NULL
  country   TEXT,                       -- CF 给的国家码,粗粒度
  device    TEXT                        -- m | d
);
CREATE INDEX IF NOT EXISTS idx_clicks_day ON clicks(day);
CREATE INDEX IF NOT EXISTS idx_clicks_placement ON clicks(placement);
