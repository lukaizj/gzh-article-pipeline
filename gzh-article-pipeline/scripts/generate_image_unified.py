# -*- coding: utf-8 -*-
"""
Unified Image Generator with Zero-Interruption Automatic Fallback
(全自动双引擎生图调度器：API 优先，遇 429 额度耗尽自动无感无缝降级至 Chrome 网页版 Gemini Pro)
"""

import os
import sys
import argparse
import subprocess

def generate_image_auto(prompt, output_path, aspect_ratio="16:9", force_web=False):
    """
    双引擎自动容灾生图逻辑：
    1. 若未指定 force_web，先尝试调用已配置的 API
    2. 若触发 429 Resource Exhausted / 额度耗尽，或 force_web 为 True，
       立即零延迟自动切换至 gemini_web_bridge.py
    """
    output_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(output_dir, exist_ok=True)

    if not force_web:
        # 尝试通过环境变量检测并调用 google-genai
        try:
            from google import genai
            from google.genai import types

            api_key = os.environ.get("GEMINI_API_KEY")
            if api_key:
                print("1. [API 模式] 正在通过 Gemini API 发起生图请求...")
                client = genai.Client(api_key=api_key)
                result = client.models.generate_images(
                    model="imagen-3.0-generate-002",
                    prompt=prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        aspect_ratio=aspect_ratio,
                    )
                )
                for generated_image in result.generated_images:
                    with open(output_path, "wb") as f:
                        f.write(generated_image.image.image_bytes)
                print(f"🎉 API 生图成功并已保存: {output_path}")
                return output_path
        except Exception as e:
            err_str = str(e)
            print(f"⚠️ [API 阻断] API 请求触发异常或配额耗尽: {err_str}")
            print("🚀 [自动降级容灾] 触发无感保底策略，正在自动切换至已登录的 Gemini Web Pro 浏览器会话...")

    # 自动降级执行 Gemini Web Bridge
    script_dir = os.path.dirname(os.path.abspath(__file__))
    bridge_path = os.path.join(script_dir, "gemini_web_bridge.py")

    from gemini_web_bridge import generate_image_via_gemini_web
    print(f"2. [Web 桥接模式] 启动 Chrome Gemini Pro 会话自动打词生图...")
    return generate_image_via_gemini_web(prompt, output_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="双引擎无感自动降级生图调度器")
    parser.add_argument("--prompt", type=str, required=True, help="生图提示词")
    parser.add_argument("--output", type=str, required=True, help="输出文件绝对路径")
    parser.add_argument("--aspect-ratio", type=str, default="16:9", help="图片比例，默认 16:9")
    parser.add_argument("--force-web", action="store_true", help="强制直接走网页版 Gemini Pro 降级通道")
    args = parser.parse_args()

    generate_image_auto(args.prompt, args.output, aspect_ratio=args.aspect_ratio, force_web=args.force_web)
