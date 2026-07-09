# 开通登录 + 云同步(Firebase,免费,约 10 分钟)

代码已就绪。完成以下步骤、把配置贴进 site.json 后,导航栏自动出现 "Sign in"
(Google 一键登录);用户的生词本和打卡记录自动同步云端、换设备不丢。
没配置之前网站完全不变。

## 1. 创建 Firebase 项目
1. 打开 https://console.firebase.google.com → Create project
2. 项目名随意(如 read-chinese-daily),Google Analytics 可以不开

## 2. 注册 Web 应用,拿配置
1. 项目首页 → 点 `</>`(Web)图标 → 起个名 → Register
2. 复制出现的 `firebaseConfig` 对象里的字段,贴进
   `content/site.json` 的 `firebase`:
```json
"firebase": {
  "apiKey": "AIza....",
  "authDomain": "xxx.firebaseapp.com",
  "projectId": "xxx",
  "appId": "1:123:web:abc"
}
```
(这些不是密钥,放前端是官方设计,安全靠第 4 步的规则。)

## 3. 开启 Google 登录
Build → Authentication → Get started → Sign-in method →
Google → Enable → 填一个支持邮箱 → Save

然后 Authentication → Settings → Authorized domains →
Add domain → `lm742611149.github.io`

## 4. 建数据库 + 安全规则
1. Build → Firestore Database → Create database → Production mode → 就近区域
2. Rules 标签页,替换为(只允许每个用户读写自己的文档):
```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{uid} {
      allow read, write: if request.auth != null && request.auth.uid == uid;
    }
  }
}
```
→ Publish

## 5. 重建推送
```bash
cd ~/Documents/mandarin-site && python3 build.py && git add -A && git commit -m "enable auth" && git push
```

## 数据模型(将来 VIP / 奖励在这上面长)
`users/{uid}` 文档: `{ words: [...生词], done: {课文: 完成日期}, plan: "free", updated }`
- 连续打卡/徽章/奖励 = 从 done 的日期集合计算
- VIP = 把 plan 改成 "pro"(Stripe Payment Link 付款后手动/脚本改,后期再上 webhook 自动化),
  前端按 plan 字段解锁内容
