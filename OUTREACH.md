# readmandarin.com 外链/获客物料（2026-09-12）

产出物：
- `dist/anki/readmandarin-hsk{1..6}.apkg` — 6 个 Anki 牌组，1465 词，全部带例句 + 音频 + 回链
- `dist/pins/*.jpg` — 30 张 1000×1500 Pinterest 图卡（`python3 gen_pins.py` 可再生成）
- 本文件 — Show HN / 老师邮件 / Pinterest 文案

---

## 1. AnkiWeb（你来操作）

1. 装 Anki 桌面版 https://apps.ankiweb.net/ ，注册 AnkiWeb 账号
2. 双击 `dist/anki/readmandarin-hsk1.apkg` 导入
3. 牌组右侧齿轮 → Share → 填 tags 和描述 → 上传
4. 六个牌组分开传（六个 AnkiWeb 页面 = 六个入口，标题里的 "HSK 1/2/3…" 正好是搜索词）

上传时的 tags（AnkiWeb 靠这个被搜到）：
`chinese mandarin hsk hsk1 vocabulary graded-reader audio example-sentences`
（每级把 hsk1 换成对应级别）

描述已经写进 apkg 里了，上传时会自动带出来，不用另写。

以后课文更新了，重跑 `python3 export_anki.py` 再上传同名牌组即可 —— 牌组 ID 是固定的，
AnkiWeb 那边算更新不算新建，已下载的人会收到更新。

## 2. 给中文老师 / 学校的邮件（你来发）

目标：社区学院、大学东亚系、K-12 中文老师、CLTA（全美中文教师学会）分会名单里的人。
一次发一个人，改一句跟对方相关的话再发。别群发，别抄送。

主题：
Free HSK-graded Chinese readings for your students (no signup)

正文：
Hi Professor ___,

I saw your Chinese 101 page lists free reading resources, so this might be useful:
my wife teaches Mandarin full-time and we've been building readmandarin.com — 415 short
graded readings sorted by HSK level, each with pinyin, tap-any-word definitions, native
audio and an English toggle. It's free, there's no account, no ads, and nothing to install.

HSK 1 is here if you want to see the level: https://readmandarin.com/hsk1

If it's useful to your students, a link on your resources page would help us a lot. And if
there's a topic your class needs that we don't cover, tell me and I'll write it.

Best,
___

（为什么这么写：说清楚是谁做的、一句话说清是什么、给一个能直接点开的级别页、
明说要什么、给对方一个回信的由头。不吹、不附件、不超过六行。）

## 3. Show HN（发一次，别重发）

标题：
Show HN: Free HSK-graded Chinese readings with audio and tap-to-define

正文：
My wife teaches Mandarin full time and kept hitting the same wall: her students had
textbooks and flashcard apps but nothing to actually read at their level. So we built
readmandarin.com — 415 short readings graded by HSK level, each with pinyin above the
characters, tap-any-word definitions, native audio per sentence and per word, and an
English toggle you can leave off.

It's a zero-dependency static site: a ~1k-line Python build script turns JSON lesson files
into HTML, audio is pre-generated at build time with edge-tts so there's no TTS call at
runtime, and the whole thing is on Cloudflare Pages. No account, no ads, no tracking beyond
CF's aggregate analytics.

The part I'd most like feedback on is the grading. Staying inside an HSK level while still
writing something a person would want to read is much harder than it looks, and the
higher levels drift.

（HN 规则：白天美东时间发，发完别刷票别喊人点赞，评论区有人问就好好答。
被 newsletter/博客转载才是真正的收获，链接本身是 nofollow。）

## 4. Pinterest（你来发）

账号：注册 business 账号（免费），profile 挂 readmandarin.com 并做网站验证
（验证后 pin 会显示站点署名，点击率高一截）。

发布节奏：一天 2–3 张，别一次全传。每张 pin 的 destination link 指向该课文页，
不是首页 —— 图卡文件名就是 slug，例如 `hsk1-buying-fruit.jpg` 对应
https://readmandarin.com/texts/hsk1-buying-fruit

标题模板（Pinterest 搜索吃标题）：
`HSK 1 Chinese Vocabulary: Buying Fruit | 5 words with pinyin + audio`

描述模板：
`Five HSK 1 words you need for buying fruit in Chinese, with pinyin and native audio.
Part of a free graded reading — tap any word for its meaning, no signup.
More HSK 1 readings at readmandarin.com`

看板（board）建六个：HSK 1 Chinese Vocabulary … HSK 6，别混在一个板里。

## 5. 顺手做的

- Quora：答 "How do I practice reading Chinese as a beginner" 这类问题，规则同 Reddit，
  先答透，账号有历史了再提站。
- Chinese-forums.com：注册后签名档可以挂链接（少数真 dofollow 的地方）。
- Facebook：**评论区别贴可点链接**，FB 会压带外链帖子的触达。评论里写站名即可，
  真链接放主页 Links 区。

## 6. 具体投递名单（2026-09-12 搜出来的，按优先级）

### 最高价值：资源库 / 榜单文章（真 dofollow 外链，权重远高于我们）

1. **Hacking Chinese 的资源数据库** — https://challenges.hackingchinese.com/resources
   Olle Linge 维护，是中文学习圈最权威的资源库，本身就接受提交。他还有一篇
   "The 10 best free Chinese reading resources"。**这一条的优先级高于所有其他外链动作。**
2. **nihawa.com "Free Chinese Learning Resources (2026): The Complete List"** —
   新榜单，收录门槛通常最低，先打这个练手
3. **AllLanguageResources "Start Reading Chinese – A Resource Guide"** —
   https://www.alllanguageresources.com/start-reading-chinese-a-resource-guide/
   这类 guide 站靠更新维持排名，欢迎新资源
4. **Culture Yard "12 Best Chinese Reading Resources"**、**DigMandarin
   "Where To Find the Best Chinese Graded Readers"**、**Migaku 的 graded readers 博客** —
   三篇都是"最佳XX列表"，邮件推荐即可，说清楚免费无注册

给榜单作者的邮件，主题写：
`A free HSK-graded reader for your "best Chinese readers" list`
正文比给老师的还要短：你那篇文章我们站可能该在里面，415 篇按 HSK 分级、带朗读和点词释义、
免费无注册、无广告，HSK1 在这里 <链接>。一句话说清差异化（**竞品里没有整站朗读 + 点词**），
不要求回链，让对方自己决定。

### 次高：.edu 资源页（一封一封写，用第 2 节的模板）

- **University of Iowa 语言文化中心** https://clcl.uiowa.edu/mandarin-language-and-culture-resources
  —— 页面里已经明确列了 "HSK reading materials"，匹配度最高，先打这个
- **St. Lawrence University** 世界语言系 Chinese Resources 页
- **University of Northern Iowa** "Best Chinese Websites"
- **Cal State** "Learn Chinese Online Page"
- 之后按 CLTA（全美中文教师学会）会员名单往下扫

### 竞品参照（不是投递对象，是选题情报）

MandarinBean / ChineseGradedReader / Decoding Chinese / Little Fox / WordSwing。
**它们都没有"整站逐句逐词朗读 + 点词释义 + 无注册"这个组合** —— 对外一句话介绍就用这个。
