# -*- coding: utf-8 -*-
"""
微信公众号草稿箱一键上传与图片自动转存脚本
- 自动获取 Access Token
- 自动将 HTML 中所有引用的本地插图上传至微信官方 CDN (media/uploadimg)
- 自动上传封面图片至微信永久素材 (material/add_material)
- 自动提交图文至微信草稿箱 (draft/add)
"""

import os
import re
import sys
import json
import argparse
import requests

def load_default_config():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "..", "references", "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def get_access_token(appid, appsecret):
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={appsecret}"
    resp = requests.get(url, timeout=15)
    data = resp.json()
    if "access_token" in data:
        return data["access_token"]
    else:
        raise Exception(f"获取微信 Access Token 失败: {json.dumps(data, ensure_ascii=False)}")

def upload_news_img(access_token, file_path):
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
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
    with open(file_path, "rb") as f:
        files = {"media": f}
        resp = requests.post(url, files=files, timeout=30)
    data = resp.json()
    if "media_id" in data:
        return data["media_id"]
    else:
        raise Exception(f"上传封面图素材失败 ({file_path}): {json.dumps(data, ensure_ascii=False)}")

def add_draft(access_token, title, author, digest, content, thumb_media_id):
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
    
    # 微信公众号 digest 限制约 120 字
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
                "need_open_comment": 1,
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

def main():
    cfg = load_default_config()
    default_appid = os.environ.get("WECHAT_APPID", cfg.get("appid", ""))
    default_appsecret = os.environ.get("WECHAT_APPSECRET", cfg.get("appsecret", ""))
    default_author = cfg.get("default_author", "AI 架构实战")

    parser = argparse.ArgumentParser(description="一键上传文章及素材至微信公众号草稿箱")
    parser.add_argument("--html", required=True, help="排版好的正文 HTML 文件路径")
    parser.add_argument("--images-dir", help="图片存储目录（可选）")
    parser.add_argument("--cover", help="封面图文件路径（默认使用正文找到的第一张图片）")
    parser.add_argument("--title", help="文章标题")
    parser.add_argument("--author", default=default_author, help="文章作者")
    parser.add_argument("--digest", help="文章摘要（不超过 120 字）")
    parser.add_argument("--appid", default=default_appid, help="微信公众号 AppID")
    parser.add_argument("--appsecret", default=default_appsecret, help="微信公众号 AppSecret")
    args = parser.parse_args()

    if not args.appid or not args.appsecret:
        print("错误: 缺少微信 AppID 或 AppSecret。可通过命令行参数 --appid/--appsecret、环境变量 WECHAT_APPID/WECHAT_APPSECRET 或 references/config.json 提供。", file=sys.stderr)
        sys.exit(1)

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
    img_src_list = re.findall(r'<img[^>]+src=["']([^"']+)["']', content)
    local_images = []
    for src in img_src_list:
        if not src.startswith("http://") and not src.startswith("https://"):
            full_path = os.path.abspath(src) if not args.images_dir else (src if os.path.isabs(src) else os.path.join(args.images_dir, os.path.basename(src)))
            if os.path.exists(full_path) and full_path not in local_images:
                local_images.append(full_path)

    # 确定封面图
    cover_path = args.cover
    if not cover_path and local_images:
        cover_path = local_images[0]

    if not cover_path or not os.path.exists(cover_path):
        print("错误: 未找到可用的封面图片", file=sys.stderr)
        sys.exit(1)

    print(f"2. 正在上传封面素材: {os.path.basename(cover_path)} ...")
    thumb_media_id = upload_thumb_material(token, cover_path)
    print(f"✓ 封面图上传成功! thumb_media_id: {thumb_media_id}")

    print("3. 正在上传正文插图至微信 CDN 并替换 HTML...")
    for img_path in local_images:
        print(f"   -> 上传插图: {os.path.basename(img_path)} ...")
        cdn_url = upload_news_img(token, img_path)
        print(f"      微信 CDN URL: {cdn_url}")
        content = content.replace(img_path, cdn_url)
        content = content.replace(os.path.basename(img_path), cdn_url)

    # 提取/设置标题与摘要
    title = args.title or "微信公众号精选推文"
    digest = args.digest or "点击查看精彩技术推文与系统性架构拆解。"

    print("4. 正在提交图文到微信公众号草稿箱...")
    draft_media_id = add_draft(token, title, args.author, digest, content, thumb_media_id)
    
    print("\n" + "="*50)
    print("🎉 恭喜！图文已成功推送至微信公众号草稿箱！")
    print(f"文章标题: {title}")
    print(f"Draft Media ID: {draft_media_id}")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
