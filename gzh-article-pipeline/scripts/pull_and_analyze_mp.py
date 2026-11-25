# -*- coding: utf-8 -*-
"""
微信公众号发表数据与公私域渠道诊断脚本 (WeChat MP Traffic & Channel Breakdown Analyzer)
自动连接 Chrome 中的微信公众平台后台，一键全量拉取：
1. 账号实时总盘：粉丝总数、今日净增、近30天总UV及全盘渠道分布（推荐/消息/会话等）
2. 单篇发表数据明细：每篇文章的公域推荐流、常读粉丝消息、群会话转发、主页点击等真实 UV
3. 爆款与低阅分层对决矩阵：科学归因为什么低阅卡在 100 阅（推荐熔断），为什么爆款能破万（90%+推荐）
4. 诊断建议与避坑指标：分享率阈值、痛点公约数检验
"""

import subprocess
import json
import base64
import html
import time
import os
import sys
import argparse
import statistics
from datetime import datetime, timedelta

SCENES_MAP = {
    "0": "公众号消息(常读粉丝)",
    "1": "聊天会话(群/私聊转发)",
    "2": "朋友圈",
    "4": "公众号主页",
    "5": "其它",
    "6": "推荐(公域看一看/算法流)",
    "7": "搜一搜"
}

def run_chrome_js(js_code):
    b64_js = base64.b64encode(js_code.encode("utf-8")).decode("ascii")
    as_script = f'''
    tell application "Google Chrome"
        repeat with aWindow in every window
            repeat with aTab in every tab of aWindow
                if (URL of aTab) contains "mp.weixin.qq.com" then
                    return execute aTab javascript "eval(new TextDecoder().decode(Uint8Array.from(atob('{b64_js}'), c => c.charCodeAt(0))))"
                end if
            end repeat
        end repeat
        return "NO_TAB"
    end tell
    '''
    res = subprocess.run(["osascript", "-e", as_script], capture_output=True, text=True)
    out = res.stdout.strip()
    if not out or out == "NO_TAB" or out == "missing value":
        return None
    return out

def get_account_overview():
    """获取账号粉丝数、昨日关键指标与30天宏观大盘概览"""
    js = """
    (() => {
        try {
            const token = new URL(location.href).searchParams.get("token");
            if (!token) return JSON.stringify({ error: "no_token" });
            
            // 1. Get stats from Home DOM
            const bodyText = document.body ? document.body.innerText : "";
            const fansMatch = bodyText.match(/总用户数\\s*\\n\\s*([0-9,]+)/);
            const readMatch = bodyText.match(/昨日阅读\\(人\\)\\s*\\n\\s*([0-9,]+)/);
            const shareMatch = bodyText.match(/昨日分享\\(人\\)\\s*\\n\\s*([0-9,]+)/);
            const followMatch = bodyText.match(/昨日新增关注\\(人\\)\\s*\\n\\s*([0-9,]+)/);
            const weeklyMatch = bodyText.match(/推荐带来([0-9\\.]+万)阅读量/);

            const homeStats = {
                cumulate_user: fansMatch ? fansMatch[1] : null,
                yesterday_read: readMatch ? readMatch[1] : null,
                yesterday_share: shareMatch ? shareMatch[1] : null,
                yesterday_follow: followMatch ? followMatch[1] : null,
                weekly_rec: weeklyMatch ? weeklyMatch[1] : null
            };
            
            // 2. Get 30-day macro total from appmsganalysis
            let read30d = 0;
            let read7d = 0;
            try {
                const aXhr = new XMLHttpRequest();
                aXhr.open("GET", "/misc/appmsganalysis?action=report&type=daily_v2&token=" + token + "&lang=zh_CN", false);
                aXhr.send();
                const aText = aXhr.responseText;
                const mMatch = aText.match(/wx\\.cgiData\\s*=\\s*(\\{.*?\\n\\s*\\});/s);
                if (mMatch) {
                    const fn = new Function("let o = " + mMatch[1] + "; return o;");
                    const cgi = fn();
                    const sumList = cgi.read_summary || [];
                    for (let s of sumList) {
                        if (s.data_range_type === 2) read7d = s.data_value;
                        if (s.data_range_type === 3) read30d = s.data_value;
                    }
                }
            } catch(e) {}
            
            return JSON.stringify({
                homeStats,
                read7d,
                read30d
            });
        } catch(err) {
            return JSON.stringify({ error: err.message });
        }
    })()
    """
    out = run_chrome_js(js)
    if not out:
        return {}
    try:
        return json.loads(out)
    except:
        return {}


def get_publisher_revenue(days=7):
    """拉取最近 N 天流量主每日曝光、点击、收入(元)与 eCPM"""
    end_d = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    start_d = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    js = f"""
    (() => {{
        try {{
            const token = new URL(location.href).searchParams.get("token");
            if (!token) return JSON.stringify([]);
            const xhr = new XMLHttpRequest();
            const url = "/promotion/publisher/publisher_stat?action=stat&page=1&page_size=100&start_date={start_d}&end_date={end_d}&slot=1&token=" + token + "&appid=&spid=&_=" + Date.now();
            xhr.open("GET", url, false);
            xhr.send(null);
            const data = JSON.parse(xhr.responseText);
            const rows = (data.cost_list && data.cost_list.cost) || [];
            const byDate = {{}};
            for (const r of rows) {{
                const d = r.start_time;
                if (!d) continue;
                if (!byDate[d]) byDate[d] = {{ date: d, views: 0, clicks: 0, cost_fen: 0 }};
                byDate[d].views += (r.view_count || 0);
                byDate[d].clicks += (r.click_count || 0);
                byDate[d].cost_fen += (r.cost || 0);
            }}
            const out = Object.values(byDate).sort((a, b) => b.date.localeCompare(a.date)).map(x => ({{
                date: x.date,
                views: x.views,
                clicks: x.clicks,
                income_yuan: Number((x.cost_fen / 100).toFixed(2)),
                ecpm: x.views > 0 ? Number(((x.cost_fen / 100) / x.views * 1000).toFixed(2)) : 0.0
            }}));
            return JSON.stringify(out);
        }} catch(e) {{
            return JSON.stringify([]);
        }}
    }})()
    """
    out = run_chrome_js(js)
    if not out:
        return []
    try:
        return json.loads(out)
    except Exception:
        return []

def get_articles_catalog(max_count=200):
    """获取已发布文章目录"""
    js = f"""
    (() => {{
        const token = new URL(location.href).searchParams.get("token");
        let all = [];
        let begin = 0;
        while (begin < {max_count}) {{
            try {{
                const xhr = new XMLHttpRequest();
                xhr.open("GET", "/cgi-bin/appmsgpublish?sub=list&begin=" + begin + "&count=20&token=" + token + "&lang=zh_CN", false);
                xhr.send();
                const m = xhr.responseText.match(/publish_page\\s*=\\s*(\\{{.*?\\}});/s);
                if (!m) break;
                const page = JSON.parse(m[1]);
                const list = page.publish_list || [];
                if (list.length === 0) break;
                all = all.concat(list);
                begin += 20;
            }} catch(e) {{
                break;
            }}
        }}
        return JSON.stringify(all);
    }})()
    """
    out = run_chrome_js(js)
    if not out:
        return []
    try:
        all_items = json.loads(out)
    except:
        return []
        
    articles = []
    for item in all_items:
        raw = html.unescape(item.get("publish_info", "{}"))
        try:
            p = json.loads(raw)
        except:
            continue
        
        ts = (
            p.get("sent_info", {}).get("time") or
            p.get("line_info", {}).get("send_time") or
            p.get("publish_info", {}).get("create_time") or
            p.get("publish_info", {}).get("update_time") or
            p.get("sent_result", {}).get("update_time")
        )
        for app in p.get("appmsg_info", []):
            t_ts = ts or app.get("line_info", {}).get("send_time")
            dt_str = datetime.fromtimestamp(t_ts).strftime("%Y-%m-%d") if t_ts else "2026-10-15"
            aid = app.get("appmsgid")
            idx = app.get("itemidx")
            articles.append({
                "title": app.get("title", ""),
                "msgid": f"{aid}_{idx}",
                "date": dt_str,
                "read_num": app.get("read_num", 0),
                "share_num": app.get("share_num", 0),
                "like_num": app.get("like_num", 0),
                "old_like_num": app.get("old_like_num", 0)
            })
    return articles

def fetch_details_batch(items):
    """批量从微信后台拉取每篇文章的 cgiData 单篇渠道数据"""
    items_json = json.dumps(items)
    b64_items = base64.b64encode(items_json.encode()).decode()
    
    js = f"""
    (() => {{
        const token = new URL(location.href).searchParams.get("token");
        const items = JSON.parse(new TextDecoder().decode(Uint8Array.from(atob('{b64_items}'), c => c.charCodeAt(0))));
        
        const results = [];
        for (let item of items) {{
            try {{
                const url = "/misc/appmsganalysis?action=detailpage&msgid=" + item.msgid + "&publish_date=" + item.date + "&type=int&pageVersion=1&token=" + token + "&lang=zh_CN";
                const xhr = new XMLHttpRequest();
                xhr.open("GET", url, false);
                xhr.send();
                const html = xhr.responseText;
                
                const marker = "window.wx.cgiData = ";
                const idx = html.lastIndexOf(marker);
                if (idx === -1) {{
                    results.push({{ msgid: item.msgid, error: "no_cgiData" }});
                    continue;
                }}
                
                const sub = html.substring(idx + marker.length);
                const endIdx = sub.indexOf("</script>");
                const jsCode = sub.substring(0, endIdx).trim();
                
                const fn = new Function("let obj = " + jsCode + "; return obj;");
                const data = fn();
                
                const summaryList = data.articleSummaryData?.list || [];
                const dataNew = data.articleData?.article_data_new || {{}};
                
                const sceneReads = {{}};
                for (let r of summaryList) {{
                    if (r.scene === 9999) continue;
                    sceneReads[r.scene] = (sceneReads[r.scene] || 0) + (r.read_user || r.read_count || 0);
                }}
                
                results.push({{
                    title: item.title,
                    msgid: item.msgid,
                    date: item.date,
                    read_num: item.read_num,
                    share_num: item.share_num,
                    like_num: item.like_num,
                    old_like_num: item.old_like_num,
                    read_uv: dataNew.read_uv || 0,
                    share_uv: dataNew.share_uv || 0,
                    like_cnt: dataNew.like_cnt || 0,
                    zaikan_cnt: dataNew.zaikan_cnt || 0,
                    follow_after_read_uv: dataNew.follow_after_read_uv || 0,
                    finished_read_ratio: dataNew.finished_read_pv_ratio || 0,
                    avg_read_time: dataNew.avg_article_read_time || 0,
                    channels: sceneReads
                }});
            }} catch(err) {{
                results.push({{ msgid: item.msgid, error: err.message }});
            }}
        }}
        return JSON.stringify(results);
    }})()
    """
    out = run_chrome_js(js)
    if not out:
        return []
    try:
        return json.loads(out)
    except:
        return []

def main():
    parser = argparse.ArgumentParser(description="微信公众号发表数据与公私域渠道诊断工具")
    parser.add_argument("--limit", type=int, default=40, help="分析最近N篇文章 (默认40)")
    parser.add_argument("--all", action="store_true", help="拉取全量全部历史文章")
    parser.add_argument("--refresh", action="store_true", help="强制刷新所有缓存")
    args = parser.parse_args()

    cache_dir = os.path.expanduser("~/.gemini/antigravity/scratch")
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, "all_analyzed_articles.json")

    print("=================================================================")
    print("🔍 [WeChat MP] 正在连接 Chrome 浏览器并拉取公众号实时发表数据...")
    print("=================================================================")

    # 1. 账号概览与流量主 7 日收益
    overview = get_account_overview()
    revenue_7d = get_publisher_revenue(days=7)
    home_stats = overview.get("homeStats", {})
    read_7d = overview.get("read7d", 0)
    read_30d = overview.get("read30d", 0)
    today_str = datetime.now().strftime("%Y-%m-%d")

    # 2. 文章列表
    catalog = get_articles_catalog(max_count=200 if args.all else 60)
    if not catalog:
        print("❌ 无法获取文章列表，请确认 Chrome 浏览器已打开微信公众号后台 (mp.weixin.qq.com) 且处于登录状态！")
        sys.exit(1)

    target_articles = catalog if args.all else catalog[:args.limit]
    print(f"✅ 成功扫描到发布记录，本次将精准分析最近 {len(target_articles)} 篇已发表文章...")

    # 3. 读取或补充缓存
    analyzed_map = {}
    if os.path.exists(cache_file) and not args.refresh:
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_list = json.load(f)
                for a in cached_list:
                    if "error" not in a and a.get("msgid"):
                        analyzed_map[a["msgid"]] = a
        except:
            analyzed_map = {}

    to_fetch = [a for a in target_articles if a["msgid"] not in analyzed_map]
    if to_fetch:
        print(f"📥 正在分批拉取 {len(to_fetch)} 篇最新单篇渠道分布明细 (每批10篇)...")
        batch_size = 10
        for i in range(0, len(to_fetch), batch_size):
            batch = to_fetch[i:i+batch_size]
            res = fetch_details_batch(batch)
            for r in res:
                if "error" not in r:
                    analyzed_map[r["msgid"]] = r
            time.sleep(0.3)
        
        # Save cache
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(list(analyzed_map.values()), f, ensure_ascii=False, indent=2)

    # 4. 统计与指标计算 (保证实时指标100%最新，不被缓存陈旧数字覆盖)
    analyzed_articles = []
    for a in target_articles:
        cached = analyzed_map.get(a["msgid"], {})
        # 以实时的 a 覆盖 cached 中的计数指标 (read_num, share_num, like_num 等)
        item = {**cached, **a}
        ch = cached.get("channels", {})
        ch_total = sum(ch.values())
        rec_uv = ch.get("6", 0)
        msg_uv = ch.get("0", 0)
        chat_uv = ch.get("1", 0)
        
        rec_ratio = (rec_uv / ch_total * 100) if ch_total > 0 else 0.0
        msg_ratio = (msg_uv / ch_total * 100) if ch_total > 0 else 0.0
        chat_ratio = (chat_uv / ch_total * 100) if ch_total > 0 else 0.0
        
        r_num = a.get("read_num", 0)
        s_num = a.get("share_num", 0)
        share_rate = (s_num / r_num * 100) if r_num > 0 else 0.0
        raw_fin = item.get("finished_read_ratio", 0) or 0
        finish_pct = (raw_fin * 100.0) if 0 < raw_fin <= 1.0 else float(raw_fin)
        is_t0_unsettled = (a.get("date") == today_str and ch_total == 0)

        analyzed_articles.append({
            **item,
            "read_num": r_num,
            "share_num": s_num,
            "like_num": a.get("like_num", 0),
            "old_like_num": a.get("old_like_num", 0),
            "ch_total": ch_total,
            "rec_uv": rec_uv,
            "msg_uv": msg_uv,
            "chat_uv": chat_uv,
            "rec_ratio": rec_ratio,
            "msg_ratio": msg_ratio,
            "chat_ratio": chat_ratio,
            "share_rate": share_rate,
            "finish_pct": finish_pct,
            "is_t0_unsettled": is_t0_unsettled,
        })

    # 分层
    tier_high = [a for a in analyzed_articles if a["read_num"] >= 1000]
    tier_mid = [a for a in analyzed_articles if 300 <= a["read_num"] < 1000]
    tier_low = [a for a in analyzed_articles if a["read_num"] < 300 and a["read_num"] > 0]

    # 输出结构化终端报告
    print("\n" + "=" * 65)
    print("📊 一、 账号全盘大盘画像 (宏观流量构成)")
    print("=" * 65)
    if home_stats:
        cum_fans = home_stats.get("cumulate_user", "--")
        yest_read = home_stats.get("yesterday_read", "--")
        yest_share = home_stats.get("yesterday_share", "--")
        yest_follow = home_stats.get("yesterday_follow", "--")
        weekly_rec = home_stats.get("weekly_rec", "--")
        print(f"👥 实时总粉丝数: {cum_fans} 人 | 昨日新增关注: +{yest_follow} 人")
        print(f"📈 昨日大盘: 阅读 {yest_read} 人 | 分享 {yest_share} 人 | 创作周报: 推荐带来 {weekly_rec} 阅读")
    
    if read_30d > 0:
        print(f"🌐 官方统计: 近30天总阅读用户 {read_30d:,} 人 | 近7天总阅读用户 {read_7d:,} 人")

    if revenue_7d:
        tot_rev = sum(r["income_yuan"] for r in revenue_7d)
        tot_views = sum(r["views"] for r in revenue_7d)
        avg_ecpm = (tot_rev / tot_views * 1000) if tot_views > 0 else 0.0
        latest = revenue_7d[0]
        print(f"💰 流量主近{len(revenue_7d)}日: 累计收入 ¥{tot_rev:.2f} | 综合 eCPM ¥{avg_ecpm:.2f} | 昨日({latest['date']}) ¥{latest['income_yuan']:.2f} (曝光 {latest['views']:,}, 点击 {latest['clicks']}, eCPM ¥{latest['ecpm']:.2f})")
    
    # Calculate aggregate channel distribution across analyzed articles
    agg_channels = {}
    for a in analyzed_articles:
        for s, v in a.get("channels", {}).items():
            agg_channels[s] = agg_channels.get(s, 0) + v
    total_agg_uv = sum(agg_channels.values())
    if total_agg_uv > 0:
        print(f"\n📑 本批次 {len(analyzed_articles)} 篇已发表文章渠道分布聚合 (总UV: {total_agg_uv:,}):")
        for s_code, uv in sorted(agg_channels.items(), key=lambda x: x[1], reverse=True):
            s_name = SCENES_MAP.get(str(s_code), f"渠道{s_code}")
            pct = uv / total_agg_uv * 100
            bar = "█" * int(pct / 4)
            print(f"   - {s_name:20s}: {uv:6,d} 人 ({pct:5.1f}%) {bar}")

    print("\n" + "=" * 65)
    print("⚔️ 二、 爆款池 vs 低阅池：公域推荐依赖度分层对决")
    print("=" * 65)
    
    def format_tier(name, items):
        if not items:
            return f"【{name}】: 0 篇"
        settled = [x for x in items if not x.get("is_t0_unsettled")]
        avg_r = statistics.mean([x["read_num"] for x in items])
        avg_rec = statistics.mean([x["rec_ratio"] for x in settled]) if settled else 0.0
        avg_msg = statistics.mean([x["msg_ratio"] for x in settled]) if settled else 0.0
        avg_share = statistics.mean([x["share_rate"] for x in items])
        fin_vals = [x["finish_pct"] for x in items if x.get("finish_pct", 0) > 0]
        avg_finish_str = f"{statistics.mean(fin_vals):5.1f}%" if fin_vals else "  -- "
        zero_rec = sum(1 for x in settled if x["rec_uv"] == 0 or x["rec_ratio"] < 5.0)
        zero_denom = len(settled)
        zero_pct = (zero_rec / zero_denom * 100) if zero_denom > 0 else 0.0
        return (
            f"【{name}】（共 {len(items)} 篇，占比 {len(items)/len(analyzed_articles)*100:.1f}%）:\n"
            f"   - 平均阅读量: {avg_r:.0f} 阅\n"
            f"   - 推荐流量占比 (公域·已结算): {avg_rec:5.1f}% 👈\n"
            f"   - 粉丝消息占比 (私域·已结算): {avg_msg:5.1f}%\n"
            f"   - 平均完读率: {avg_finish_str} | 平均分享率: {avg_share:5.2f}%\n"
            f"   - 零推荐比例 (<5%推荐·不含T+0): {zero_rec}/{zero_denom} 篇 ({zero_pct:.1f}%)"
        )

    print(format_tier("头部破圈爆款池 (阅读 >= 1000)", tier_high))
    print("-" * 50)
    print(format_tier("腰部探索池 (阅读 300 ~ 999)", tier_mid))
    print("-" * 50)
    print(format_tier("低阅读私域池 (阅读 < 300)", tier_low))


    print("=" * 65)
    print("⏱️ 三、 近期发表文章全景追踪 (按时间倒序)")
    print("=" * 65)
    sorted_by_time = sorted(analyzed_articles, key=lambda x: (x.get("date") or "", x.get("msgid") or ""), reverse=True)
    for i, a in enumerate(sorted_by_time[:6]):
        r = a.get("read_num", 0)
        sr = a.get("share_rate", 0.0)
        fp = a.get("finish_pct", 0.0)
        fp_str = f"{fp:4.1f}%" if fp > 0 else "  -- "
        if a.get("is_t0_unsettled"):
            ch_str = "推荐:结算中 | 粉丝:结算中"
        else:
            ch_str = f"推荐:{a.get('rec_ratio', 0.0):4.1f}% | 粉丝:{a.get('msg_ratio', 0.0):4.1f}%"
        title = a.get("title", "")[:36]
        d = a.get("date", "--")
        print(f" {i+1}. [{r:4d}阅 | 完读:{fp_str} | 享:{sr:4.1f}% | {ch_str}] {title} ({d})")

    print("\n" + "=" * 65)
    print("🏆 四、 头部爆款文章渠道透视 TOP 5")
    print("=" * 65)
    sorted_high = sorted(analyzed_articles, key=lambda x: x["read_num"], reverse=True)
    for i, a in enumerate(sorted_high[:5]):
        fp = a.get("finish_pct", 0.0)
        fp_str = f"{fp:4.1f}%" if fp > 0 else "  -- "
        print(f" {i+1}. [{a['read_num']:5d}阅 | 完读:{fp_str} | 享:{a['share_rate']:4.1f}% | 推荐:{a['rec_ratio']:4.1f}% | 粉丝:{a['msg_ratio']:4.1f}%] {a['title'][:36]} ({a['date']})")

    print("\n" + "=" * 65)
    print("❄️ 五、 近期低阅读文章归因透视 (为什么卡在 100 阅)")
    print("=" * 65)
    sorted_by_date = sorted(analyzed_articles, key=lambda x: x["date"], reverse=True)
    low_recent = [a for a in sorted_by_date if a["read_num"] < 250][:8]
    for i, a in enumerate(low_recent):
        if a.get("is_t0_unsettled"):
            tag = "⏳ 当日数据结算中 (T+0 渠道未出)"
        elif a["share_rate"] >= 15.0 and a["rec_ratio"] < 5.0:
            tag = "⚡️ 圈层自嗨 (高分享但死在第1关CTR/第2关完读率)"
        elif a["rec_ratio"] < 5.0:
            tag = "❄️ 零推荐 (公域初筛未通过)"
        elif a["rec_ratio"] < 20.0:
            tag = "⚠️ 微推荐 (推荐受阻)"
        else:
            tag = "🌱 推荐中"
        print(f" {i+1}. [{a['read_num']:3d}阅 | 享:{a['share_rate']:4.1f}% | {tag}] {a['title'][:34]} ({a['date']})")

    print("\n" + "=" * 65)
    print("💡 六、 算法分发核心洞察与运营铁律")
    print("=" * 65)
    print("1. 【三道递进闸门定律】: 算法按‘第1关公域CTR ➔ 第2关完读率 ➔ 第3关分享率’严格顺序考核。高分享率（如26%）若死在第1关（标题出现‘路由器/改代码’等认知阻力词，或封面脱敏），公域流在第1关即刻熔断！")
    print("2. 【圈层自嗨与收藏吃灰】: 极客圈层高分享多为‘收藏吃灰/标记转发’，若字数过长（>2000字）导致完读率<20%，系统判定为枯燥沉重，彻底切断外部分发。")
    print("3. 【严格字数控制与零阻力】: 纯文本必须严格控制在 1000~1300 字（保 40%+ 完读率），标题与封面严禁使用‘改路由器/改代码/DNS’等认知门槛词，用‘插上U盘/一键解压/扫码秒推’消除阻力。")
    print("4. 【私域底盘常态】: 本号目前有 80~120 个忠实常读铁粉。任何文章只要没有进入算法推荐，阅读量必然严格停留在 100~180 阅之间。")
    print("=================================================================\n")

    # 自动保存实证经验画像库供生产流水线 (gzh-article-pipeline) 消费闭环
    try:
        export_empirical_profile(overview, analyzed_articles, tier_high, tier_mid, tier_low, revenue_7d=revenue_7d)
    except Exception as e:
        print(f"⚠️ 保存经验画像时发生异常: {e}")

def export_empirical_profile(overview, analyzed_articles, tier_high, tier_mid, tier_low, revenue_7d=None):
    """
    将分析提炼出的实证数据沉淀为结构化 JSON，供 gzh-article-pipeline 实时消费
    """
    home_stats = overview.get("homeStats", {}) if overview else {}

    avg_low = statistics.mean([x["read_num"] for x in tier_low]) if tier_low else 120
    avg_high = statistics.mean([x["read_num"] for x in tier_high]) if tier_high else 2000
    avg_high_share = statistics.mean([x["share_rate"] for x in tier_high]) if tier_high else 15.0

    sorted_high = sorted(analyzed_articles, key=lambda x: x["read_num"], reverse=True)
    top_samples = []
    for a in sorted_high[:5]:
        top_samples.append({
            "title": a["title"],
            "read_num": a["read_num"],
            "rec_ratio": round(a["rec_ratio"], 1),
            "share_rate": round(a["share_rate"], 1),
            "finish_pct": round(a.get("finish_pct", 0.0), 1),
            "date": a["date"]
        })

    sorted_by_date = sorted(analyzed_articles, key=lambda x: x["date"], reverse=True)
    melted_samples = []
    for a in [x for x in sorted_by_date if x["read_num"] < 250 and not x.get("is_t0_unsettled")][:8]:
        melted_samples.append({
            "title": a["title"],
            "read_num": a["read_num"],
            "share_rate": round(a["share_rate"], 1),
            "rec_ratio": round(a["rec_ratio"], 1),
            "finish_pct": round(a.get("finish_pct", 0.0), 1),
            "date": a["date"]
        })

    profile_data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "account_macro": {
            "cumulate_user": home_stats.get("cumulate_user", "未知"),
            "yesterday_read": home_stats.get("yesterday_read", "0"),
            "yesterday_share": home_stats.get("yesterday_share", "0"),
            "yesterday_follow": home_stats.get("yesterday_follow", "0"),
            "weekly_rec": home_stats.get("weekly_rec", "0")
        },
        "recent_revenue_7d": revenue_7d or [],
        "empirical_rules": {
            "private_base_reads_range": [round(avg_low * 0.8), round(avg_low * 1.2)],
            "rec_breakout_target_reads": round(avg_high),
            "min_share_rate_threshold": round(avg_high_share, 1),
            "rec_ratio_breakout_threshold": 60.0,
            "core_insights": [
                "【三道递进闸门定律】: 算法按第1关公域CTR ➔ 第2关完读率 ➔ 第3关分享率严格顺序过关。26%高分享率若死在第1关门槛词，公域流直接熔断",
                "【圈层自嗨陷阱】: 极客高分享多为收藏式转发，若正文篇幅>2000字拖垮完读率，算法判定为枯燥沉重并终止推流",
                "【严格字数控制】: 正文纯文本必须严格控制在 1000~1300 字（保 40%+ 完读率），避免长文跳出",
                "【消灭认知阻力词】: 标题与封面严禁出现‘路由器/改代码/DNS/配置’，必须用‘插上U盘/扫码秒推/即开即用’零阻力动词",
                "【封面防脱敏与安全视窗】: 严禁连续使用千篇一律模板色；视窗内容高度<=525px居中y=[121, 646]，保留30px双向防裁切留白"
            ]
        },
        "top_performing_articles": top_samples,
        "recent_melted_topics": melted_samples
    }

    # 1. 保存到 wechat-content-analysis/references
    cur_ref_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "references"))
    os.makedirs(cur_ref_dir, exist_ok=True)
    out_file1 = os.path.join(cur_ref_dir, "account_empirical_profile.json")
    with open(out_file1, "w", encoding="utf-8") as f:
        json.dump(profile_data, f, ensure_ascii=False, indent=2)

    # 2. 同步保存到 gzh-article-pipeline/references (本地配置及 codex 路径)
    target_dirs = [
        os.path.expanduser("~/.gemini/config/skills/gzh-article-pipeline/references"),
        os.path.expanduser("~/.codex/skills/gzh-article-pipeline/references")
    ]
    saved_paths = [out_file1]
    for p_dir in target_dirs:
        if os.path.exists(p_dir):
            out_target = os.path.join(p_dir, "account_empirical_profile.json")
            with open(out_target, "w", encoding="utf-8") as f:
                json.dump(profile_data, f, ensure_ascii=False, indent=2)
            saved_paths.append(out_target)

    print("📦 [Empirical Profile] 实证经验画像已同步持久化:")
    for sp in saved_paths:
        print(f"   - {sp}")
    print()

if __name__ == "__main__":
    main()
