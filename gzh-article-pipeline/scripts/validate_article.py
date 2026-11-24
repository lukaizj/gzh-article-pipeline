#!/usr/bin/env python3
"""
GZH Article Pipeline Quality & Compliance Validator (Offline)

Combines Olive Journal structural validation with editorial quality gates:
1. Title 4-dimension score (15/35/15/35) + length <= 26 + jargon check
2. Pure CJK character count window (1000 ~ 1300 target)
3. Mobile paragraph length check (2 ~ 3 lines / <= 65 CJK chars per para)
4. AI buzzword & mechanical ending detector
5. Platform/compliance prohibited word check with English boundary matching
6. Visual pacing / image cadence check (~every 300 chars)
7. Info density per 400-CJK chunk (numbers / concrete actions)
8. Opening-3-sentences & light-ending / HTML clean rules check
9. <span leaf=""> integrity via LeafValidator (for HTML inputs)
"""

import argparse
import json
import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
REF_DIR = SCRIPT_DIR.parent / "references"
if str(REF_DIR) not in sys.path:
    sys.path.insert(0, str(REF_DIR))

try:
    from olive_journal_template import LeafValidator
except ImportError:
    LeafValidator = None

# 标题绝对禁用黑话 & 低级死刑词
TITLE_JARGON_BLACKLIST = [
    "MD", "Markdown", "Agent", "智能体", "紫微斗数", "天纪",
    "DNS", "软路由", "旁路由", "抓包", "逆向", "端口映射",
    "固件", "编译", "内网穿透", "AI切片", "战情室", "KDBX", "Docker",
]
TITLE_GEEK_LABELS = ["GitHub", "开源", "万星"]
LOW_ECPM_BAIT_WORDS = ["白嫖", "破解版", "全网看剧", "打游戏"]
HARD_BANNED_WORDS = ["逼氪"]
PUBLIC_AUDIENCE_KEYWORDS = [
    "电脑", "手机", "浏览器", "微信", "U盘", "电视", "大屏", "汽车",
    "PDF", "合同", "发票", "银行", "证券", "密码", "金库", "会员", "VIP",
    "录音笔", "会议", "纪要", "语音", "网课", "英语", "内存", "空间",
    "广告", "文件", "弹窗", "老旧", "省钱", "免费",
]
HIGH_ECPM_ANCHOR_KEYWORDS = [
    "合同", "发票", "报销", "财务", "银行", "证券", "账密", "密码", "金库",
    "PDF", "办公", "Excel", "会议", "纪要", "录音笔", "网课", "英语", "企业", "会员", "VIP",
]
VIRAL_HOOK_KEYWORDS = [
    "恶心吐了", "坑爹", "流氓", "别再", "别让", "别花", "别开", "别扔", "别当",
    "太危险", "冤枉钱", "一键", "1秒", "秒变", "连根拔起", "翻倍", "拉满",
    "骗了你", "扒透", "锁死", "彻底", "神作", "神器", "省下", "出精华", "全免费",
]

AI_BUZZWORDS = [
    "赋能", "抓手", "打法", "闭环", "颗粒度", "对齐", "沉淀",
    "方法论前置", "底层逻辑", "心智", "调性",
]
AI_PATTERNS = [
    r"在当今.{0,15}的时代",
    r"众所周知",
    r"不言而喻",
    r"综上所述",
    r"总而言之",
    r"最后总结一下",
    r"不仅.{1,25}而且",
    r"!!!+",
]

COMPLIANCE_REDLINES = [
    (r"后台回复.{0,12}(领取|获取|密码|暗号)", "禁止后台回复暗号引流话术"),
    (r"(评论区|留言区).{0,10}(聊聊|说说|提问|分享)", "文末禁止评论区/留言区盖楼引导"),
    (r"周杰伦.{0,12}(免费|白嫖|VIP|破解)", "禁止触碰腾讯音乐周杰伦独家版权红线"),
    (r"(QQ音乐|腾讯视频).{0,12}(VIP|SVIP|破解|白嫖)", "禁止触碰腾讯系 VIP 白嫖版权红线"),
    (r"(微信群控|微信外挂|微信协议破解)", "禁止触碰微信生态外挂红线"),
    (r"(全网最全|绝对第一|永久破解|100%有效)", "避免广告法极限/绝对化用词"),
]
ENGLISH_RISKY_WORDS = ["crack", "keygen", "pirate", "warez"]


class OliveHTMLInspector(HTMLParser):
    """Extract clean prose paragraphs, images, tables, headings, and profile tags."""

    def __init__(self) -> None:
        super().__init__()
        self.paragraphs: List[str] = []
        self.images: List[str] = []
        self.table_count = 0
        self.h1_count = 0
        self.has_mp_profile = False
        self._in_p = False
        self._p_buf: List[str] = []
        self._p_is_caption = False
        self._tag_stack: List[Tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        attr_map = dict(attrs)
        style = attr_map.get("style") or ""
        self._tag_stack.append((tag, style))

        if tag == "img":
            self.images.append(attr_map.get("src") or "")
        elif tag == "table":
            self.table_count += 1
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "mp-common-profile":
            self.has_mp_profile = True
        elif tag == "p":
            self._in_p = True
            self._p_buf = []
            # 12px/11px captions or card subtitles shouldn't trigger body para checks
            self._p_is_caption = ("font-size:12px" in style) or ("font-size:11px" in style) or ("font-size:16px" in style)

    def handle_endtag(self, tag: str) -> None:
        if tag == "p" and self._in_p:
            text = "".join(self._p_buf).strip()
            if text and not self._p_is_caption:
                in_special_card = any(
                    ("background:#fdfdf8" in s) or ("background:#f7f8f4" in s) or ("border-collapse:collapse" in s)
                    for _, s in self._tag_stack
                )
                if not in_special_card:
                    self.paragraphs.append(text)
            self._in_p = False
            self._p_buf = []
        if self._tag_stack:
            self._tag_stack.pop()

    def handle_data(self, data: str) -> None:
        if self._in_p:
            self._p_buf.append(data)


def count_cjk(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def score_title_4dim(title: str) -> Tuple[int, str, Dict[str, int], List[str]]:
    """Estimate 4-dimension score (15 + 35 + 15 + 35 = 100) for a WeChat title."""
    notes: List[str] = []
    # a. Audience + high-eCPM commercial scenario match (15)
    aud_hits = [k for k in PUBLIC_AUDIENCE_KEYWORDS if k.lower() in title.lower()]
    ecpm_hits = [k for k in HIGH_ECPM_ANCHOR_KEYWORDS if k.lower() in title.lower()]
    jargon_hits = [
        k for k in TITLE_JARGON_BLACKLIST
        if (bool(re.search(rf"(?<![a-zA-Z]){re.escape(k)}(?![a-zA-Z])", title, re.I)) if k.isascii() else (k in title))
    ]
    geek_hits = [k for k in TITLE_GEEK_LABELS if k.lower() in title.lower()]
    low_ecpm_hits = [k for k in LOW_ECPM_BAIT_WORDS if k in title]

    if jargon_hits:
        dim_a = 0
        notes.append(f"命中极客/小众黑话 {jargon_hits}，定位偏离扣至 0 分")
    elif len(aud_hits) >= 2 and ecpm_hits:
        dim_a = 15
    elif len(aud_hits) >= 2:
        dim_a = 12
        notes.append("具备大众受众词，若能嵌入合同/银行/会议/会员等高 eCPM 锚点词可进一步抬高单价")
    elif len(aud_hits) == 1:
        dim_a = 9
    else:
        dim_a = 4
        notes.append("缺少大众日常与高净值场景词（如银行/合同/PDF/会议/手机/电脑/会员），建议替换")

    if geek_hits:
        notes.append(f"标题包含技术门脸词 {geek_hits}，按双高模型建议改用省钱/安全/效率利益点")
    if low_ecpm_hits:
        dim_a = max(0, dim_a - 5)
        notes.append(f"命中低 eCPM 引流词 {low_ecpm_hits}，极易被系统塞入低单价广告")

    # b. Click hook intensity (35)
    hook_hits = [k for k in VIRAL_HOOK_KEYWORDS if k in title]
    has_num = bool(re.search(r"\d+", title))
    has_pain = any(w in title for w in ["恶心", "坑爹", "流氓", "别", "危险", "冤枉", "删", "费眼", "限速", "收费", "会员", "VIP"])
    dim_b = 10
    if has_pain:
        dim_b += 10
    if len(hook_hits) >= 2:
        dim_b += 10
    elif len(hook_hits) == 1:
        dim_b += 6
    if has_num or "免费" in title or "神器" in title or "金库" in title:
        dim_b += 5
    dim_b = min(35, dim_b)

    # c. Structure compliance (15)
    tlen = len(title)
    dim_c = 8 if 15 <= tlen <= 26 else (4 if tlen <= 30 else 0)
    if not jargon_hits and tlen <= 26:
        dim_c += 7
    elif tlen > 26:
        notes.append(f"标题长度 {tlen} 字超过 26 字上限，会被列表折叠截断")

    # d. Viral + High-eCPM template similarity (35)
    is_pure_question = title.endswith(("吗？", "怎么样？", "好不好？"))
    has_emotive_colon = ("！" in title or "？" in title) and ("：" in title or "，" in title)
    dim_d = 12
    if is_pure_question:
        dim_d = 6
        notes.append("纯设问弱标题属于 E 级高危格式（历史均阅低）")
    else:
        if has_emotive_colon:
            dim_d += 12
        if ecpm_hits or any(w in title for w in ["神作", "神器", "金库", "全免费", "出精华"]):
            dim_d += 11
    dim_d = min(35, dim_d)

    total = dim_a + dim_b + dim_c + dim_d
    grade = "S" if total >= 90 else ("A" if total >= 75 else ("B" if total >= 60 else "C"))
    return total, grade, {
        "audience_match_15": dim_a,
        "click_hook_35": dim_b,
        "structure_15": dim_c,
        "viral_potential_35": dim_d,
    }, notes


def parse_input(path: Path) -> Dict:
    raw = path.read_text(encoding="utf-8")
    is_html = path.suffix.lower() in (".html", ".htm") or "<section" in raw

    if is_html:
        inspector = OliveHTMLInspector()
        inspector.feed(raw)
        plain = re.sub(r"<[^>]+>", " ", raw)
        plain = re.sub(r"\s+", " ", plain).strip()
        return {
            "is_html": True,
            "raw": raw,
            "plain": plain,
            "paragraphs": inspector.paragraphs,
            "images": inspector.images,
            "table_count": inspector.table_count,
            "h1_count": inspector.h1_count,
            "has_mp_profile": inspector.has_mp_profile,
            "md_title": "",
        }

    # Markdown fallback parser
    md_title = ""
    images = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", raw)
    stripped = re.sub(r"```.*?```", "", raw, flags=re.DOTALL)
    stripped = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", stripped)
    paragraphs = []
    for block in re.split(r"\n\s*\n", stripped):
        b = block.strip()
        if not b or b.startswith("#") or b.startswith("|") or b.startswith("---"):
            if b.startswith("# ") and not md_title:
                md_title = b[2:].strip()
            continue
        paragraphs.append(re.sub(r"[*_`>\[\]]", "", b))
    plain = re.sub(r"[#*>`_|\[\]()]", " ", stripped)
    plain = re.sub(r"\s+", " ", plain).strip()
    return {
        "is_html": False,
        "raw": raw,
        "plain": plain,
        "paragraphs": paragraphs,
        "images": images,
        "table_count": len(re.findall(r"\n\|[-:\s|]+\|\n", raw)),
        "h1_count": 0,
        "has_mp_profile": True,
        "md_title": md_title,
    }


def run_validation(path: Path, title: str, min_cjk: int, max_cjk: int) -> Dict:
    parsed = parse_input(path)
    effective_title = title or parsed["md_title"]
    plain = parsed["plain"]
    raw = parsed["raw"]
    paragraphs = parsed["paragraphs"]

    checks: Dict[str, Dict] = {}
    hard_fails = 0
    warnings = 0

    def record(name: str, status: str, detail: Dict) -> None:
        nonlocal hard_fails, warnings
        checks[name] = {"status": status, **detail}
        if status == "fail":
            hard_fails += 1
        elif status == "warning":
            warnings += 1

    # 1. Title 4-dim score & length
    if effective_title:
        score, grade, dims, notes = score_title_4dim(effective_title)
        banned_in_title = [w for w in HARD_BANNED_WORDS if w in effective_title]
        if len(effective_title) > 26 or banned_in_title:
            status = "fail"
        elif score < 75:
            status = "warning"
        else:
            status = "pass"
        record("title_quality", status, {
            "title": effective_title,
            "length": len(effective_title),
            "score": score,
            "grade": grade,
            "dimensions": dims,
            "notes": notes + ([f"禁用词: {banned_in_title}"] if banned_in_title else []),
        })
    else:
        record("title_quality", "warning", {"notes": ["未传入 --title，跳过标题四维打分"]})

    # 2. Pure CJK count
    cjk_total = count_cjk(plain)
    if cjk_total > 1500:
        wc_status = "warning"
        wc_note = "纯汉字超 1500 字，极易触发『收藏吃灰』中途跳出导致完读率崩盘"
    elif min_cjk <= cjk_total <= max_cjk:
        wc_status = "pass"
        wc_note = f"处于 {min_cjk}~{max_cjk} 黄金精读区间"
    else:
        wc_status = "warning"
        wc_note = f"建议控制在 {min_cjk}~{max_cjk} 纯汉字（当前 {cjk_total} 字）"
    record("word_count", wc_status, {"cjk_chars": cjk_total, "note": wc_note})

    # 3. Mobile paragraph lines (<= 65 CJK chars ~ 3-4 lines on mobile)
    long_paras = []
    for idx, para in enumerate(paragraphs, 1):
        pcjk = count_cjk(para)
        if pcjk > 65:
            long_paras.append({"para_index": idx, "cjk_chars": pcjk, "preview": para[:36] + "..."})
    record("mobile_paragraph_lines", "warning" if long_paras else "pass", {
        "long_paragraph_count": len(long_paras),
        "threshold_cjk": 65,
        "examples": long_paras[:5],
    })

    # 4. AI buzzwords & mechanical endings
    ai_hits = [w for w in AI_BUZZWORDS if w in plain]
    pat_hits = [p for p in AI_PATTERNS if re.search(p, plain)]
    record("ai_buzzwords", "warning" if (ai_hits or pat_hits) else "pass", {
        "buzzwords": ai_hits,
        "mechanical_patterns": pat_hits,
    })

    # 5. Compliance & word-boundary scan
    comp_hard = []
    comp_warn = []
    for w in HARD_BANNED_WORDS:
        if w in raw:
            comp_hard.append(f"触发绝对死刑词: {w}")
    for pat, msg in COMPLIANCE_REDLINES:
        if re.search(pat, plain):
            comp_warn.append(msg)
    for ew in ENGLISH_RISKY_WORDS:
        if re.search(rf"(?<![a-zA-Z]){ew}(?![a-zA-Z])", plain, re.I):
            comp_warn.append(f"含高风险英文敏感词: {ew}")
    c_status = "fail" if comp_hard else ("warning" if comp_warn else "pass")
    record("compliance_redlines", c_status, {"hard_violations": comp_hard, "warnings": comp_warn})

    # 6. Image cadence (~every 300-450 CJK chars)
    img_cnt = len(parsed["images"])
    chars_per_img = round(cjk_total / max(1, img_cnt))
    img_ok = (img_cnt >= 2) and (chars_per_img <= 480)
    record("image_cadence", "pass" if img_ok else "warning", {
        "image_count": img_cnt,
        "cjk_per_image": chars_per_img,
        "note": "达标（每图间距合理）" if img_ok else "插图偏少或图文间距过大，建议约每300字配一张图",
    })

    # 7. Info density per ~400 CJK chunk
    body_joined = "".join(paragraphs)
    chunks = [body_joined[i:i + 400] for i in range(0, max(1, len(body_joined)), 400)]
    dry_chunks = []
    for ci, ch in enumerate(chunks, 1):
        has_concrete = bool(re.search(r"\d|MB|GB|TB|秒|分钟|小时|元|星|打开|点击|拖入|解压", ch))
        if len(ch) > 150 and not has_concrete:
            dry_chunks.append({"chunk": ci, "preview": ch[:35] + "..."})
    record("info_density", "warning" if dry_chunks else "pass", {
        "chunks_checked": len(chunks),
        "low_density_chunks": dry_chunks,
    })

    # 8. Opening-3-paragraphs & HTML structural rules
    first3_text = " ".join(paragraphs[:3])
    first3_cjk = sum(count_cjk(x) for x in paragraphs[:3])
    struct_fails = []
    struct_warns = []
    if parsed["is_html"]:
        if parsed["h1_count"] > 0:
            struct_fails.append(f"检测到 {parsed['h1_count']} 个 <h1> 标签，严禁在正文顶部重复大标题")
        raw_no_img_src = re.sub(r'src="[^"]*"', "", raw)
        if "/Users/" in raw_no_img_src or "C:\\" in raw_no_img_src:
            struct_fails.append("检测到正文非图片路径区域泄露本地磁盘路径 (/Users/ 或 C:\\)")
        if not parsed["has_mp_profile"]:
            struct_warns.append("正文末尾未检测到 <mp-common-profile> 公众号名片（推送脚本可自动补全）")
    if first3_cjk > 190:
        struct_warns.append(f"前三段总字数 {first3_cjk} 字偏长，建议控制在 190 字内只做痛点与悬念钩子")
    if re.search(r"https?://|github\.com", first3_text, re.I):
        struct_warns.append("前 3 段直接暴露网址或仓库链接，易致读者收藏即退出拉低完读率（请移至中后段/传送门）")
    if parsed["table_count"] > 2:
        struct_warns.append(f"表格数量为 {parsed['table_count']} 张，建议控制在 1~2 张以内")
    st_status = "fail" if struct_fails else ("warning" if struct_warns else "pass")
    record("opening_and_structure", st_status, {
        "first3_paragraphs_cjk": first3_cjk,
        "table_count": parsed["table_count"],
        "fails": struct_fails,
        "warnings": struct_warns,
    })

    # 9. LeafWrapper integrity
    if parsed["is_html"] and LeafValidator is not None:
        bare, _ = LeafValidator.validate(raw)
        record("leaf_integrity", "fail" if bare else "pass", {
            "bare_text_nodes": len(bare),
            "examples": bare[:5],
        })

    return {
        "file": str(path),
        "summary": {
            "hard_fails": hard_fails,
            "warnings": warnings,
            "passed": sum(1 for c in checks.values() if c["status"] == "pass"),
        },
        "checks": checks,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="微信公众号文章 9 项质量与合规自动校验器")
    parser.add_argument("--input", required=True, help="待校验的 HTML 或 Markdown 文件路径")
    parser.add_argument("--title", default="", help="文章标题（可选，用于四维评分与黑话检测）")
    parser.add_argument("--min-cjk", type=int, default=950, help="纯汉字最低建议值（默认 950）")
    parser.add_argument("--max-cjk", type=int, default=1300, help="纯汉字最高建议值（默认 1300）")
    parser.add_argument("--json", default="", help="可选，导出完整 JSON 质检报告的路径")
    parser.add_argument("--strict", action="store_true", help="严格模式：存在任意 warning 也返回非零退出码")
    args = parser.parse_args()

    target = Path(args.input).expanduser().resolve()
    if not target.exists():
        print(f"❌ 文件不存在: {target}")
        sys.exit(2)

    report = run_validation(target, args.title, args.min_cjk, args.max_cjk)

    if args.json:
        out_p = Path(args.json).expanduser().resolve()
        out_p.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 64)
    print(f"📋 公众号文章质检报告: {target.name}")
    print("=" * 64)
    icons = {"pass": "[PASS]", "warning": "[WARN]", "fail": "[FAIL]"}
    for name, detail in report["checks"].items():
        st = detail["status"]
        line = f"  {icons[st]} {name:<26}"
        if name == "title_quality" and "score" in detail:
            line += f" {detail['score']}/100 ({detail['grade']}级, {detail['length']}字)"
        elif name == "word_count":
            line += f" {detail['cjk_chars']} 纯汉字 ({detail['note']})"
        elif name == "mobile_paragraph_lines":
            line += f" 超长段落: {detail['long_paragraph_count']}"
        elif name == "image_cadence":
            line += f" {detail['image_count']} 图 (~{detail['cjk_per_image']}字/图)"
        elif name == "leaf_integrity":
            line += f" 裸文本节点: {detail['bare_text_nodes']}"
        print(line)
        if st in ("warning", "fail"):
            for k in ("notes", "examples", "buzzwords", "mechanical_patterns", "hard_violations", "warnings", "fails"):
                v = detail.get(k)
                if v:
                    print(f"       -> {k}: {v}")
    s = report["summary"]
    print("=" * 64)
    print(f"汇总: PASS={s['passed']} | WARN={s['warnings']} | FAIL={s['hard_fails']}")

    if s["hard_fails"] > 0:
        sys.exit(1)
    if args.strict and s["warnings"] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
