# -*- coding: utf-8 -*-
"""
WeChat Upload & Draft Engine (微信公众平台直连发布与素材上传引擎)
支持新建草稿 (draft/add)、覆盖更新 (draft/update)、图片批量上云与 2.35:1 封面智能安全裁切。
"""

import os
import re
import sys
import json
import argparse
import requests
from PIL import Image

def find_and_load_config():
    """多级路径智能嗅探 config.json"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, "..", "references", "config.json"),
        os.path.join(script_dir, "config.json"),
        os.path.join(os.getcwd(), "config.json"),
        os.path.join(os.getcwd(), "references", "config.json"),
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                with open(c, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    return {}

CFG = find_and_load_config()
DEFAULT_APPID = CFG.get("appid", "")
DEFAULT_APPSECRET = CFG.get("appsecret", "")
DEFAULT_AUTHOR = CFG.get("default_author", "奇点造物所")

def get_access_token(appid, appsecret):
    """获取 Access Token"""
    if not appid or not appsecret:
        raise ValueError("微信 AppID 或 AppSecret 为空！请在 references/config.json 中配置，或通过参数传入。")
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={appsecret}"
    resp = requests.get(url, timeout=15)
    data = resp.json()
    if "access_token" in data:
        return data["access_token"]
    else:
        raise Exception(f"获取微信 Access Token 失败: {json.dumps(data, ensure_ascii=False)}")

def upload_news_img(access_token, file_path):
    """上传正文插图至微信 CDN (media/uploadimg)"""
    url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={access_token}"
    with open(file_path, "rb") as f:
        files = {"media": f}
        resp = requests.post(url, files=files, timeout=30)
    data = resp.json()
    if "url" in data:
        return data["url"]
    else:
        raise Exception(f"上传正文图片到微信 CDN 失败 ({file_path}): {json.dumps(data, ensure_ascii=False)}")

def upload_thumb_material(access_token, file_path):
    """上传封面图获取永久素材 thumb_media_id (material/add_material)"""
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
    with open(file_path, "rb") as f:
        files = {"media": f}
        resp = requests.post(url, files=files, timeout=30)
    data = resp.json()
    if "media_id" in data:
        return data["media_id"]
    else:
        raise Exception(f"上传封面图素材失败 ({file_path}): {json.dumps(data, ensure_ascii=False)}")

def add_draft(access_token, title, author, digest, content, thumb_media_id, open_comment=1):
    """提交新建草稿"""
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
    if len(digest) > 120:
        digest = digest[:116] + "..."

    payload = {
        "articles": [
            {
                "title": title[:64],
                "author": author[:8],
                "digest": digest,
                "content": content,
                "thumb_media_id": thumb_media_id,
                "need_open_comment": 1 if open_comment else 0,
                "only_fans_can_comment": 0
            }
        ]
    }
    headers = {"Content-Type": "application/json; charset=utf-8"}
    resp = requests.post(url, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), headers=headers, timeout=30)
    data = resp.json()
    if "media_id" in data:
        return data["media_id"]
    else:
        raise Exception(f"提交微信草稿箱失败: {json.dumps(data, ensure_ascii=False)}")

def update_draft(access_token, media_id, title, author, digest, content, thumb_media_id, open_comment=1):
    """覆盖更新已有草稿"""
    url = f"https://api.weixin.qq.com/cgi-bin/draft/update?access_token={access_token}"
    if len(digest) > 120:
        digest = digest[:116] + "..."
    payload = {
        "media_id": media_id,
        "index": 0,
        "articles": {
            "title": title[:64],
            "author": author[:8],
            "digest": digest,
            "content": content,
            "thumb_media_id": thumb_media_id,
            "need_open_comment": 1 if open_comment else 0,
            "only_fans_can_comment": 0
        }
    }
    headers = {"Content-Type": "application/json; charset=utf-8"}
    resp = requests.post(url, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), headers=headers, timeout=30)
    data = resp.json()
    if data.get("errcode", 0) == 0:
        return media_id
    else:
        raise Exception(f"更新微信草稿箱失败: {json.dumps(data, ensure_ascii=False)}")

def replace_image_src(content, source, cdn_url):
    pattern = rf'(src=["\']){re.escape(source)}(["\'])'
    return re.sub(pattern, lambda match: f'{match.group(1)}{cdn_url}{match.group(2)}', content)

def ensure_safe_crop_cover(cover_path):
    """微信封面 2.35:1 居中裁切安全防线（智能像素分析与防呆重构）"""
    if not os.path.exists(cover_path):
        return cover_path

    try:
        im = Image.open(cover_path).convert('RGB')
        w, h = im.size
        
        crop_h = int(w / 2.35)
        crop_y0 = (h - crop_h) // 2
        crop_y1 = crop_y0 + crop_h

        bg_color = im.getpixel((5, 5))
        
        diff_threshold = 20
        non_bg_coords = []
        for y in range(h):
            for x in range(0, w, 4):
                px = im.getpixel((x, y))
                diff = sum(abs(px[i] - bg_color[i]) for i in range(3))
                if diff > diff_threshold:
                    non_bg_coords.append((x, y))
                    break

        if not non_bg_coords:
            return cover_path

        ys = [c[1] for c in non_bg_coords]
        y_min, y_max = min(ys), max(ys)
        
        min_top_margin = int(crop_h * 0.15)
        min_bottom_margin = int(crop_h * 0.12)
        safe_top = crop_y0 + min_top_margin
        safe_bottom = crop_y1 - min_bottom_margin

        if y_min < safe_top or y_max > safe_bottom:
            print(f"⚠️ 封面安全视窗预警: 内容范围 y=[{y_min}, {y_max}]，微信 2.35:1 裁切线位于 y=[{crop_y0}, {crop_y1}]")
            print(f"   -> 正在自动重构居中安全视窗（防切字防呆自动处理）...")
            
            all_xs = []
            for y in range(y_min, y_max + 1):
                for x in range(0, w, 2):
                    px = im.getpixel((x, y))
                    if sum(abs(px[i] - bg_color[i]) for i in range(3)) > diff_threshold:
                        all_xs.append(x)
            
            x_min = min(all_xs) if all_xs else 0
            x_max = max(all_xs) if all_xs else w

            content = im.crop((x_min, y_min, x_max, y_max))
            safe_h = crop_h - min_top_margin - min_bottom_margin
            scale = min(safe_h / (y_max - y_min), (w - 60) / (x_max - x_min), 1.0)
            new_w = int((x_max - x_min) * scale)
            new_h = int((y_max - y_min) * scale)
            content_resized = content.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            new_img = Image.new('RGB', (w, h), bg_color)
            paste_x = (w - new_w) // 2
            paste_y = crop_y0 + min_top_margin + (safe_h - new_h) // 2
            new_img.paste(content_resized, (paste_x, paste_y))
            
            safe_cover_path = os.path.splitext(cover_path)[0] + "_safe_crop.jpg"
            new_img.save(safe_cover_path, quality=95)
            print(f"✓ 已生成防切字安全封面: {os.path.basename(safe_cover_path)} (大标题与主体已锁定于 2.35:1 居中安全视窗)")
            return safe_cover_path
    except Exception as e:
        print(f"安全视窗检测略过: {e}")
        
    return cover_path

def main():
    parser = argparse.ArgumentParser(description="一键上传文章及素材至微信公众号草稿箱")
    parser.add_argument("--html", required=True, help="排版好的正文 HTML 文件路径")
    parser.add_argument("--images-dir", help="图片存储目录（可选）")
    parser.add_argument("--cover", help="封面图文件路径（默认使用找到的第一张图片）")
    parser.add_argument("--title", help="文章标题（默认从 HTML 提取）")
    parser.add_argument("--author", default=DEFAULT_AUTHOR, help="文章作者")
    parser.add_argument("--digest", help="文章摘要（不超过 120 字）")
    parser.add_argument("--update-draft", help="指定要覆盖更新的已有草稿 media_id（避免草稿重复并防止格式劣化）")
    parser.add_argument("--reuse-thumb", help="复用已有封面素材 thumb_media_id（无需重复上传封面图片）")
    parser.add_argument("--appid", default=DEFAULT_APPID, help="微信公众号 AppID")
    parser.add_argument("--appsecret", default=DEFAULT_APPSECRET, help="微信公众号 AppSecret")
    args = parser.parse_args()

    html_path = os.path.abspath(args.html)
    if not os.path.exists(html_path):
        print(f"错误: HTML 文件不存在: {html_path}", file=sys.stderr)
        sys.exit(1)

    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    print("1. 正在获取 Access Token...")
    token = get_access_token(args.appid, args.appsecret)
    print("✓ Access Token 获取成功!")

    # 提取所有本地图片路径
    img_src_list = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', content)
    local_images = []
    source_by_path = {}
    for src in img_src_list:
        if not src.startswith("http://") and not src.startswith("https://"):
            full_path = os.path.abspath(src) if not args.images_dir else (src if os.path.isabs(src) else os.path.join(args.images_dir, os.path.basename(src)))
            source_by_path.setdefault(full_path, []).append(src)
            if os.path.exists(full_path) and full_path not in local_images:
                local_images.append(full_path)

    # 确定封面图或复用已有封面
    if args.reuse_thumb:
        thumb_media_id = args.reuse_thumb
        print(f"2. 复用已有封面素材 thumb_media_id: {thumb_media_id}")
    else:
        cover_path = args.cover
        if not cover_path and local_images:
            cover_path = local_images[0]

        if not cover_path or not os.path.exists(cover_path):
            print("错误: 未找到可用的封面图片", file=sys.stderr)
            sys.exit(1)

        cover_path = ensure_safe_crop_cover(cover_path)
        print(f"2. 正在上传封面素材: {os.path.basename(cover_path)} ...")
        thumb_media_id = upload_thumb_material(token, cover_path)
        print(f"✓ 封面图上传成功! thumb_media_id: {thumb_media_id}")

    print("3. 正在上传正文插图至微信 CDN 并替换 HTML...")
    for img_path in local_images:
        print(f"   -> 上传插图: {os.path.basename(img_path)} ...")
        cdn_url = upload_news_img(token, img_path).replace("http://", "https://", 1)
        print(f"      微信 CDN URL: {cdn_url}")
        for source in source_by_path.get(img_path, []):
            content = replace_image_src(content, source, cdn_url)

    title = args.title or "微信公众号精选推文"
    digest = args.digest or "点击查看精彩深度推文与系统性实操拆解。"

    if args.update_draft:
        print(f"4. 正在更新已有草稿 (Media ID: {args.update_draft})...")
        draft_media_id = update_draft(token, args.update_draft, title, args.author, digest, content, thumb_media_id)
        print("\n" + "="*50)
        print("🎉 恭喜！图文已成功更新至微信公众号草稿箱！")
        print(f"文章标题: {title}")
        print(f"Draft Media ID: {draft_media_id}")
        print("="*50 + "\n")
    else:
        print("4. 正在提交图文到微信公众号草稿箱...")
        draft_media_id = add_draft(token, title, args.author, digest, content, thumb_media_id)
        print("\n" + "="*50)
        print("🎉 恭喜！图文已成功推送至微信公众号草稿箱！")
        print(f"文章标题: {title}")
        print(f"Draft Media ID: {draft_media_id}")
        print("="*50 + "\n")

if __name__ == "__main__":
    main()
