# 🚀 GZH Article Pipeline (微信公众号全自动推文生产与发布流水线)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Codex Skill](https://img.shields.io/badge/Codex-Skill-green.svg)](https://github.com/openai/codex)
[![Antigravity](https://img.shields.io/badge/Google-Antigravity-orange.svg)](https://deepmind.google)
[![WeChat Official Account](https://img.shields.io/badge/WeChat-Official%20Account%20API-07C160.svg)](https://mp.weixin.qq.com)

> **把文章链接、演讲稿或技术文档，一键转化为带火柴人插图、深度去 AI 味、排版精致并直推微信公众号草稿箱的爆款推文。**

---

## 💡 为什么需要这个 Skill？

传统的 AI 写公众号推文往往存在以下痛点：
1. **AI 味浓厚**：充斥着“不仅……而且……”、“在这个数字化转型的时代”、“至关重要”等假大空废话，缺乏真实一线工程质感；
2. **配图与内容割裂**：使用泛化的 AI 绘画或生硬的架构图，读者看不懂也记不住；
3. **排版繁琐脆弱**：排版工具格式混乱，复制粘贴进公众号经常丢失边框、代码高亮和样式；
4. **人工搬运繁重**：每次都要手动下载图片、上传公众号后台、一张张替换、排版、存草稿。

**`gzh-article-pipeline` 将 3 个专业 Skill 与微信官方 API 打通，提供确定性、高品质的推文创作与发布闭环。**

---

## 🏗️ 核心工作流 (4 阶段)

```text
[用户输入] (文章链接 / Markdown / 演讲稿)
   │
   ▼
[阶段 1: 视觉锚点规划] (基于 stick-figure-illustrations)
   ├─ 提炼核心认知转折点
   ├─ 输出 16:9 火柴人草图规划表 (Shot List)
   └─ ⏸️ 强制停顿，等待用户确认
   │
   ▼ (用户确认后)
[阶段 2: 深度去 AI 味撰写] (基于 humanizer-zh)
   ├─ 去除所有 LLM 机械套话
   └─ 注入真实一线实战口吻，讲深讲透
   │
   ▼
[阶段 3: 视觉生成与内刊排版] (基于 gzh-design-skill)
   ├─ 批量生成 16:9 白底极简火柴人插图
   ├─ 组装「橄榄手记」/「摸鱼绿」内联样式 HTML
   └─ 100% 格式合规校验 (<span leaf=""> 0 Warning)
   │
   ▼
[阶段 4: 一键推送草稿箱] (WeChat API 直连)
   ├─ 自动上传封面素材 (thumb_media_id)
   ├─ 自动上传正文插图至微信 CDN 并替换 HTML
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

在对话中输入：

```text
Use $gzh-article-pipeline 帮我写这篇公众号文章：

https://example.com/some-tech-article-or-doc
```
或：
```text
用 gzh-article-pipeline 流水线，根据下面这篇架构文档写一篇公众号推文：

<粘贴文章或附带本地 Markdown 文件路径>
```

---

## 📄 开源许可证

本项目基于 [MIT License](LICENSE) 开源。欢迎 Star ⭐️ 与 PR！
