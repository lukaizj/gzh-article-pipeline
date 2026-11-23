# -*- coding: utf-8 -*-
"""
WeChat Little Green Book / Image Post (小绿书 type=8 / article_type="newspic") Engine
固化防踩坑能力：
1. 强制标题 <= 20 字硬门槛（防微信列表直接截断成……）；
2. 提供 --safe-cover-src 封装：自动把核心方图/海报严格收束进微信实测双重居中裁切安全区（300x360 inside 765x1024），外围生成纯净连贯星空暗底（零重影、零边框），并输出 *_home_sim.jpg 供人眼预检；
3. 上传永久图片素材并提交 article_type="newspic" 草稿（支持 --update-draft 覆盖）；
4. 推送后自动调 draft/get 回拉微信真实生成的 thumb_url，按 203x270 实际展示比例裁出对比图供 read_file 最终验收！
"""

import argparse
import io
import json
import os
import random
import sys
import requests
from PIL import Image, ImageDraw, ImageFilter

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)
import upload_to_wechat as uw


def build_safe_newspic_cover(src_path: str, dst_path: str, sim_path: str = "", seed: int = 42) -> str:
    """将核心 1:1/4:5 主视觉安全嵌入 765x1024 正中心双重裁切安全区内，外围铺纯净星空暗场。"""
    im = Image.open(src_path).convert("RGB")
    sw, sh = im.size
    # 若原图明显偏竖（如 3:4），先居中取 1:1 方框核心或保持清晰高宽比收束；若用户已手工切好，保留其长宽比缩放
    W, H = 765, 1024

    # 洁净深空暗场底（严禁使用原图整体高斯模糊，防止出现重影文字！）
    r_avg, g_avg, b_avg = im.getpixel((min(sw - 1, 8), min(sh - 1, 8)))
    # 保底限制在极暗色调范围，避免亮色外框刺眼
    bg_rgb = (min(18, max(4, r_avg // 2)), min(22, max(8, g_avg // 2)), min(28, max(12, b_avg // 2)))
    canvas = Image.new("RGB", (W, H), bg_rgb)

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((W // 2 - 220, H // 2 - 140, W // 2 + 220, H // 2 + 240), fill=(18, 62, 74, 85))
    gd.ellipse((W // 2 - 170, H // 2 - 190, W // 2 + 170, H // 2 + 20), fill=(85, 65, 25, 55))
    glow = glow.filter(ImageFilter.GaussianBlur(70))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), glow).convert("RGB")

    rng = random.Random(seed)
    pix = canvas.load()
    for _ in range(260):
        sx = rng.randint(4, W - 5)
        sy = rng.randint(4, H - 5)
        b = rng.randint(55, 180)
        pix[sx, sy] = (
            min(255, pix[sx, sy][0] + b),
            min(255, pix[sx, sy][1] + b),
            min(255, pix[sx, sy][2] + int(b * 1.1)),
        )

    # 严格落入实测 324x431 安全窗口（宽 <= 300, 高 <= 360）
    tw = 300
    th = int(round(tw * sh / sw))
    if th > 365:
        th = 365
        tw = int(round(th * sw / sh))
    hero = im.resize((tw, th), Image.Resampling.LANCZOS)

    x0 = (W - tw) // 2
    y0 = (H - th) // 2

    mask = Image.new("L", (tw, th), 255)
    md = mask.load()
    fx, fy = max(12, tw // 9), max(12, th // 9)
    for y in range(th):
        for x in range(tw):
            dx = min(x, tw - 1 - x) / float(fx)
            dy = min(y, th - 1 - y) / float(fy)
            d = min(1.0, min(dx, dy))
            t = d * d * (3 - 2 * d)
            md[x, y] = int(255 * t)

    canvas.paste(hero, (x0, y0), mask)
    os.makedirs(os.path.dirname(os.path.abspath(dst_path)), exist_ok=True)
    canvas.save(dst_path, quality=95)

    if sim_path:
        y16_0, y16_1 = int(H * 0.2899), int(H * 0.7101)
        s16 = canvas.crop((0, y16_0, W, y16_1))
        cw = int(round(s16.height * (203 / 270)))
        cx0 = (W - cw) // 2
        sim = s16.crop((cx0, 0, cx0 + cw, s16.height))
        sim.save(sim_path, quality=95)
    return dst_path


def upload_permanent_image(token: str, file_path: str) -> str:
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    with open(file_path, "rb") as f:
        resp = requests.post(url, files={"media": (os.path.basename(file_path), f, "image/jpeg")}, timeout=30)
    data = resp.json()
    if "media_id" not in data:
        raise RuntimeError(f"上传图片素材失败 ({file_path}): {data}")
    return data["media_id"]


def main() -> None:
    parser = argparse.ArgumentParser(description="微信公众号小绿书 (type=8 / newspic) 安全封壳与直推工具")
    parser.add_argument("--images", nargs="+", help="按顺序传入贴图图片路径（首张为封面图）")
    parser.add_argument("--title", default="", help="贴图标题（严格 <= 20 字符）")
    parser.add_argument("--content", default="", help="贴图短文案正文（纯文本）")
    parser.add_argument("--content-file", default="", help="可选，从本地 txt/md 读取正文")
    parser.add_argument("--update-draft", default="", help="可选，覆盖更新已有 newspic 草稿 media_id")
    parser.add_argument("--verify-out", default="", help="可选，下载线上 thumb_url 并按 203x270 裁出真实卡片校验图")
    parser.add_argument("--safe-cover-src", default="", help="仅生成防裁切安全封面模式：输入中心主体图路径，输出至 --safe-cover-dst 后退出或继续上传")
    parser.add_argument("--safe-cover-dst", default="", help="搭配 --safe-cover-src 指定输出安全封面路径")
    parser.add_argument("--sim-out", default="", help="搭配 --safe-cover-src 输出 203x270 模拟卡片预检图路径")
    parser.add_argument("--appid", default=uw.DEFAULT_APPID)
    parser.add_argument("--appsecret", default=uw.DEFAULT_APPSECRET)
    args = parser.parse_args()

    if args.safe_cover_src:
        dst = args.safe_cover_dst or os.path.splitext(args.safe_cover_src)[0] + "_safe.jpg"
        sim = args.sim_out or os.path.splitext(dst)[0] + "_home_sim.jpg"
        build_safe_newspic_cover(args.safe_cover_src, dst, sim_path=sim)
        print(f"✓ 已生成小绿书安全防裁切封面: {dst}")
        print(f"✓ 已生成 203x270 首页卡片预检图: {sim}（请务必用 read_file 检视确认无切字！）")
        if not args.images:
            return

    if not args.images:
        parser.error("必须提供 --images 或使用 --safe-cover-src。")
    if not args.title:
        parser.error("必须提供 --title。")
    if len(args.title) > 20:
        print(f"❌ 触发小绿书物理红线: 标题共 {len(args.title)} 字，超过 20 字上限会被微信截断成『……』！", file=sys.stderr)
        sys.exit(1)

    content = args.content
    if args.content_file:
        with open(args.content_file, "r", encoding="utf-8") as f:
            content = f.read().strip()

    token = uw.get_access_token(args.appid, args.appsecret)
    image_list = []
    for p in args.images:
        mid = upload_permanent_image(token, p)
        print(f"✓ 上传 {os.path.basename(p)} -> {mid}")
        image_list.append({"image_media_id": mid})

    article_obj = {
        "article_type": "newspic",
        "title": args.title,
        "content": content,
        "need_open_comment": 1,
        "only_fans_can_comment": 0,
        "image_info": {"image_list": image_list},
    }

    draft_id = args.update_draft
    if draft_id:
        upd = requests.post(
            f"https://api.weixin.qq.com/cgi-bin/draft/update?access_token={token}",
            data=json.dumps({"media_id": draft_id, "index": 0, "articles": article_obj}, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=30,
        )
        upd.encoding = "utf-8"
        ures = upd.json()
        if ures.get("errcode", 0) != 0:
            raise RuntimeError(f"更新小绿书草稿失败: {ures}")
        print(f"✓ 已覆写小绿书草稿: {draft_id}")
    else:
        add = requests.post(
            f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}",
            data=json.dumps({"articles": [article_obj]}, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=30,
        )
        add.encoding = "utf-8"
        ares = add.json()
        if "media_id" not in ares:
            raise RuntimeError(f"新建小绿书草稿失败: {ares}")
        draft_id = ares["media_id"]
        print(f"✓ 已推送小绿书草稿: {draft_id}")

    get_resp = requests.post(
        f"https://api.weixin.qq.com/cgi-bin/draft/get?access_token={token}",
        json={"media_id": draft_id},
        timeout=15,
    )
    get_resp.encoding = "utf-8"
    item = get_resp.json()["news_item"][0]
    print(f"VERIFIED type={item.get('article_type')} | title={item.get('title')} ({len(item.get('title', ''))}字) | images={len(item.get('image_info', {}).get('image_list', []))}")

    if args.verify_out and item.get("thumb_url"):
        tu = item["thumb_url"]
        im = Image.open(io.BytesIO(requests.get(tu, timeout=15).content))
        w, h = im.size
        cw = int(round(h * (203 / 270)))
        cx0 = max(0, (w - cw) // 2)
        card = im.crop((cx0, 0, min(w, cx0 + cw), h))
        card.save(args.verify_out, quality=95)
        print(f"✓ 已抓取线上真实 thumb_url ({im.size}) 并裁出 203x270 核验图: {args.verify_out}")


if __name__ == "__main__":
    main()
