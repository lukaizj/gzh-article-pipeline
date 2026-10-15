# -*- coding: utf-8 -*-
"""
Gemini Web Pro 自动化桥接器 (通过 macOS 原生 AppleScript 控制 Chrome 中的 Gemini Pro 会话)
100% 复用用户已登录的 Google One AI Premium (Gemini Advanced / Pro) 权益，无惧 429 API 配额限制。
"""

import os
import sys
import time
import json
import base64
import subprocess
import requests

def find_gemini_tab():
    """在当前运行的所有 Chrome 窗口中查找已打开的 Gemini 标签页，返回 (window_id, tab_idx)"""
    script = """
    tell application "Google Chrome"
        repeat with w in windows
            set t_idx to 1
            repeat with t in tabs of w
                if URL of t contains "gemini.google.com" or title of t contains "Gemini" then
                    return (id of w as string) & "," & (t_idx as string)
                end if
                set t_idx to t_idx + 1
            end repeat
        end repeat
        return "NOT_FOUND"
    end tell
    """
    try:
        res = subprocess.check_output(["osascript", "-e", script]).decode("utf-8").strip()
    except Exception as e:
        raise Exception(f"无法与 Google Chrome 通信: {e}")

    if res != "NOT_FOUND":
        w, t = res.split(",")
        return int(w), int(t)

    # 如果没打开，自动在当前窗口打开一个新标签
    open_script = """
    tell application "Google Chrome"
        if (count of windows) is 0 then
            make new window
        end if
        tell front window
            set newTab to make new tab with properties {URL:"https://gemini.google.com/app"}
            return (id as string) & "," & (count of tabs as string)
        end tell
    end tell
    """
    res = subprocess.check_output(["osascript", "-e", open_script]).decode("utf-8").strip()
    time.sleep(3) # 等待加载
    w, t = res.split(",")
    return int(w), int(t)

def execute_js(win_id, tab_idx, js_code):
    """通过 UTF-8 TextDecoder + Base64 在指定标签页中安全执行 JavaScript"""
    b64 = base64.b64encode(js_code.encode("utf-8")).decode("ascii")
    runner = f"""
    tell application "Google Chrome"
        try
            set targetWin to (first window whose id is {win_id})
            set jsStr to "eval(new TextDecoder().decode(Uint8Array.from(atob('{b64}'), c => c.charCodeAt(0))))"
            set res to execute tab {tab_idx} of targetWin javascript jsStr
            return "SUCCESS:::" & (res as string)
        on error errMsg
            return "ERROR:::" & errMsg
        end try
    end tell
    """
    out = subprocess.check_output(["osascript", "-e", runner]).decode("utf-8").strip()
    if out.startswith("SUCCESS:::"):
        return True, out[len("SUCCESS:::"):].strip()
    else:
        return False, out[len("ERROR:::"):].strip()

def generate_image_via_gemini_web(prompt, output_file_path, timeout=120):
    """
    通过网页版已登录的 Gemini Pro 自动发词并捕获生成的图片
    """
    win_idx, tab_idx = find_gemini_tab()
    if not win_idx:
        raise Exception("未能在 Chrome 中找到或启动 Gemini 网页端。")

    print(f"1. 正在连接 Chrome [窗口 {win_idx}, 标签 {tab_idx}] (Gemini Web Pro)...")
    # 自动导航至纯净新对话，彻底隔离历史残留图片
    nav_script = f'''
    tell application "Google Chrome"
        set w to (first window whose id is {win_idx})
        set URL of tab {tab_idx} of w to "https://gemini.google.com/app"
    end tell
    '''
    subprocess.run(["osascript", "-e", nav_script], check=True)
    time.sleep(3.5)

    # 1. 记录现有图片列表（用于识别新生成的图片）
    get_existing_js = """
    (function() {
        return JSON.stringify(Array.from(document.querySelectorAll('img')).map(img => img.src));
    })()
    """
    ok, existing_json = execute_js(win_idx, tab_idx, get_existing_js)
    existing_srcs = set(json.loads(existing_json) if ok and existing_json else [])

    # 2. 注入提示词（必须去除换行符，因为 Chromium execCommand insertText 会在第一个换行符截断）
    print(f"2. 正在自动输入生图提示词...")
    prompt_clean = " ".join(line.strip() for line in prompt.strip().splitlines() if line.strip())
    b64_prompt = base64.b64encode(prompt_clean.encode("utf-8")).decode("ascii")
    insert_js = f"""
    (function() {{
        const editor = document.querySelector('rich-textarea div.ql-editor');
        if (!editor) return 'NO_EDITOR';
        
        editor.focus();
        const range = document.createRange();
        range.selectNodeContents(editor);
        const sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
        
        document.execCommand('selectAll', false, null);
        document.execCommand('delete', false, null);
        
        const text = new TextDecoder().decode(Uint8Array.from(atob('{b64_prompt}'), c => c.charCodeAt(0)));
        const ok = document.execCommand('insertText', false, text);
        editor.dispatchEvent(new Event('input', {{ bubbles: true }}));
        
        const curLen = editor.innerText.trim().length;
        if (curLen < text.length * 0.7) {{
            return 'INSERT_FAILED_TRUNCATED:' + curLen + '_EXPECTED_' + text.length;
        }}
        return 'INSERTED:' + curLen;
    }})()
    """
    ok, res = execute_js(win_idx, tab_idx, insert_js)
    if not ok or not res.startswith("INSERTED"):
        raise Exception(f"在 Gemini 网页端注入提示词失败: {res}")
    print(f"   -> 成功注入提示词字符数: {res.split(':')[1]} (原提示词长度: {len(prompt_clean)})")

    # 3. 等待并点击发送按钮
    print(f"3. 正在等待发送按钮激活并点击...")
    submitted = False
    for _ in range(12): # 最多等待 6 秒
        time.sleep(0.5)
        click_send_js = """
        (function() {
            const sendBtn = document.querySelector('button[aria-label="发送"], button[aria-label*="发送"], button.send-button');
            if (!sendBtn) return 'NO_SEND_BTN';
            if (sendBtn.disabled || sendBtn.getAttribute('aria-disabled') === 'true') return 'SEND_BTN_DISABLED';
            sendBtn.click();
            return 'CLICKED';
        })()
        """
        ok, res = execute_js(win_idx, tab_idx, click_send_js)
        if ok and res == "CLICKED":
            submitted = True
            break
        elif ok and res == "SEND_BTN_DISABLED":
            # 尝试再次触发 input 事件
            execute_js(win_idx, tab_idx, "document.querySelector('rich-textarea div.ql-editor')?.dispatchEvent(new Event('input', { bubbles: true }))")

    if not submitted:
        raise Exception(f"点击发送按钮失败: 未能激活或找到发送按钮 ({res})")

    print("✓ 提示词已成功提交！Gemini Pro 正在实时生成画面，等待结果返回...")

    # 4. 轮询检测新生成的图片
    start_time = time.time()
    target_img_b64 = None

    while time.time() - start_time < timeout:
        time.sleep(3)
        check_js = f"""
        (function() {{
            const existing = new Set({json.dumps(list(existing_srcs))});
            const allImgs = Array.from(document.querySelectorAll('img'));
            
            // 筛选新增的大图（排除头像、图标）
            const newImgs = allImgs.filter(img => {{
                if (existing.has(img.src)) return false;
                if (!img.src || img.src.length < 10) return false;
                if (img.src.includes('avatar') || img.src.includes('googleusercontent.com/a/')) return false;
                const w = img.naturalWidth || img.width;
                const h = img.naturalHeight || img.height;
                return (w > 300 || h > 300);
            }});
            
            if (newImgs.length === 0) return 'WAITING';
            const img = newImgs[newImgs.length - 1];
            if (!img.complete || img.naturalWidth < 100) return 'LOADING';
            
            try {{
                const canvas = document.createElement('canvas');
                canvas.width = img.naturalWidth || img.width;
                canvas.height = img.naturalHeight || img.height;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0);
                return canvas.toDataURL('image/jpeg', 0.95);
            }} catch(e) {{
                return 'CANVAS_ERR:' + e.message;
            }}
        }})()
        """
        ok, res = execute_js(win_idx, tab_idx, check_js)
        if ok and res.startswith("data:image/"):
            target_img_b64 = res.split(",", 1)[1]
            break
        elif ok and res != "WAITING" and res != "LOADING":
            print(f"   [状态: {res}]")

    if not target_img_b64:
        raise Exception("超时未捕获到新生成的图片，请检查网页端是否遇到报错或排队。")

    print(f"3. 成功捕获到高清图片，正在保存原图文件...")

    # 5. 保存为本地图片文件
    os.makedirs(os.path.dirname(os.path.abspath(output_file_path)), exist_ok=True)
    with open(output_file_path, "wb") as f:
        f.write(base64.b64decode(target_img_b64))

    print(f"🎉 成功保存高清图片至: {output_file_path} (大小: {os.path.getsize(output_file_path)} 字节)")
    return output_file_path

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Gemini Web Pro 自动化生图降级桥接器")
    parser.add_argument("--prompt", type=str, help="生图提示词")
    parser.add_argument("--output", type=str, help="图片保存绝对路径 (e.g. /path/to/image.jpg)")
    parser.add_argument("--timeout", type=int, default=120, help="轮询超时时间(秒)，默认 120 秒")
    args = parser.parse_args()

    if args.prompt and args.output:
        generate_image_via_gemini_web(args.prompt, args.output, timeout=args.timeout)
    else:
        w, t = find_gemini_tab()
        ok, res = execute_js(w, t, "document.title")
        print(f"Gemini Web Bridge 就绪! [窗口 {w}, 标签 {t}]: {res}")
        print("用法: python3 gemini_web_bridge.py --prompt \"...\" --output \"/path/to/image.jpg\"")
