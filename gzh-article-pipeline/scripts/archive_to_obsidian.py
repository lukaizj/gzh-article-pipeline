#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Archive WeChat Official Account articles (HTML / Markdown) into an Obsidian vault.

Features:
1. Converts inline-styled WeChat HTML into clean GitHub-Flavored Markdown (headings,
   lists, blockquotes, code blocks, links, tables, bold text, images).
2. Copies referenced local images (plus optional --cover) into <vault>/assets/<slug>/
   and rewrites Markdown image links to relative Obsidian paths.
3. Writes structured YAML frontmatter and appends an entry to <vault>/00-INDEX.md
   with title/file deduplication.
"""

import argparse
import html
import json
import os
import re
import shutil
import sys
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional, Tuple


DEFAULT_VAULT_DIR = Path.home() / "Documents" / "obsidian-vault" / "gzh-article-kb"


def sanitize_filename(name: str, max_len: int = 80) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|\r\n]+', "", name).strip()
    cleaned = re.sub(r"\s+", "-", cleaned)
    return cleaned[:max_len].strip("-") or "untitled"


def extract_cjk_count(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


class WeChatHTMLToMarkdown(HTMLParser):
    """Lightweight, zero-dependency converter for WeChat inline-styled HTML."""

    def __init__(self, image_resolver=None):
        super().__init__(convert_charrefs=True)
        self.image_resolver = image_resolver
        self.out: List[str] = []
        self.in_pre = False
        self.in_code = False
        self.in_strong = False
        self.in_em = False
        self.in_a = False
        self.a_href = ""
        self.a_text: List[str] = []
        self.in_blockquote = False
        self.list_stack: List[Tuple[str, int]] = []
        self.in_li = False
        self.in_table = False
        self.table_rows: List[List[str]] = []
        self.cur_row: List[str] = []
        self.in_cell = False
        self.cell_buf: List[str] = []
        self.skip_depth = 0
        self.tag_stack: List[Tuple[str, str]] = []
        self.in_section_header = False

    def _emit(self, text: str):
        if self.skip_depth > 0:
            return
        if self.in_cell:
            self.cell_buf.append(text)
        elif self.in_a:
            self.a_text.append(text)
        else:
            self.out.append(text)

    def _ensure_newlines(self, count: int = 2):
        if self.in_cell or self.in_a:
            return
        cur = "".join(self.out[-4:])
        trailing = len(cur) - len(cur.rstrip("\n"))
        if trailing < count:
            self.out.append("\n" * (count - trailing))

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        tag = tag.lower()
        attr_map = {k.lower(): (v or "") for k, v in attrs}
        style = attr_map.get("style", "")
        self.tag_stack.append((tag, style))

        if tag in ("script", "style", "svg", "noscript"):
            self.skip_depth += 1
            return
        if self.skip_depth > 0:
            return

        if tag in ("h1", "h2", "h3", "h4"):
            self._ensure_newlines(2)
            level = int(tag[1])
            self._emit("#" * max(2, level) + " ")
        elif tag == "p":
            if "border-left" in style and ("17px" in style or "16px" in style or "18px" in style or "font-weight:700" in style or "font-weight:800" in style):
                self._ensure_newlines(2)
                self._emit("## ")
                self.in_section_header = True
            elif not self.in_li and not self.in_cell:
                self._ensure_newlines(2)
        elif tag == "br":
            self._emit("  \n" if not self.in_cell else " ")
        elif tag == "hr":
            self._ensure_newlines(2)
            self._emit("---\n\n")
        elif tag == "blockquote":
            self._ensure_newlines(2)
            self.in_blockquote = True
            self._emit("> ")
        elif tag == "pre":
            self._ensure_newlines(2)
            self.in_pre = True
            self._emit("```text\n")
        elif tag == "code":
            if not self.in_pre:
                self.in_code = True
                self._emit("`")
        elif tag in ("strong", "b"):
            if not self.in_section_header and not self.in_strong:
                self.in_strong = True
                self._emit("**")
        elif tag in ("em", "i"):
            if not self.in_em:
                self.in_em = True
                self._emit("*")
        elif tag == "ul":
            self._ensure_newlines(2)
            self.list_stack.append(("ul", 0))
        elif tag == "ol":
            self._ensure_newlines(2)
            self.list_stack.append(("ol", 0))
        elif tag == "li":
            self._ensure_newlines(1)
            self.in_li = True
            indent = "  " * max(0, len(self.list_stack) - 1)
            if self.list_stack and self.list_stack[-1][0] == "ol":
                kind, idx = self.list_stack[-1]
                idx += 1
                self.list_stack[-1] = (kind, idx)
                self._emit(f"{indent}{idx}. ")
            else:
                self._emit(f"{indent}- ")
        elif tag == "a":
            self.in_a = True
            self.a_href = attr_map.get("href", "").strip()
            self.a_text = []
        elif tag == "img":
            src = attr_map.get("src", "").strip() or attr_map.get("data-src", "").strip()
            alt = attr_map.get("alt", "").strip() or "插图"
            if src:
                resolved = self.image_resolver(src) if self.image_resolver else src
                if resolved:
                    self._ensure_newlines(2)
                    self._emit(f"![{alt}]({resolved})")
                    self._ensure_newlines(2)
        elif tag == "table":
            self._ensure_newlines(2)
            self.in_table = True
            self.table_rows = []
        elif tag == "tr" and self.in_table:
            self.cur_row = []
        elif tag in ("td", "th") and self.in_table:
            self.in_cell = True
            self.cell_buf = []

    def handle_endtag(self, tag: str):
        tag = tag.lower()
        if tag in ("script", "style", "svg", "noscript"):
            if self.skip_depth > 0:
                self.skip_depth -= 1
            if self.tag_stack:
                self.tag_stack.pop()
            return
        if self.skip_depth > 0:
            if self.tag_stack:
                self.tag_stack.pop()
            return

        if tag in ("h1", "h2", "h3", "h4"):
            self._ensure_newlines(2)
        elif tag == "p":
            if self.in_section_header:
                self.in_section_header = False
                self._ensure_newlines(2)
            elif self.in_blockquote:
                self._emit("\n> ")
            elif not self.in_li and not self.in_cell:
                self._ensure_newlines(2)
        elif tag == "blockquote":
            self.in_blockquote = False
            self._ensure_newlines(2)
        elif tag == "pre":
            if not (self.out and self.out[-1].endswith("\n")):
                self._emit("\n")
            self._emit("```\n\n")
            self.in_pre = False
        elif tag == "code":
            if self.in_code and not self.in_pre:
                self._emit("`")
                self.in_code = False
        elif tag in ("strong", "b"):
            if self.in_strong:
                self._emit("**")
                self.in_strong = False
        elif tag in ("em", "i"):
            if self.in_em:
                self._emit("*")
                self.in_em = False
        elif tag in ("ul", "ol"):
            if self.list_stack:
                self.list_stack.pop()
            self._ensure_newlines(2)
        elif tag == "li":
            self.in_li = False
            self._ensure_newlines(1)
        elif tag == "a":
            label = "".join(self.a_text).strip()
            href = self.a_href
            self.in_a = False
            self.a_href = ""
            self.a_text = []
            if href and not href.startswith("javascript:"):
                self._emit(f"[{label or href}]({href})")
            elif label:
                self._emit(label)
        elif tag in ("td", "th") and self.in_table:
            cell = re.sub(r"\s+", " ", "".join(self.cell_buf)).strip().replace("|", "\\|")
            self.cur_row.append(cell)
            self.in_cell = False
            self.cell_buf = []
        elif tag == "tr" and self.in_table:
            if self.cur_row:
                self.table_rows.append(self.cur_row)
            self.cur_row = []
        elif tag == "table" and self.in_table:
            self.in_table = False
            if self.table_rows:
                cols = max(len(r) for r in self.table_rows)
                norm = [r + [""] * (cols - len(r)) for r in self.table_rows]
                lines = [
                    "| " + " | ".join(norm[0]) + " |",
                    "| " + " | ".join(["---"] * cols) + " |",
                ]
                for r in norm[1:]:
                    lines.append("| " + " | ".join(r) + " |")
                self._emit("\n".join(lines) + "\n\n")
            self.table_rows = []

        if self.tag_stack:
            self.tag_stack.pop()

    def handle_data(self, data: str):
        if self.skip_depth > 0:
            return
        if self.in_pre:
            self._emit(data)
            return
        # Collapse HTML layout whitespace unless inside pre
        text = re.sub(r"[ \t\r\n]+", " ", data)
        if not text.strip():
            # Preserve single space between inline spans
            if self.out and not self.out[-1].endswith((" ", "\n", "**", "*", "`", "> ")):
                self._emit(" ")
            return
        if self.in_blockquote:
            text = text.lstrip()
        self._emit(text)

    def get_markdown(self) -> str:
        raw = "".join(self.out)
        # Clean up whitespace artifacts
        raw = re.sub(r"\*\*\s+\*\*", "", raw)
        raw = re.sub(r"[ \t]+\n", "\n", raw)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        raw = re.sub(r"^> \s*\n", "", raw, flags=re.M)
        return raw.strip() + "\n"


def resolve_local_image(
    src: str,
    source_dir: Path,
    vault_assets_dir: Path,
    slug: str,
    copied_map: Dict[str, str],
) -> Optional[str]:
    src = src.strip()
    if not src or src.startswith("data:"):
        return None
    if src.startswith(("http://", "https://")):
        return src

    if src in copied_map:
        return copied_map[src]

    # Try relative to source_dir, then fallback to scratch/images if needed
    candidate = Path(src)
    if not candidate.is_absolute():
        candidate = (source_dir / src).resolve()
    if not candidate.exists():
        alt = source_dir / Path(src).name
        if alt.exists():
            candidate = alt
        else:
            return None

    target_dir = vault_assets_dir / slug
    target_dir.mkdir(parents=True, exist_ok=True)
    dst_name = candidate.name
    dst = target_dir / dst_name
    if dst.exists() and dst.stat().st_size != candidate.stat().st_size:
        dst_name = f"{candidate.stem}_{abs(hash(str(candidate))) % 10000}{candidate.suffix}"
        dst = target_dir / dst_name
    if not dst.exists():
        shutil.copy2(candidate, dst)

    rel_link = f"../assets/{slug}/{dst_name}"
    copied_map[src] = rel_link
    return rel_link


def normalize_title(title: str) -> str:
    return re.sub(r"[\W_]+", "", title).lower()


def find_existing_note(folder: Path, title: str, source_file: str) -> Optional[Path]:
    norm_t = normalize_title(title)
    for note in folder.glob("*.md"):
        try:
            head = note.read_text(encoding="utf-8", errors="ignore")[:1500]
            if source_file and f"source_file: {source_file}" in head:
                return note
            m = re.search(r'^title:\s*"?(.+?)"?\s*$', head, re.M)
            if m and normalize_title(m.group(1)) == norm_t:
                return note
        except Exception:
            pass
        if norm_t and norm_t in normalize_title(note.stem):
            return note
    return None


def update_index_md(
    vault_dir: Path,
    folder_name: str,
    note_filename: str,
    title: str,
    category: str,
    summary_short: str,
    status: str,
):
    index_path = vault_dir / "00-INDEX.md"
    if not index_path.exists():
        return
    content = index_path.read_text(encoding="utf-8")
    link_target = f"{folder_name}/{note_filename[:-3]}"
    if link_target in content or title in content:
        return

    # Count existing numbered rows in the target table
    rows = re.findall(r"^\|\s*\*\*(\d+)\*\*\s*\|", content, re.M)
    next_num = max([int(x) for x in rows], default=0) + 1
    safe_title = title.replace("|", "/")
    safe_summary = summary_short.replace("|", "/").replace("\n", " ")[:90]
    new_row = f"| **{next_num:02d}** | [[{link_target}|{safe_title}]] | {category} | {safe_summary} | {status} |\n"

    marker = "## 🎨 视觉资产目录"
    if folder_name == "03-青川的孕期日记":
        sec_header = "## 🤱 青川的孕期日记专栏沉淀"
        if sec_header not in content:
            block = (
                f"\n---\n\n{sec_header}\n\n"
                "| 序号 | 推文标题 | 核心领域 | 摘要 | 草稿箱状态 |\n"
                "| :--- | :--- | :--- | :--- | :--- |\n"
                f"{new_row}"
            )
            if marker in content:
                content = content.replace(marker, block.lstrip("\n") + "\n---\n\n" + marker, 1)
            else:
                content += block
        else:
            # Append right before marker or EOF without inserting --- inside the table
            if marker in content:
                idx = content.index(marker)
                before = content[:idx].rstrip()
                if before.endswith("---"):
                    before = before[:-3].rstrip()
                content = before + "\n" + new_row + "\n---\n\n" + content[idx:]
            else:
                content = content.rstrip() + "\n" + new_row
    else:
        if marker in content:
            idx = content.index(marker)
            before = content[:idx].rstrip()
            # Remove trailing --- right before marker if present, then re-add cleanly
            if before.endswith("---"):
                before = before[:-3].rstrip()
            content = before + "\n" + new_row + "\n---\n\n" + content[idx:]
        else:
            content = content.rstrip() + "\n" + new_row

    index_path.write_text(content, encoding="utf-8")


def archive_article(
    input_path: Path,
    title: str,
    vault_dir: Path = DEFAULT_VAULT_DIR,
    account: str = "奇点造物所",
    folder_name: str = "02-已发布推文专栏",
    date_str: str = "",
    cover_path: Optional[Path] = None,
    status: str = "已推送草稿箱",
    draft_media_id: str = "",
    source_url: str = "",
    category: str = "开源工具 / AI 实战",
    tags: Optional[List[str]] = None,
    read_num: Optional[int] = None,
    rec_ratio: Optional[float] = None,
    overwrite: bool = False,
) -> Optional[Path]:
    if not vault_dir.exists():
        print(f"[archive_to_obsidian] Vault not found at {vault_dir}; skipping archive.")
        return None

    target_folder = vault_dir / folder_name
    target_folder.mkdir(parents=True, exist_ok=True)
    vault_assets_dir = vault_dir / "assets"
    vault_assets_dir.mkdir(parents=True, exist_ok=True)

    if not date_str:
        date_str = datetime.fromtimestamp(input_path.stat().st_mtime).strftime("%Y-%m-%d")

    existing = find_existing_note(target_folder, title, input_path.name)
    if existing and not overwrite:
        print(f"[archive_to_obsidian] Already archived, skipping: {existing.name}")
        return existing

    slug = f"{date_str}-{sanitize_filename(title, 48)}"
    raw_text = input_path.read_text(encoding="utf-8", errors="ignore")
    copied_map: Dict[str, str] = {}

    if input_path.suffix.lower() in (".html", ".htm"):
        parser = WeChatHTMLToMarkdown(
            image_resolver=lambda s: resolve_local_image(s, input_path.parent, vault_assets_dir, slug, copied_map)
        )
        parser.feed(raw_text)
        body_md = parser.get_markdown()
    else:
        body_md = raw_text.strip() + "\n"

    # Extract GitHub / external URL if not given
    if not source_url:
        m_gh = re.search(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", raw_text)
        if m_gh:
            source_url = m_gh.group(0)

    # Copy cover if explicitly provided
    cover_rel = ""
    if cover_path and cover_path.exists():
        cover_rel_link = resolve_local_image(str(cover_path), cover_path.parent, vault_assets_dir, slug, copied_map)
        if cover_rel_link:
            cover_rel = cover_rel_link[3:] if cover_rel_link.startswith("../") else cover_rel_link

    # Build summary from first substantive paragraph
    plain_lines = [
        ln.strip()
        for ln in body_md.splitlines()
        if ln.strip() and not ln.strip().startswith(("#", "!", ">", "-", "*", "`", "|"))
    ]
    summary = plain_lines[0][:140] if plain_lines else title

    tag_list = tags or ([account, "公众号归档"])
    fm_lines = [
        "---",
        f'title: "{title.replace(chr(34), chr(39))}"',
        f"date: {date_str}",
        f"author: {account}",
        f"status: {status}",
        f"cjk_chars: {extract_cjk_count(body_md)}",
    ]
    if draft_media_id:
        fm_lines.append(f"draft_media_id: {draft_media_id}")
    if source_url:
        fm_lines.append(f"source_url: {source_url}")
    if cover_rel:
        fm_lines.append(f"cover: {cover_rel}")
    if read_num is not None:
        fm_lines.append(f"read_num: {read_num}")
    if rec_ratio is not None:
        fm_lines.append(f"rec_ratio: {rec_ratio}")
    fm_lines.append(f"source_file: {input_path.parent.name}/{input_path.name}")
    fm_lines.append("tags:")
    for t in tag_list:
        fm_lines.append(f"  - {t}")
    fm_lines.append("---\n")

    header_parts = [f"# {title}\n", f"> **摘要**：{summary}\n"]
    if cover_rel:
        header_parts.append(f"![封面图](../{cover_rel})\n")

    final_md = "\n".join(fm_lines) + "\n".join(header_parts) + "\n" + body_md
    note_filename = f"{date_str}-{sanitize_filename(title, 65)}.md"
    out_path = target_folder / note_filename
    out_path.write_text(final_md, encoding="utf-8")

    update_index_md(vault_dir, folder_name, note_filename, title, category, summary, status)
    print(f"[archive_to_obsidian] Archived -> {out_path}")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="归档公众号推文 HTML/Markdown 到 Obsidian 知识库")
    parser.add_argument("--input", required=True, help="推文 HTML 或 Markdown 文件路径")
    parser.add_argument("--title", required=True, help="文章标题")
    parser.add_argument("--vault-dir", default=os.environ.get("OBSIDIAN_GZH_VAULT", str(DEFAULT_VAULT_DIR)), help="Obsidian 知识库根目录")
    parser.add_argument("--account", default="奇点造物所", help="公众号名称（奇点造物所 / 青川的孕期日记）")
    parser.add_argument("--folder", default="", help="归档子目录，默认按账号自动映射")
    parser.add_argument("--date", default="", help="发布或成稿日期 YYYY-MM-DD")
    parser.add_argument("--cover", default="", help="可选封面图本地路径")
    parser.add_argument("--status", default="已推送草稿箱", help="文章状态")
    parser.add_argument("--media-id", default="", help="微信草稿箱 media_id")
    parser.add_argument("--source-url", default="", help="关联项目/参考链接")
    parser.add_argument("--category", default="", help="分类标签")
    parser.add_argument("--overwrite", action="store_true", help="若已存在同名笔记则覆盖更新")
    args = parser.parse_args()

    folder = args.folder
    if not folder:
        folder = "03-青川的孕期日记" if "青川" in args.account or "孕" in args.account else "02-已发布推文专栏"
    category = args.category or ("母婴孕产 / 育儿避坑" if folder == "03-青川的孕期日记" else "开源工具 / AI 实战")

    archive_article(
        input_path=Path(args.input).resolve(),
        title=args.title.strip(),
        vault_dir=Path(args.vault_dir).expanduser(),
        account=args.account.strip(),
        folder_name=folder,
        date_str=args.date.strip(),
        cover_path=Path(args.cover).resolve() if args.cover else None,
        status=args.status.strip(),
        draft_media_id=args.media_id.strip(),
        source_url=args.source_url.strip(),
        category=category,
        overwrite=args.overwrite,
    )


if __name__ == "__main__":
    main()
