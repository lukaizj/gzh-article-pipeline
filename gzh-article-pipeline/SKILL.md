---
name: gzh-article-pipeline
description: >-
  微信公众号全自动推文生产与发布流水线（包含火柴人配图规划、去AI味人性化写作、专业内刊排版与草稿箱一键推送）。
  当用户提供文章链接、文档、主题、大纲或素材，并希望“写公众号推文”、“做公众号排版”、“配火柴人插图”或“发布到公众号草稿箱”时激活本 Skill。
---

# 微信公众号全流程创作与发布流水线 (GZH Article Pipeline)

本 Skill 整合了三大核心能力与官方 API 直连，形成一套确定性、高质量的微信公众号内容生产与发布闭环：
1. **`stick-figure-illustrations`**：提炼视觉锚点，规划火柴人（16:9）草图隐喻与 Shot List（先规划，用户确认后再批量生图）；
2. **`humanizer-zh`**：去除 AI 痕迹，以一线资深工程师/作者的真实口吻，输出透彻、深刻、接地气的正文；
3. **`gzh-design-skill`**：自动进行公众号内联样式排版（推荐「橄榄手记」内刊风或「摸鱼绿」），实现 100% 格式合规校验（`<span leaf="">` 包裹，0 报错 0 告警）；
4. **微信公众平台 API 直连**：自动将所有本地插图上传至微信 CDN、上传封面素材，并一键推送到微信公众号草稿箱。

---

## 核心工作流 (4 个标准化阶段)

### 阶段一：阅读输入与视觉锚点规划 (Planning & Shot List)
1. **解析输入**：读取用户提供的 Markdown 文件、URL 链接内容（使用 `read_url_content`）、文字草稿或主题大纲；
2. **提炼核心认知转折点**：找出读者卡点、架构分工、反直觉结论或流程闭环；
3. **输出规划表格 (Shot List)**：严格使用 `stick-figure-illustrations` 规范生成候选配图方案表格：
   `| # | Priority | Placement | Canvas | Theme | Core idea | Composition pattern | Stick-figure action | Emotion | Main objects | Labels | Generate? |`
4. **强制停顿确认**：输出推荐首选图并提供交互选项（如 `确认方案并生成` / `调整 #1`），**等待用户明确确认后，方可进入下一阶段**。

---

### 阶段二：深度人性化写作 (Humanized Writing)
用户确认规划方案后，结合 **`humanizer-zh`** 进行深度内容撰写：
- **拒绝 AI 腔调**：禁止使用“不仅……而且……”、假大空三段式排比、“在这个数字化时代”、“至关重要”、“织锦”等套话；
- **注入真实工程灵魂**：使用第一人称或真实一线实战口吻，讲透技术原理、踩坑细节与权衡取舍；
- **图文紧密呼应**：在文章每个认知停顿点自然嵌入规划好的火柴人插图，用生动的动作场景辅助解释抽象概念；
- **讲深讲透**：不流于表面概括，深入机制底层，篇幅充实。

---

### 阶段三：视觉生成与公众号内联排版 (Generation & Formatting)
1. **批量生成插画**：调用 `generate_image` 工具生成所有已批准的 `16:9` 白底极简黑线 + 科技蓝/终端绿点缀色的火柴人插图，保存在工作目录；
2. **组装内联 HTML**：使用 `gzh-design-skill` 中的主题组件（首选「橄榄手记」`theme-olive-journal`，或根据题材匹配「摸鱼绿」`theme-moyu-green`）；
3. **格式合规校验**：运行合规校验脚本，确保所有文本节点均被 `<span leaf="">` 包裹，达成 0 Error 0 Warning；
4. **生成一键复制预览页**：运行 `wrap_preview.py` 生成带「复制到公众号」按钮的 HTML 预览文件。

---

### 阶段四：一键推送微信公众号草稿箱 (WeChat Draft Publishing)
当用户发出“上传到草稿箱”、“发布”或完成流程时，直接执行内置发布脚本：

```bash
python3 gzh-article-pipeline/scripts/upload_to_wechat.py \
  --html "<排版好的HTML绝对路径>" \
  --images-dir "<图片所在目录>" \
  --title "<文章标题>" \
  --author "<作者名>" \
  --digest "<120字以内的精准摘要>" \
  --cover "<封面图绝对路径>"
```

**脚本自动执行以下操作**：
1. 请求微信服务器获取有效 `Access Token`；
2. 上传封面图片获取永久素材 `thumb_media_id`；
3. 将 HTML 内所有引用的本地插图上传至微信官方 CDN（`media/uploadimg`），并全自动完成 URL 替换；
4. 调用 `draft/add` 接口提交图文，返回 `Draft Media ID`；
5. 向用户反馈提交结果与公众平台查看路径。
