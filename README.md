# GZH Article Pipeline

<p align="center">
  <img src="assets/hero-banner.jpg" alt="GZH Article Pipeline Banner" width="100%" style="border-radius: 8px;" />
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square" alt="License: MIT" /></a>
  <a href="https://github.com/openai/codex"><img src="https://img.shields.io/badge/Codex-Skill-green.svg?style=flat-square" alt="Codex Skill" /></a>
  <a href="https://deepmind.google"><img src="https://img.shields.io/badge/Google-Antigravity-orange.svg?style=flat-square" alt="Google Antigravity" /></a>
  <a href="https://mp.weixin.qq.com"><img src="https://img.shields.io/badge/WeChat-Official%20Account%20API-07C160.svg?style=flat-square" alt="WeChat Official Account API" /></a>
  <a href="https://github.com/lukaizj/gzh-article-pipeline/stargazers"><img src="https://img.shields.io/github/stars/lukaizj/gzh-article-pipeline?style=flat-square&logo=github&label=Stars" alt="GitHub Stars" /></a>
  <a href="https://github.com/lukaizj/gzh-article-pipeline"><img src="https://visitor-badge.laobi.icu/badge?page_id=lukaizj.gzh-article-pipeline" alt="Visitors" /></a>
</p>

<p align="center">
  <b>微信公众号全自动生产、质检与数据复盘闭环流水线</b><br>
  <span>选题规划 → 内容驱动封面生图 → 1000字高完读撰写 → 9项自动质检 → 一键推草稿箱 → 后台推荐流复盘校准</span>
</p>

<p align="center">
  <a href="#核心功能亮点-highlights">核心亮点</a> •
  <a href="#视觉与闭环架构-architecture">架构视觉</a> •
  <a href="#快速上手-quick-start">快速上手</a> •
  <a href="#安装与配置-installation">安装配置</a> •
  <a href="#隐私安全与支持-contact">支持与定制</a>
</p>

> [!TIP]
> 💡 **觉得省时好用，欢迎点亮右上角 ⭐️ [Star](https://github.com/lukaizj/gzh-article-pipeline) 支持！这是持续迭代维护的最大动力。**

---

## 核心功能亮点 (Highlights)

告别长篇大论、样式被微信吞掉、发完不知道为什么没流量的传统 AI 写作套路，流水线用**实证后台数据 + 工程化硬卡扣**跑通全流程：

| 核心模块 | 解决什么痛点 | 硬核机制与能力 |
| :--- | :--- | :--- |
| **🎯 实证选品与标题门槛** | 选题全靠拍脑袋，写完没人点进门 | • **5 步存活性死刑复核**：核查源码、最近提交与 Release 包，拒绝推荐已失效僵尸项目<br>• **4 维差异化定位 + 标题 100 分打分**：`<= 26` 字禁绝极客黑话，`< 75 分` 自动打回重写 |
| **✍️ 高完读短节奏与 9 项质检** | 开头废话多、段落像砖头、满篇 AI 腔 | • **1000～1300 字精炼流**：前三句直接给结论，手机端 2～3 行短段、每功能必译为人话收益<br>• **`validate_article.py` 离线质检**：自动扫描黑话、段长、图文密度、词边界违禁词与 `<span leaf="">` 完整性 |
| **🎨 吸睛 `21:9` 封面与 429 容灾** | 灰底素图没人点，API 限流就中断 | • **内容驱动全画幅实景封面**：高饱和撞色 + 单行 7～9 字发光主标题，`--no-safe-crop` 满版直传不切字<br>• **双引擎生图零中断**：API 遇 `429` 配额耗尽，秒级无缝切 Chrome Gemini Web Pro 自动接管 |
| **🚀 零清洗排版与草稿箱直推** | 微信后台吞 CSS、反复改稿版式乱 | • **0 单引号纯内联引擎（橄榄手记）**：兼容图文大表与警示卡，自动植入文末官方公众号名片<br>• **`upload_to_wechat.py` 一键推**：支持直接新建或 `--update-draft` 原地覆盖更新已有草稿 |
| **📊 后台推荐流复盘飞轮** | 不知道文章卡在 CTR 还是完读率 | • **`pull_and_analyze_mp.py` 免密钥直连**：复用 Chrome 后台会话，3 秒拉全篇**完读率 + 推荐流占比 + 粉丝打开率**，自动回写 `account_empirical_profile.json` 指导下一篇选题 |

---

## 视觉与闭环架构 (Architecture)

```text
[模式 A: 自动选题 / 模式 B: 链接直写]
       │
       ▼
[封面与插图生成 (API/Web 双引擎)] ➔ [1000字短段排版 + validate_article 9项质检] ➔ [upload_to_wechat 推草稿箱]
       ▲                                                                                     │
       └────── [经验画像库 account_empirical_profile.json] ◄── [pull_and_analyze_mp 后台全渠道复盘] ◄─┘
```

![核心工作流：双轨驱动架构](assets/workflow-architecture.jpg)

| 实证选品与 100 分标题门禁 | 21:9 封面与 429 自动容灾 |
| :---: | :---: |
| <img src="assets/01-topic-gate.jpg" width="100%" alt="实证选品与100分标题门禁" style="border-radius: 6px;" /> | <img src="assets/02-visual-429.jpg" width="100%" alt="21:9封面与429自动容灾" style="border-radius: 6px;" /> |
| **短节奏排版与 9 项自动质检** | **免密钥直连后台复盘飞轮** |
| <img src="assets/03-quality-validator.jpg" width="100%" alt="短节奏排版与9项自动质检" style="border-radius: 6px;" /> | <img src="assets/04-closed-loop-review.jpg" width="100%" alt="免密钥直连后台复盘飞轮" style="border-radius: 6px;" /> |

---

## 快速上手 (Quick Start)

| 使用场景 | 对 AI 说 / 执行命令 | 说明 |
| :--- | :--- | :--- |
| **不知写什么（自主选题）** | `今天选个题` | 结合后台经验库现挖 3 个高通过率候选 + S/A 级标题 |
| **已有项目/链接（直接出稿）** | `用 gzh-article-pipeline 写这篇：<URL>` | 自动规划配图、生图、写稿、9 项质检并直推草稿箱 |
| **复盘最近文章流量** | `python3 wechat-content-analysis/scripts/pull_and_analyze_mp.py --limit 30` | Chrome 保持登录 `mp.weixin.qq.com` 即可一键出诊断报告 |

<details>
<summary><b>展开查看仓库目录结构</b></summary>

```text
gzh-article-pipeline/
├── gzh-article-pipeline/                      # 主创作与发布流水线 Skill
│   ├── SKILL.md                              # 全流程总控指令
│   ├── scripts/
│   │   ├── upload_to_wechat.py               # 微信草稿箱直推 (--no-safe-crop / --update-draft)
│   │   ├── validate_article.py               # 离线 9 项质量、标题评分与违禁词校验器
│   │   ├── gemini_web_bridge.py              # Chrome Gemini Web 429 自动容灾生图
│   │   ├── generate_image_unified.py         # 生图双引擎统一调度器
│   │   └── pull_and_analyze_mp.py            # 公众号后台全渠道数据拉取
│   └── references/
│       ├── topic_selection.md                # 选品七道生死门与 4 维定位卡扣
│       ├── writing_playbook.md               # 去说明书写法与标题百分制评分卡
│       ├── visual_system.md                  # 21:9 吸睛封面规范与 7 维终检
│       ├── olive_journal_template.py         # 橄榄手记内联 HTML 组件库与名片注入
│       └── account_empirical_profile.example.json
└── wechat-content-analysis/                  # 独立公众号数据复盘专家 Skill
    ├── SKILL.md
    └── scripts/pull_and_analyze_mp.py
```

</details>

---

## 安装与配置 (Installation)

**方式 A（推荐）：** 直接把本仓库发给你的 Codex / Antigravity：
```text
请帮我安装这个 skill：https://github.com/lukaizj/gzh-article-pipeline
```

**方式 B：手动命令行安装**
```bash
git clone https://github.com/lukaizj/gzh-article-pipeline.git /tmp/gzh-pipeline
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R /tmp/gzh-pipeline/gzh-article-pipeline "${CODEX_HOME:-$HOME/.codex}/skills/"
cp -R /tmp/gzh-pipeline/wechat-content-analysis "${CODEX_HOME:-$HOME/.codex}/skills/"
```

**配置微信推送凭据（仅直推草稿箱需要，复盘脚本免配）：**
复制 `gzh-article-pipeline/references/config.example.json` 为 `config.json` 填入 `appid` / `appsecret`（需在公众号后台加本机 IP 白名单），或设置环境变量 `WECHAT_APPID`、`WECHAT_APPSECRET`。

---

## 隐私安全与支持 (Contact)

- **零密钥泄漏保障**：`.gitignore` 默认屏蔽 `config.json` 与凭据缓存；所有排版、质检与后台拉取全部本机完成，无第三方代理。
- **MIT 开源协议**：详见 [LICENSE](LICENSE)，欢迎提 Issue / PR。

| 微信赞赏支持 | 主理人微信（技术交流 / 一键部署定制） |
| :---: | :---: |
| <img src="assets/sponsor.png" width="200" alt="微信赞赏支持" style="border-radius: 8px;" /> | <img src="assets/wechat.png" width="200" alt="主理人微信" style="border-radius: 8px;" /> |
| **觉得好用，请作者喝杯冰美式** | **微信：`lukai391424`（备注 `开源` 或 `部署`）** |
