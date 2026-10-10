---
name: gzh-article-pipeline
description: >-
  微信公众号全自动推文生产与发布流水线（包含火柴人配图规划与AI原生中文生图、爆款工程学去AI味写作、经典橄榄手记内刊排版与草稿箱一键推送）。
  当用户提供文章链接、文档、主题、大纲或素材，并希望“写公众号推文”、“做公众号排版”、“配火柴人插图”或“发布到公众号草稿箱”时激活本 Skill。
---

# 微信公众号全流程创作与发布流水线 (GZH Article Pipeline)

本 Skill 基于 9月24日破圈级爆款推文（[yt-dlp 深度解析文](https://mp.weixin.qq.com/s/J6uXtqTk8AhrJWPuYz6GIg)，分享率高达 11.45%）提炼的最佳工程实践与视觉规范，形成一套高转化、高分享、排版高级、API 全自动化的微信公众号内容生产与发布闭环：

1. **爆款工程学叙事与去 AI 味写作 (`humanizer-zh`)**：
   - 击中全民级高频痛点（控诉流氓套路，制造受害者情绪共鸣）；
   - 四维黄金标题法 + 颠覆性认知解密（把技术讲成“降妖除魔的攻防爽文”）；
   - 包含超出预期的隐藏神技，文末交付“可抄作业的极简高频命令速查表 + 全维度对比表”，提供极高社交货币。
2. **AI 原生中文火柴人插图与封面安全视窗 (`stick-figure-illustrations`)**：
   - **AI 原生中文绘制**：插图中的招牌、卷轴、旗帜、气泡台词直接由生图模型原生渲染为生动清晰的中文字符；
   - **封面 2.35:1 安全视窗居中法则**：严格适配微信订阅号列表预览（900×383 垂直居中裁剪），顶部预留 25%~30% 留白，文字与核心主体居中下沉，100% 完整展示不被裁切。
3. **经典「橄榄手记 (theme-olive-journal)」标准排版体系**：
   - 严格调用 `references/olive_journal_template.py` 组件库：
     - `section_title(num, title, sub)`：大号 PART 计数器 + 1px 细线分隔 + 纯黑标题 + 灰绿副标；
     - `p(text, align="justify")`：`IBM Plex Sans` 14px，行高 1.9，两端对齐；
     - `editors_note(tag, sub, text)`：暗夜控制台卡片（黑色状态栏 + 浅色底板）；
     - `quote_card(quote_text, author_title)`：4px 经典科技蓝边卡片；
     - `code_block(lang, code_lines)`：深色终端窗与代码命令；
     - `comparison_table(headers, rows)`：细线全屏对比大表；
     - `github_portal_card(...)`：高质感 GitHub 项目传送门卡片；
     - 自动化 `LeafWrapper` 校验，确保 100% `<span leaf="">` 包裹（0 Error 0 Warning）。
4. **微信公众平台 API 直连自动化**：
   - 自动将本地插图上传至微信官方 CDN (`media/uploadimg`)；
   - 自动上传封面图片至永久素材库 (`material/add_material`)；
   - 自动替换 HTML 内图片路径并一键推送到公众号草稿箱 (`draft/add`)。

---

## 微信公众平台开发者凭证配置
- **AppID**: `YOUR_WECHAT_APPID`
- **AppSecret**: `YOUR_WECHAT_APPSECRET`
- **配置文件**: `references/config.json`

---

## 核心工作流 (4 个标准化阶段)

### 阶段一：阅读输入与视觉锚点规划 (Planning & Shot List)
1. **解析输入**：读取用户提供的 Markdown 文件、URL 链接内容（使用 `read_url_content`）、文字草稿或主题大纲；
2. **提炼核心认知转折点与痛点反差**：找出全民级痛点、反常识技术底座（如音画分离）、猫鼠攻防博弈点；
3. **输出规划表格 (Shot List)**：严格使用规范生成候选配图方案表格，**并在 Labels 中明确写出需要 AI 直接绘制的中文文本**：
   `| # | Priority | Placement | Canvas | Theme | Core idea | Composition pattern | Stick-figure action | Emotion | Main objects | Labels (AI 原生中文字符) | Generate? |`
   - **封面设计要求**：必须在 Shot List 中注明 `16:9 (2.35:1 居中安全视窗)`，标明主标题横幅与副标；
4. **强制停顿确认**：输出推荐首选图并提供交互选项（如 `确认方案并生成` / `调整 #1`），**等待用户明确确认后，方可进入下一阶段**。

---

### 阶段二：深度人性化写作 (Humanized Writing)
用户确认规划方案后，结合 **`humanizer-zh`** 与爆款工程学进行深度撰写：
- **拒绝 AI 腔调**：禁止使用“不仅……而且……”、假大空三段式排比、“在这个数字化时代”、“至关重要”、“织锦”、“双刃剑”等套话；
- **爆款叙事节奏**：
  1. *序章*：第一人称控诉普遍经历的恶心流氓痛点，引发强烈共鸣；
  2. *绝活一*：纯粹开源极客体验，与商业全家桶形成剧烈反差；
  3. *绝活二*：颠覆认知科普（“为什么你以前只能下 720P / 为什么会有限速？”），用通俗比喻拆解底层原理；
  4. *绝活三*：猫鼠攻防博弈，还原开源社区逆向破除限制的技术美感；
  5. *绝活四*：超出预期的隐藏神技（如智能切广告）；
  6. *速查表与对比表*：提供可直接抄作业的 5~6 条高频神仙命令，以及四维全方位代际对比大表。

---

### 阶段三：视觉生成与公众号内联排版 (Generation & Formatting)
1. **批量生成插画**：调用 `generate_image` 工具生成所有已批准的 `16:9` 白底/米色底极简黑线火柴人插图：
   - **生图 Prompt 必须明确包含中文文字指令**（例如：`Hand-drawn signboard clearly displaying Chinese text: "创业未半 云账单先破产"`）；
   - **封面严格居中下沉**，确保 2.35:1 裁剪时不切字不切边缘；
2. **组装内联 HTML**：导入或使用 `references/olive_journal_template.py` 中的标准组件拼装正文；
3. **格式合规校验**：运行 `LeafWrapper` 与 `LeafValidator`，确保所有文本节点均被 `<span leaf="">` 包裹，达成 0 Error 0 Warning。

---

### 阶段四：一键推送微信公众号草稿箱 (WeChat Draft Publishing)
当排版与图片准备就绪后，直接运行发布脚本：

```bash
python3 /Users/qcc/.codex/skills/gzh-article-pipeline/scripts/upload_to_wechat.py \
  --html "<排版好的HTML绝对路径>" \
  --images-dir "<图片所在目录>" \
  --title "<文章标题>" \
  --author "奇点造物所" \
  --digest "<120字以内的精准摘要>" \
  --cover "<封面图绝对路径>"
```

**脚本自动执行以下操作**：
1. 请求微信服务器获取有效 `Access Token`；
2. 上传封面图片获取永久素材 `thumb_media_id`；
3. 将 HTML 内所有引用的本地插图上传至微信官方 CDN（`media/uploadimg`），并全自动完成 URL 替换；
4. 调用 `draft/add` 接口提交图文，返回 `Draft Media ID`；
5. 向用户反馈提交结果与公众平台查看路径。

---

## 参考与扩展资料
- `references/olive_journal_template.py`：经典「橄榄手记」标准版式 Python 组件库代码
- `references/viral_playbook.md`：11.45% 爆款分享率复盘实战指南与创作军规
- `references/config.json`：默认 AppID 与 AppSecret 配置文件
