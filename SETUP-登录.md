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

## 3. 开启登录方式(代码已支持 Google + Facebook + 邮箱三种)
Build → Authentication → Get started → Sign-in method:

**a) Google**: Enable → 填支持邮箱 → Save(最简单,先开这个)

**b) Email/Password**: Enable → Save(邮箱密码注册,顺手开)

**c) Facebook**(对你的粉丝最重要,但要多几步):
1. 去 https://developers.facebook.com → My Apps → Create App →
   类型选 "Authenticate and request data from users with Facebook Login"
2. App 里添加产品 **Facebook Login** → 设置里 Valid OAuth Redirect URIs 填:
   `https://<你的projectId>.firebaseapp.com/__/auth/handler`
   (确切地址在 Firebase 的 Facebook 开关页会显示,复制即可)
3. 拿 App ID 和 App Secret,回 Firebase → Sign-in method → Facebook →
   Enable → 贴入 → Save
4. Meta App 切到 **Live 模式**(基础的 public_profile/email 权限不需要审核;
   若提示需要商家验证,按指引用你的 FB 主页完成)

最后 Authentication → Settings → Authorized domains →
Add domain → `lm742611149.github.io`

> 用不上某个方式?在 `site.json` 的 `auth_providers` 里删掉对应项,
> 弹窗里就不显示那个按钮。将来加 Apple/X/GitHub 同理(Apple 需要
> $99/年开发者账号,建议以后有 iOS 需求再说)。
> 注意:同一邮箱在不同方式间不互通 —— 用户用 Google 注册过,再用
> 同邮箱的 Facebook 登录会收到"请用原方式登录"的提示(代码已处理)。

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
