# 内容路线图 — 每级 50 篇,共 300 篇

目标: 每个 HSK 级别 50 篇原创短文,系统性覆盖该级词表的大部分词汇和句型。
生产方式: 每次让 Claude 按本清单批量写 3-5 篇(指定级别+主题),校对后 build+push。
注意: ✅ 标记只覆盖标题与本清单完全一致的篇目,实际已写 315 篇(不少标题在写作时改过措辞)。
     **选题前务必先列出 content/texts/*.json 的 title_zh 逐一比对,避免撞题。**
原则: 只用本级及以下词汇(允许 ≤10% 超纲词,超纲词必须进生词表);每篇 5-8 句;
     话题贴近成年学习者的真实生活;可与 Facebook Reels 主题联动。

---

## ⭐️ 选题规则:标题必须是"有人会搜的词"(2026-09-05 定)

**背景**: GSC 数据显示课文页已经能排到第 3-10 名(第一页),但每篇只有 1-2 次展示 ——
页面模板 Google 认可,废掉的是选题。没有人会搜"买水果""什么是幸福"。排在第一页的竞品
(chinesegradedreader.com)把课文直接命名成 `Thank You`/`Hello`/`Excuse Me`,标题本身
就是搜索词。

**新选题的两个硬条件(必须同时满足)**:
1. 英文标题写成 `<场景/表达> in Chinese` 后,是一个英语母语学习者真会在 Google 里打的短语
   —— 比如 `how to say thank you in chinese` / `ordering food in chinese` /
   `chinese numbers 1 to 10`
2. 课文内容真能兑现这个标题(不是标题党),且能用**本级及以下**词汇写出来

**反面例子(别再选)**: 记叙散文式的题目 —— 苹果和米饭 / 小狗和小猫 / 快乐的一天 /
我的杯子。这类写出来很好读,但搜索量为零,315 篇里的大多数展示为 0 就是这个原因。

**优先级**: HSK1-2 最重要(入门搜索词的量级最大,且竞品在这一层最弱)。
HSK4-6 保持现在的话题路线(碳中和/认知偏差这类),那是与竞品的差异化,不要求搜索词化。

**命名约定**: 中文标题照旧自然拟;`title_en` 直接写成搜索短语。疑问句用 `Asking…` 开头
(`Asking the Time in Chinese`),不要硬加后缀写成 `What Time Is It? in Chinese`。

### 待写的搜索型选题(已做过撞题检查,2026-09-05)

⚠️ **先看这条**: 2026-09-05 已把 58 篇 HSK1-3 课文的 `title_en` 改成搜索短语,
**这批搜索词已经被占了,别再重复写**。已覆盖的包括: Ordering Food / Buying Coffee /
Getting a Haircut / Asking for Directions / At the Hotel / Taking a Taxi /
Talking About the Weather / Asking the Time / Asking Someone's Name /
Registering at a Hospital / Opening a Bank Account / Sending a Package /
The Job Interview / Exchanging Money 等(完整清单见 git log 69fe6bf)。
**拟新选题前,先跑一遍 title_zh 和 title_en 的双向撞题比对。**

**HSK 1** — 入门功能词,搜索量最大也最空白的一层。**这 9 篇已于 2026-09-05 开写**
谢谢/不客气 → Saying Thank You in Chinese ⭐️(竞品 CGR 就是靠这类词排上第一页) /
对不起 → Saying Sorry in Chinese ⭐️ / 你好·问候 → Greetings in Chinese ⭐️ /
多少钱 → Asking How Much It Costs in Chinese ⭐️ /
我听不懂 → Saying You Don't Understand in Chinese(「懂」超纲,进 vocab) /
认识你很高兴 → Nice to Meet You in Chinese ⭐️ /
月份和日期 → Months and Dates in Chinese /
我爱你 → How to Say I Love You in Chinese ⭐️ / 是和不是 → Saying Yes and No in Chinese

⚠️ **拟 HSK1 选题前先查 150 词表** —— 2026-09-05 有两条候选是查了词表才发现写不了的:
- **颜色 → Colors in Chinese:已砍。HSK1 词表里一个颜色词都没有**(红/蓝/白/黑全不在),
  整篇会 100% 超纲。要写得等 HSK3 以上
- **家人称呼 → Family Members in Chinese:已砍**。HSK1 亲属词只有爸爸/妈妈/儿子/女儿四个,
  内容单薄,而且与已有「我的家 → Talking About My Family in Chinese」撞搜索词
- 同理注意:「懂」「知道」「明白」「生日」都不在 150 词表里

### 📌 选题来源:扒竞品的课文列表(2026-09-05 加)

排在第一页的竞品,它们的课文标题就是**被验证过的选题** —— 既有搜索量、又能写成分级读物。
抓法: `curl https://chinesegradedreader.com/post-sitemap.xml`,URL 的 slug 就是标题
(hskreading.com 的 sitemap 不带级别,要从 /category/hsk-N/ 页面取)。

⚠️ **但不能照单全收**:CGR 90 篇里有一大半也没搜索量(`14 times` / `the egg` /
`really really` / `good good` / `just one`)。**要用搜索价值再筛一遍**。

**筛出来的规律(重要)**:真正有搜索量的那类不是场景文,是**日常口语短句** ——
`too expensive` / `no problem` / `help me` / `wait a moment` / `hurry up` /
`be careful` / `what do you mean` / `i dont understand`。这类词搜索量比
「买车票」「在超市」这种场景选题高得多,而且低级词汇就写得出来。

**HSK 2** — 口语短句优先(2026-09-05 首批 7 篇已开写)
我不知道 → I Don't Know in Chinese ⭐️ / 没问题 → No Problem in Chinese ⭐️ /
请帮帮我 → Help Me in Chinese ⭐️ / 等一下 → Wait a Moment in Chinese ⭐️ /
太贵了 → Too Expensive in Chinese ⭐️(砍价,与已有「便宜还是贵」的比价区分) /
请说慢一点 → Please Speak Slowly in Chinese ⭐️ /
你是什么意思 → What Do You Mean in Chinese
第二批(2026-09-06 开写): 我想你 → I Miss You in Chinese ⭐️ / 走吧 → Let's Go in Chinese ⭐️ /
你在做什么 → What Are You Doing in Chinese ⭐️ / 真好吃 → Delicious in Chinese /
一个还是两个 → Chinese Measure Words / 买火车票 → Buying a Train Ticket in Chinese

**HSK 3** — (2026-09-05 首批 3 篇已开写)
小心 → Be Careful in Chinese / 快一点 → Hurry Up in Chinese(与「迟到了」区分:催促 vs 结果) /
买手机卡 → Getting a SIM Card in Chinese ⭐️(在华外国人真实痛点,竞争极低)
第二批(2026-09-06 开写): 怎么办 → What Should I Do in Chinese ⭐️ /
别担心 → Don't Worry in Chinese ⭐️ / 好久不见 → Long Time No See in Chinese ⭐️(这句是中文直译进
英文的,学习者爱搜) / 在药店 → At the Pharmacy in Chinese / 点外卖 → Ordering Delivery in Chinese

第三批(2026-09-06 开写,旅游/日常必备,搜索量最高的一层):
洗手间在哪儿 → Where Is the Bathroom in Chinese ⭐️⭐️(外国人在华最常用的一句) /
你会说英语吗 → Do You Speak English in Chinese ⭐️⭐️ / 晚安 → Good Night in Chinese ⭐️⭐️ /
加油 → Come On in Chinese ⭐️(字面"加燃料",学习者爱查) / 我饿了 → I'm Hungry in Chinese /
干杯 → Cheers in Chinese / 我要这个 → I Want This in Chinese / 真的吗 → Really in Chinese /
请进 → Come In in Chinese / 什么时候 → When in Chinese / 当然 → Of Course in Chinese /
我同意 → I Agree in Chinese

**分级注意**: 「洗手间」不在 HSK2 词表(HSK3 才有),这篇要放 HSK3。
**已否决**: 为什么 → Why in Chinese —— 与已有「为什么学中文」标题字面撞,且搜索意图模糊

### 🎯 冲 100 篇搜索型课文的完整清单(2026-09-06 定,已过撞题+词池双检查)

目标: 搜索型课文凑满 100 篇。已完成 42,下面 58 个候选**全部检查过**,
分四轮写。✅ 已写 / 🔨 进行中 / 空白 = 待写。

**轮 1(15 篇,🔨 进行中)**
🔨你好吗 How Are You(1) / 🔨请问 Excuse Me(1) / 🔨早上好 Good Morning(2) /
🔨不客气 You Are Welcome(2) / 🔨没关系 It Is OK(2) / 🔨欢迎 Welcome(2) /
🔨怎么说 How Do You Say It(2) / 🔨太好了 That Is Great(2) / 🔨我累了 I Am Tired(2) /
🔨怎么走 How Do I Get There(2) / 🔨多远 How Far Is It(2) / 🔨我到了 I Have Arrived(2) /
🔨生日快乐 Happy Birthday(3) / 🔨恭喜 Congratulations(3) / 🔨我饱了 I Am Full(3)

**轮 2(15 篇)** — 吃饭购物
好吃吗 Is It Good(2) / 再来一个 One More(2) / 菜单 The Menu(2) / 有没有 Do You Have It(2) /
我不吃辣 I Do Not Eat Spicy Food(3) / 打包 Takeout(3) / 我请客 My Treat(3) /
我试一下 Can I Try It On(3) / 我只看看 Just Looking(3) / 刷卡 Paying by Card(3) /
回头见 See You Later(2) / 保重 Take Care(3) / 麻烦你了 Sorry to Trouble You(3) /
你说什么 What Did You Say(2) / 我不会 I Cannot Do It(2)

**轮 3(15 篇)** — 感受 + 沟通
我很开心 I Am Happy(2) / 我难过 I Am Sad(3) / 没意思 Boring(3) / 我怕 I Am Scared(2) /
没事 It Is Nothing(2) / 还可以 Not Bad(2) / 有点儿 A Little Bit(2) / 我看看 Let Me See(2) /
随便 Whatever You Like(3) / 差不多 About the Same(3) / 算了 Forget It(3) /
不一定 Not Necessarily(3) / 你先 After You(3) / 这个字怎么读 How Do You Read This(3) /
要多长时间 How Long Does It Take(3)

**轮 4(13 篇)** — 生活场景
我回来了 I Am Home(2) / 我忘了 I Forgot(2) / 我要走了 I Have to Go(2) /
我马上到 I Will Be There Soon(2) / 快递到了 My Package Arrived(3) / 我迟到了 I Am Late(3) /
我丢了 I Lost It(3) / 借我用一下 Can I Borrow It(3) / 我搬家了 I Moved(3) /
停一下 Stop Here(3) / 加个微信 Add Me on WeChat(3) / 你结婚了吗 Are You Married(3) /
你的电话号码 Your Phone Number(3)

**检查时否掉的**:
- 你是哪国人 Where Are You From —— 已被 hsk2-nice-to-meet-you 覆盖
- 你的电话号码 原定 HSK2 → **改 HSK3**(「号码」只在 HSK3 池里)

**每篇都要提醒 agent 与已有课文区分**,清单里已标注的例如:
怎么走 vs 已有的「问路」/ 不客气 vs 已有的「谢谢你」/ 没关系 vs 已有的「对不起」/
生日快乐 vs 已有的三篇生日课文 / 我饱了 vs 已有的「我饿了」

**又砍掉两条(词表不够,同「颜色」)**:
- **身体部位 → Body Parts in Chinese**: HSK2 只有「眼睛」一个部位词,头/手/脚全不在。等 HSK4
- **生日快乐 → Happy Birthday in Chinese**: 站上已有「过生日」「难忘的生日」「妈妈的生日」
  三篇生日课文,第四篇必然内容重合。用「我不知道」替换

### ✅ 新课文三道检查(缺一不可,2026-09-06 定)

```
python3 validate_texts.py <slug片段...>   # schema:句数/标点/拼音/quiz/grammar 结构
python3 check_vocab.py    <slug...>       # 超纲:池外词 >2 或没进 vocab 就报错
python3 review_batch.py   <slug...>       # 人读才发现的那几类(见下)
```

⚠️ **前两道全过 ≠ 能发**。前两批的实际经验:schema 和词汇都干净,但内容仍有
套话收尾、整题中文 quiz、代词无着落、逻辑打架、格式多行展开等问题。
`review_batch.py` 就是把这些**踩过的坑**固化成检查项:套话收尾 / 结尾跨篇雷同 /
quiz 整题中文 / quiz 答案扎堆 / 疑似超纲高级词点名 / t 数组多行 / 句内副词重复。

**三道全绿之后仍要人眼通读一遍**(语义和自然度机器查不出) —— 例如
「等一下,蛋糕做好了」这种前后打架、「妈妈说:女儿,我爱你」这种不像中文的称呼。

### 🔧 写课文时的词汇约束办法(2026-09-05 定)
HSK2/3 的官方词表(300/600 词)不要凭记忆列 —— 容易错。改用**站内已验证词池**:
从现有同级及以下课文里提取所有用过的词(HSK2 池 636 词 / HSK3 池 1124 词),
给子agent 当安全词表,池外词每篇最多 2 个且必须进 vocab。
配套自检脚本 `check_oov.py` + 词池 json 在 scratchpad(要长期用的话该挪进仓库)。
注意:池子只能证明"用过的一定安全",不能证明"没用过的就超纲" —— 池外词要人工核对词表。

**已从候选里剔除的(撞现有课文,别再拟)**: 数字 1-10(撞「数字真有趣」)/ 星期几(撞「星期天」)/
再见的说法(撞「再见,老师」)/ 看医生(撞「我不舒服」「生病了」「医院挂号」三篇)/
点咖啡(撞「买咖啡」)/ 天气的说法(撞「今天的天气」「天气预报」)/ 在理发店(撞「理发」)/
快递取件(撞「寄快递」)/ 租房看房(撞 HSK4「租房记」)/ 道歉与原谅(与 HSK1「对不起」重复)/
打招呼寒暄(与 HSK1「你好·问候」重复)

---

## HSK 1(50 篇)— 每篇 4-6 句,150 词表词
自我介绍 ✅ / 我的家 ✅ / 我的一天 ✅ / 在饭馆 ✅ / 我的老师 ✅ / 我的学校 ✅ / 买东西 ✅ /
今天的天气 ✅ / 我的狗 ✅ / 我的猫 ✅ / 喝茶还是咖啡 ✅ / 我会说汉语 ✅ / 打电话 ✅ / 看电影 ✅ /
我的朋友 ✅ / 几点了 ✅ / 昨天今天明天 ✅ / 我的房间 ✅ / 坐出租车 ✅ / 去商店 ✅ / 星期天 ✅ /
妈妈做的菜 ✅ / 我不舒服(看医生) ✅ / 在飞机上 ✅ / 我的中国名字 ✅ / 数字真有趣 ✅ /
这是什么 ✅ / 他是谁 ✅ / 我住在哪儿 ✅ / 下雨了 ✅ / 太热了 ✅ / 我爱睡觉 ✅ / 读书 ✅ / 写汉字 ✅ /
我的杯子 ✅ / 三口人吃饭 ✅ / 买水果 ✅ / 苹果和米饭 ✅ / 开车去北京 ✅ / 火车站 / 在学校学习 ✅ /
小狗和小猫 ✅ / 妈妈的生日 ✅ / 爸爸工作 ✅ / 我的钱 ✅ / 大商店小商店 ✅ / 请坐请喝茶 ✅ /
再见,老师 ✅ / 你叫什么名字 ✅ / 中国很大 ✅ / 我的电脑 ✅（批次10 新拟） / 漂亮的衣服 ✅（批次10 新拟） / 回家 ✅（批次10 新拟） / 今年多大 ✅（批次10 新拟）

## HSK 2(50 篇)— 每篇 5-7 句,+150 词
买咖啡 ✅ / 周末去公园 ✅ / 我爱运动 ✅ / 生病了 ✅ / 问路 ✅ / 坐公共汽车 ✅ / 去机场 ✅ /
第一次吃火锅 ✅ / 唱歌跳舞 ✅ / 踢足球 ✅ / 早上跑步 ✅ / 天气预报 ✅ / 穿什么衣服 ✅ / 红色的裙子 ✅ /
去朋友家做客 ✅ / 准备考试 ✅ / 图书馆 ✅ / 买手机 ✅ / 手表和时间 ✅ / 旅游计划 ✅ / 在酒店 ✅ /
点菜 ✅ / 羊肉还是鱼 ✅ / 服务员,买单 ✅ / 便宜还是贵 ✅ / 送礼物 ✅ / 过生日 ✅ / 新年快乐 ✅ /
帮助别人 ✅ / 迟到了 ✅ / 等公共汽车 ✅ / 雪天 ✅ / 游泳 ✅ / 教室里 ✅ / 同学 / 妻子和丈夫 ✅ /
孩子上学 ✅ / 卖西瓜的人 ✅ / 累了休息 ✅ / 别玩手机了 ✅ / 一起做饭 ✅ / 洗衣服 ✅ / 打扫房间 ✅ /
看报纸 ✅ / 喝牛奶吃鸡蛋 ✅ / 左边右边 ✅ / 离家很近 ✅ / 已经十点了 ✅ / 为什么学中文 ✅ / 快乐的一天 ✅

## HSK 3(50 篇)— 每篇 6-8 句,+300 词
我的中国朋友 ✅ / 搬家 ✅ / 面试 ✅ / 第一天上班 ✅ / 减肥 ✅ / 刷牙洗脸(习惯) ✅ / 邻居 ✅ /
借书 ✅ / 还钱 ✅ / 银行开户 ✅ / 换钱 ✅ / 发烧感冒 ✅ / 医院挂号 ✅ / 锻炼身体 ✅ / 爬山 ✅ / 骑自行车 ✅ /
地铁真方便 ✅ / 堵车 ✅ / 迷路 ✅ / 护照丢了 ✅ / 打算去旅行 ✅ / 北京的四季 ✅ / 南方和北方 ✅ /
中秋节的月亮 ✅ / 春节回家 ✅ / 送月饼 ✅ / 学做中国菜 ✅ / 筷子的故事 ✅ / 茶文化 ✅ / 请客吃饭 ✅ /
结婚 / 照顾生病的朋友 ✅ / 担心考试 ✅ / 成绩出来了 ✅ / 选择工作 ✅ / 加班 ✅ / 会议 ✅ / 出差 ✅ /
网上聊天 ✅ / 电子邮件 ✅ / 世界地图 / 动物园 ✅ / 熊猫 ✅ / 环境和树 ✅ / 节约用水 ✅ / 街道很干净 /
安静的图书馆 / 着急的一天 ✅ / 有趣的比赛 ✅ / 难忘的生日 ✅

## HSK 4(50 篇)— 每篇 6-9 句,+600 词
手机和生活 ✅ / 压力与放松 ✅ / 咖啡文化 ✅ / 外卖时代 ✅ / 共享单车 ✅ / 移民与故乡 ✅ /
面试技巧 ✅ / 职业选择 ✅ / 租房记 ✅ / 养宠物的责任 ✅ / 网络交友 ✅ / 遥远的朋友 ✅ / 独自旅行 ✅ /
迷人的丽江 ✅ / 长城游记 ✅ / 火锅与朋友 ✅ / 地方口音 ✅ / 普通话与方言 ✅ / 汉字的美 ✅ /
成语故事:画蛇添足 ✅ / 塞翁失马 / 熟能生巧 ✅ / 广告的秘密 ✅ / 排队文化 ✅ / 面子 ✅ /
送礼的学问 ✅ / 中国的高铁 ✅ / 二维码生活 ✅ / 无现金社会 ✅ / 健身房 ✅ / 熬夜的代价 ✅ /
垃圾分类 ✅ / 雾霾与蓝天 ✅ / 快递小哥 ✅ / 直播购物 / 奶茶经济 ✅ / 相亲 ✅ / 婚礼见闻 /
广场舞 ✅ / 春运 ✅ / 十二生肖 ✅ / 属相与性格 / 茶还是咖啡 / 中医初体验 ✅ / 太极拳 ✅ /
功夫电影 ✅ / 流行音乐 ✅ / 追剧 ✅ / 假期计划 ✅ / 时间管理 ✅ / 网约车司机 ✅（批次10 新拟） / 学车记 ✅（批次10 新拟） / 二手市场 ✅（批次10 新拟）

## HSK 5(50 篇)— 每篇 7-10 句,+1300 词
网上购物 ✅ / 人工智能与工作 ✅ / 远程办公 ✅ / 内卷与躺平 ✅ / 消费主义 ✅ / 极简生活 ✅ /
碳中和 ✅ / 新能源汽车 ✅ / 城市化 ✅ / 老龄化社会 ✅ / 独生子女一代 ✅ / 教育竞争 ✅ / 学区房 ✅ /
留学的得与失 ✅ / 文化冲击 ✅ / 跨国婚姻 ✅ / 家乡的变化 ✅ / 传统手艺的消失 ✅ / 非物质文化遗产 ✅ /
故宫的故事 ✅ / 丝绸之路 ✅ / 郑和下西洋 ✅ / 四大发明 ✅ / 唐诗之美 ✅ / 李白与月亮 ✅ / 书法 ✅ /
京剧脸谱 ✅ / 美食纪录片 ✅ / 一碗兰州拉面 ✅ / 川菜的哲学 ✅ / 微信改变生活 ✅ / 短视频时代 ✅ /
信息茧房 ✅ / 网络暴力 ✅ / 隐私与便利 ✅ / 睡眠经济 ✅ / 宠物经济 ✅ / 单身经济 / 副业刚需 ✅ /
第一次创业 ✅ / 失败的价值 ✅ / 幸福是什么 ✅ / 金钱与快乐 ✅ / 友情的保质期 ✅ / 代沟 ✅ /
妈妈的手机课 ✅ / 志愿者经历 / 无偿献血 ✅ / 马拉松热 ✅ / 冬奥会记忆

## HSK 6(50 篇)— 每篇 7-10 句,+2500 词
坚持的力量 ✅ / 大器晚成 ✅ / 塞翁失马新解 ✅ / 愚公移山与现代人 ✅ / 中庸之道 ✅ /
知足常乐 ✅ / 大道至简 ✅ / 匠人精神 ✅ / 快与慢的辩证 ✅ / 碎片化阅读之弊 ✅ / 深度工作 ✅ /
延迟满足 ✅ / 认知偏差 ✅ / 幸存者偏差 ✅ / 内驱力 ✅ / 习惯的复利 ✅ / 语言与思维 ✅ /
翻译的艺术 ✅ / 汉语的模糊之美 ✅ / 委婉语 ✅ / 谦虚的文化根源 ✅ / 集体与个人 ✅ /
儒家与现代职场 ✅ / 道法自然 ✅ / 禅与生活 ✅ / 科技伦理 ✅ / 基因编辑之争 ✅ / 太空探索 ✅ /
量子计算浅谈 ✅ / 数字货币 ✅ / 全球化的退潮 ✅ / 一带一路 / 大城市病 ✅ / 乡村振兴 /
共同富裕 / 灰色收入 / 舆论监督 / 媒介素养 ✅ / 历史的温度 ✅ / 敦煌的守护者 ✅ /
考古新发现 ✅ / 博物馆热 ✅ / 国潮兴起 ✅ / 汉服运动 / 网络文学出海 ✅ / 科幻的黄金时代 ✅ /
《三体》现象 ✅ / 气候变化与责任 ✅ / 生物多样性 ✅ / 人类的未来 ✅ / 仪式感的意义 ✅（批次10 新拟） / 怀旧为何流行 ✅（批次10 新拟）
