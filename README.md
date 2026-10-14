# 🚀 GZH Article Pipeline (微信公众号全自动推文生产与发布流水线)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Codex Skill](https://img.shields.io/badge/Codex-Skill-green.svg)](https://github.com/openai/codex)
[![Antigravity](https://img.shields.io/badge/Google-Antigravity-orange.svg)](https://deepmind.google)
[![WeChat Official Account](https://img.shields.io/badge/WeChat-Official%20Account%20API-07C160.svg)](https://mp.weixin.qq.com)
[![Visitors](https://visitor-badge.laobi.icu/badge?page_id=lukaizj.gzh-article-pipeline)](https://github.com/lukaizj/gzh-article-pipeline)

> **从零自主策划高转化爆款选题，或直接输入文章链接/技术文档，一键转化为带火柴人插图、深度去 AI 味、排版精致并直推微信公众号草稿箱的爆款推文。**

---

## 💡 为什么需要这个 Skill？

传统的 AI 写公众号推文往往存在以下痛点：
1. **不会选题与选品**：不知道读者想看什么，净写纯底层协议或小众技术，完读率与转发率惨淡；
2. **AI 味浓厚**：充斥着“不仅……而且……”、“在这个数字化转型的时代”、“至关重要”等假大空废话，缺乏真实一线工程质感；
3. **配图与内容割裂**：使用泛化的 AI 绘画或生硬的架构图，读者看不懂也记不住；
4. **排版繁琐脆弱**：排版工具格式混乱，复制粘贴进公众号经常丢失边框、代码高亮和样式；
5. **人工搬运繁重**：每次都要手动下载图片、上传公众号后台、一张张替换、排版、存草稿。

**`gzh-article-pipeline` 将 3 个专业 Skill 与微信官方 API 打通，提供从「爆款选题策划」到「草稿箱直推」的工业级全自动闭环。**

---

## 🏗️ 核心工作流：双轨驱动架构 (Dual-Engine Architecture)

```text
                   ┌──────────────────────────────────────────────┐
                   │ 模式 A：自主选题引擎 (用户零输入 / 寻找灵感)    │
                   │ 触发词：“今天写什么”、“按爆款准则给我几个选题” │
                   └──────────────────────┬───────────────────────┘
                                          │
                                          ▼
                          [阶段 0: 智能爆款选品与流量规划]
                          ├─ 选品四象限（全民高频痛点 × 降维免费 × 0门槛）
                          ├─ 社交货币审查（明确读者群聊转发动机）
                          └─ 输出 3 套黄金标题与方案 ➔ 用户选定
                                          │
                                          ▼
┌─────────────────────────────────────────┴────────────────────────────────────────┐
│ 模式 B：指定输入直写 (文章链接 / GitHub 仓库 / Markdown / 演讲稿)                  │
└─────────────────────────────────────────┬────────────────────────────────────────┘
                                          │
                                          ▼
                          [阶段 1: 视觉锚点规划 (Shot List)]
                          ├─ 提炼核心认知转折点与攻防反差
                          ├─ 输出 16:9 (2.35:1 居中视窗) 插图规划表
                          └─ ⏸️ 强制停顿，等待用户确认
                                          │
                                          ▼ (用户确认后)
                          [阶段 2: 深度去 AI 味撰写 (Humanizer)]
                          ├─ 拒绝机械套话，还原有体温的受害现场
                          └─ 生活化比喻拆解底层原理 + 坦白 20% 边界
                                          │
                                          ▼
                          [阶段 3: 视觉生成与内刊排版 (Olive Journal)]
                          ├─ 🎨 生图双引擎: L1 API 极速生图 ➔ 遇 429 自动无缝切换至
                          │   L2 浏览器原生桥接 (gemini_web_bridge.py 免 API 配额)
                          ├─ 五层叙事剧场版封面 (2.35:1 防切字算法)
                          ├─ 组装「橄榄手记」纯内联 HTML (0 单引号防清洗)
                          └─ 100% 格式合规校验 (<span leaf=""> 0 Warning)
                                          │
                                          ▼
                          [阶段 4: 一键直推草稿箱 (WeChat API)]
                          ├─ 自动上传封面至永久素材库 (thumb_media_id)
                          ├─ 自动上传正文插图至微信 CDN (uploadimg)
                          └─ 提交 draft/add 并返回草稿箱 Draft Media ID
```

---

## 🎨 视觉风格展示：火柴人动作隐喻

本流水线采用统一的 `16:9` 极简黑线 + 科技蓝/终端绿点缀色手绘火柴人风格：

| 图 1：不做重复轮子，做专业编排 | 图 2：科学排障四步法 |
| :---: | :---: |
| ![调度指挥家](assets/01-agent-orchestration.jpg) | ![四步时序](assets/02-four-step-diagnosis.jpg) |
| **图 3：告别盲猜，用证据链说话** | **图 4：面向大数据的智能控制层** |
| ![证据链拼图](assets/03-evidence-chain.jpg) | ![六层控制塔](assets/04-six-layer-architecture.jpg) |

---

## 🌟 核心工程特性 (Core Engineering Highlights)

1. **实战大数据选品与千次转发裂变引擎 (Data-Driven Viral Topic Engine - 模式 A)**：
   - **127 篇 6.2 万真实阅读大数据背书**：内置四大高能母题白名单——资源白嫖/免限速下载（均阅 5k+ 👑）、安全反诈/查底细（均阅 10k+ 🚀）、降维搞钱自动化（均阅 2k+ 🎯）、平替商业流氓软件（均阅 1k+ 🛠️）；
   - **底层技术一票否决门禁**：对纯底层代码/架构库、B2B 企业运维、缺乏反抗情绪的温和工具一票否决，彻底消除 56.7% 死于 100 阅以下的自嗨题材；
   - **标题 NLP 暴击词与 26 字符铁律**：标题严格限制在 `<= 26 字符`（彻底消灭手机列表折叠与信息截断），强制使用“被...恶心吐了/流氓/坑爹”（均阅 2051.2）、“一键/秒级/1秒”（均阅 2934.9）、“GitHub万星”等高转化词库；
   - **单屏截图物证大表与现成群聊安利词**：排版紧凑的《四维代际对比大表》手机一屏即可完整截屏，配合文末预埋的 30~50 字现成安利词，消灭读者转发阻力，冲刺 1,000 次群聊裂变阈值；
   - **黄金发文时段门禁调度器 (Timing Gate)**：脚本内置自动化时段调度建议，首选 07:00~07:20 晨间战神档（均阅 2250.9，享 16 小时发酵），警示 09:30~11:30 早会死亡重灾区。

2. **五层叙事剧场版封面工作流 (5-Tier Editorial Architecture)**：
   - 告别单调大黄底与营销号式排版，采用科技杂志特刊级视觉规范（场景标签 + 醒目大标 + 具象副标 + 权威黑金徽章 + 利益药丸）；
   - **2.35:1 居中安全视窗防切字算法**：自动识别图像边缘并执行居中安全缩放与纯色背景扩展，确保手机订阅号消息流大图 100% 完整露字不切头。

3. **微信富文本 CSS 清洗防御机制 (Zero-CSS-Loss Engine)**：
   - 纯内联样式架构，彻底杜绝单引号导致的微信服务端转义清空 `style=""` 恶性 Bug；
   - 移动端 100% 自适应，保障暗夜状态卡、双色细线对照表与蓝边引言全端渲染完美。

4. **零门槛自然语言操控体系**：
   - 无需编写任何代码或操作繁琐软件，附带 [《日常使用大白话指令卡》](CLIENT_PROMPT_CARD.md)，只需在 AI 对话框中发送自然语言指令，即可自动完成高颜值排版、原生作图并秒级送达微信公众平台草稿箱。

5. **生图双引擎与 429 智能容灾逃逸架构 (Dual-Engine Image Fallback & 429 Bypass)**：
   - **痛点反差**：市面上的 AI 写作 Agent 一旦遭遇生图 API 额度耗尽或高频请求限制（`ResourceExhausted: 429 Too Many Requests`），通常直接抛出异常中断流水线，或者被迫降级使用 Python PIL 绘制简陋死板的灰框，导致推文视觉体验毁灭性崩塌；
   - **核心工程实现**：
     - **L1 API 高速通道**：优先调用系统原生 Native Tool 毫秒级极速渲染高精中文手绘插图；
     - **L2 浏览器原生桥接通道 (`gemini_web_bridge.py`)**：当捕获到 429 配额拦截时，智能体**拒绝中断与违规降级**，全自动无缝唤醒本地 macOS 原生 AppleScript 桥接引擎，操控已在 Chrome 中保持登录的 Google Gemini (Advanced / Pro) 网页端会话，自动注入中英文混合 Prompt、等待 Canvas 渲染并提取无损高精原图；
   - **终极收益**：**0 中断、0 额度焦虑、0 视觉质量降级**，彻底复用个人浏览器订阅权益，保障批量工业化出文 100% 稳定交付。

## 📦 安装与配置

### 1. 安装 Skill

#### 方式 A：直接让 Codex / Antigravity 安装
将本项目 GitHub 链接发送给你的 AI Assistant：
```text
请帮我安装这个 skill：
https://github.com/lukaizj/gzh-article-pipeline
```

#### 方式 B：本地源码安装
```bash
# 克隆仓库
git clone https://github.com/lukaizj/gzh-article-pipeline.git /tmp/gzh-pipeline

# 安装到 Codex
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R /tmp/gzh-pipeline/gzh-article-pipeline "${CODEX_HOME:-$HOME/.codex}/skills/"

# 安装到 Antigravity (可选软链接)
mkdir -p "$HOME/.gemini/antigravity/skills"
ln -sf "${CODEX_HOME:-$HOME/.codex}/skills/gzh-article-pipeline" "$HOME/.gemini/antigravity/skills/gzh-article-pipeline"
```

---

### 2. 配置微信公众号凭证 (可选)

如果你希望开启**「阶段四：一键自动直推草稿箱」**，请配置你的微信公众号开发者凭证（需在公众号后台加白本机 IP）：

#### 方式 1：配置文件
复制 `references/config.example.json` 为 `references/config.json`：
```json
{
  "appid": "your_wechat_appid",
  "appsecret": "your_wechat_appsecret",
  "default_author": "你的公众号作者名"
}
```

#### 方式 2：环境变量
```bash
export WECHAT_APPID="your_wechat_appid"
export WECHAT_APPSECRET="your_wechat_appsecret"
```

---

## 🚀 快速上手示例

### 场景 1：不知写什么？让 AI 策划高转化爆款选题 (模式 A)
直接在对话中输入：
```text
今天选个题
```
或：
```text
按照爆款准则，结合最近的前沿开源项目，帮我策划 3 个公众号选题，说明为什么容易引发转发。
```

---

### 场景 2：已有文章/项目链接或文档，端到端全自动直写 (模式 B)
直接在对话中输入：
```text
Use $gzh-article-pipeline 帮我写这篇公众号文章：

https://github.com/BCUninstaller/Bulk-Crap-Uninstaller
```
或：
```text
用 gzh-article-pipeline 流水线，根据下面这篇架构文档写一篇公众号推文并直推草稿箱：

<粘贴文章或附带本地 Markdown 文件路径>
```

---

## ☕ 赞赏支持与交流合作 (Sponsorship & Contact)

> **开源不易，如果本项目为您或团队省下了宝贵的排版时间与昂贵的第三方编辑器会员费，欢迎请作者喝杯咖啡！您的支持是本项目持续迭代与开源的最大动力。**

| ☕ 微信赞赏支持 (Buy Me a Coffee) | 💬 主理人微信 (交流群 / 商业定制) |
| :---: | :---: |
| <img src="assets/sponsor.png" width="220" alt="微信赞赏支持"> | <img src="assets/wechat.png" width="220" alt="主理人微信"> |
| **觉得好用，请作者喝杯冰美式 ☕** | **扫码添加作者微信（技术交流 / 专属定制）** |

- 🛠️ **专属交钥匙部署与品牌定制服务**：如果您是企业、自媒体团队或高频博主，日常发文量大但不想折腾 Python 环境、服务器 IP 白名单与微信接口调试，提供 30 分钟远程 1v1 极速部署、独家品牌视觉卡片定制交付服务；
- 💬 **添加微信号**：`lukai391424`（备注：`智能体部署` 或 `技术交流`）。

---

## 📄 开源许可证

本项目基于 [MIT License](LICENSE) 开源。欢迎 Star ⭐️ 与 PR！
