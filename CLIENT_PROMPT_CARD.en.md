# GZH Article Pipeline · Natural-Language Prompt Card

> 💡 **How to use**: No need to memorize CLI flags—just copy and paste any prompt below into your AI coding assistant (Codex / Antigravity / Claude Code) with this skill installed. See [README.en.md](README.en.md) for setup details.

---

## Scenario 1: Topic Ideation (Dual-High eCPM/CTR)
When you need fresh article ideas calibrated to high-RPM verticals and past performance:

> 🗣️ **Say to your AI**:
> “Pick 3 WeChat Official Account article topics for today using `gzh-article-pipeline`. Check repo liveliness first, prioritize high-eCPM verticals, keep the framing jargon-free for general readers, and provide 3 title candidates per topic.”

---

## Scenario 2: URL / GitHub Repo to Draft Box (End-to-End)
When you spot a useful open-source project or product link and want a full article pushed to your Draft Box:

> 🗣️ **Say to your AI**:
> “Use `gzh-article-pipeline` to write an article about `<URL>`. Verify project status first, draft `950~1300` CJK characters in short mobile paragraphs, generate a story-driven `21:9` full-bleed cover, pass all 9 QA checks, and push it to my WeChat Draft Box.”

---

## Scenario 3: Existing Draft / Notes to Inline Formatting & Cover
When you already wrote notes in Notion, Feishu, or Markdown and want inline WeChat formatting plus a cover:

> 🗣️ **Say to your AI**:
> “Format the draft below using `olive_journal_template.py` inline styles, generate a matching `21:9` story cover, run `validate_article.py`, and push to my WeChat Draft Box:
>
> [Paste your draft here]”

---

## Scenario 4: Little Green Book (`newspic`) Safe-Crop Push
When publishing an image-first WeChat `newspic` post:

> 🗣️ **Say to your AI**:
> “Use the `upload_newspic` workflow to publish a Little Green Book post about `[topic]`. Keep the title within 20 characters, wrap the visual in the center safe zone, and verify the rendered `203×270` card after pushing to the Draft Box.”

---

## Scenario 5: In-Place Draft Update (New Title / Cover)
When an article is already in the Draft Box and you want to swap the title or cover without creating a duplicate draft:

> 🗣️ **Say to your AI**:
> “Update the latest draft in my WeChat Draft Box in-place (`--update-draft`): change the title to `《[New Title <= 26 chars, score >= 75]》` and regenerate a `21:9` cover emphasizing `[specific pain point]`.”

---

## Scenario 6: Keyless Backend Analytics Review
When diagnosing CTR, completion rate, or share-rate bottlenecks without configuring `appid` / `appsecret`:

> 🗣️ **Say to your AI**:
> “Use `wechat-content-analysis` to pull the latest 30 published articles from my signed-in Chrome `mp.weixin.qq.com` session, break down recommendation vs. follower traffic, and suggest next-issue topic adjustments.”

---

## Quick FAQ

- **Will pushing to the Draft Box publish directly to followers?**
  - **No.** Scripts only write to your WeChat Draft Box so you can preview and publish manually.
- **What does WeChat API error `40164` mean?**
  - Your current public IP is not in the WeChat Official Account IP whitelist. Add your current IP under *Settings & Development ➔ Basic Configuration ➔ IP Whitelist* in the WeChat MP backend.
- **Can I run QA and analytics without configuring `appid` / `appsecret`?**
  - **Yes.** `validate_article.py` (offline QA) and `pull_and_analyze_mp.py` (using your logged-in Chrome session on macOS) require zero WeChat API credentials.
