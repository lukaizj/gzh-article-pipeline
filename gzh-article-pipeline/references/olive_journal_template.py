# -*- coding: utf-8 -*-
"""
gzh-article-pipeline 经典「橄榄手记 (theme-olive-journal)」标准版式组件库
完全对标 yt-dlp 爆款文章 (https://mp.weixin.qq.com/s/J6uXtqTk8AhrJWPuYz6GIg)
包含段落、PART标题、暗夜卡片、蓝边引言、深色终端、细线表格与 100% <span leaf=""> 校验封装
"""

import os
import re
from html.parser import HTMLParser

def leaf(text):
    return f'<span leaf="">{text}</span>'

def p(text, align="justify"):
    return f'''<section style="margin-top:24px;">
  <section style="font-family:-apple-system,BlinkMacSystemFont,PingFang SC,Hiragino Sans GB,sans-serif;">
    <p style="margin:0;font-size:14px;line-height:1.9;text-align:{align};color:#4d4f46;">
      {text}
    </p>
  </section>
</section>'''

def strong(text):
    return f'<strong style="color:#23251d;"><span leaf="">{text}</span></strong>'

def hl(text):
    """
    行内关键词高亮标签（注意：仅限用于 10 字以内的短词或关键词！严禁包裹跨行长句子，否则 WebKit/微信浏览器会产生边框重叠破损。长句请使用 strong()）
    """
    return f'<span style="background:#eeefe9;padding:1px 5px;border-radius:4px;font-weight:600;color:#23251d;border:1px solid #bfc1b7;"><span leaf="">{text}</span></span>'

def underline(text):
    return f'<span style="border-bottom:2px solid #2e6cc4;font-weight:600;color:#23251d;"><span leaf="">{text}</span></span>'

def code_inline(text):
    return f'<span style="background:#eeefe9;color:#23251d;padding:2px 6px;border-radius:4px;font-family:ui-monospace,Menlo,Monaco,Consolas,monospace;font-size:13px;border:1px solid #b6b7af;"><span leaf="">{text}</span></span>'

def section_title(num, title, sub):
    """
    经典双层分段标题：大号 PART 计数器 + 1px 细竖线分割 + 纯黑标题 + 灰绿副标
    """
    return f'''<section style="margin-top:36px;">
  <section style="font-family:-apple-system,BlinkMacSystemFont,PingFang SC,Hiragino Sans GB,sans-serif;">
    <section style="display:flex;align-items:center;gap:14px;">
      <section style="text-align:center;flex-shrink:0;">
        <p style="margin:0;font-size:24px;font-weight:800;color:#23251d;line-height:1;letter-spacing:-2px;"><span leaf="">{num}</span></p>
        <p style="margin:0;font-size:8px;font-weight:700;color:#9ea096;letter-spacing:2px;"><span leaf="">PART</span></p>
      </section>
      <span style="width:1px;height:36px;background:#bfc1b7;flex-shrink:0;display:inline-block;overflow:hidden;vertical-align:middle;font-size:0;line-height:0;"><span leaf="">&nbsp;</span></span>
      <section>
        <p style="margin:0 0 1px;font-size:17px;font-weight:800;color:#23251d;letter-spacing:0.2px;"><span leaf="">{title}</span></p>
        <p style="margin:0;font-size:11px;font-weight:600;color:#65675e;letter-spacing:1.2px;"><span leaf="">{sub}</span></p>
      </section>
    </section>
  </section>
</section>'''

def image_card(img_path_or_name, caption, images_base=None):
    """
    带细边框与居中题注的配图卡片
    """
    if images_base and not os.path.isabs(img_path_or_name):
        full_path = os.path.join(images_base, img_path_or_name)
    else:
        full_path = img_path_or_name
    return f'''<section style="margin-top:24px;">
  <figure style="font-family:-apple-system,BlinkMacSystemFont,PingFang SC,Hiragino Sans GB,sans-serif;margin:0;">
    <section style="border-radius:6px;overflow:hidden;border:1px solid #bfc1b7;display:block;">
      <span leaf=""><img src="{full_path}" alt="{caption}" style="max-width:100%;height:auto;display:block;margin:0 auto;"></span>
    </section>
    <figcaption style="font-size:13px;line-height:1.7;color:#65675e;text-align:center;margin-top:10px;"><span leaf="">— {caption} —</span></figcaption>
  </figure>
</section>'''

def editors_note(tag, sub, text):
    """
    暗夜控制台卡片：黑色顶部状态栏 + 浅米色内容主体 + 细边框
    """
    return f'''<section style="margin-top:24px;">
  <section style="background:#fdfdf8;border:1px solid #bfc1b7;border-radius:6px;overflow:hidden;font-family:-apple-system,BlinkMacSystemFont,PingFang SC,Hiragino Sans GB,sans-serif;">
    <section style="padding:10px 16px;background:#1e1f23;display:flex;align-items:center;justify-content:space-between;gap:10px;">
      <span style="font-size:12px;font-weight:700;letter-spacing:1.5px;color:#fdfdf8;"><span leaf="">{tag}</span></span>
      <span style="font-size:10px;font-weight:500;color:#a0a29a;letter-spacing:1px;"><span leaf="">{sub}</span></span>
    </section>
    <section style="padding:14px 16px;">
      <p style="margin:0;font-size:13px;line-height:1.85;color:#4d4f46;text-align:justify;">
        {text}
      </p>
    </section>
  </section>
</section>'''

def quote_card(quote_text, author_title):
    """
    科技蓝边引言卡片：左侧 4px solid #2e6cc4
    """
    return f'''<section style="margin-top:24px;">
  <section style="background:#f7f8f4;border-left:4px solid #2e6cc4;padding:14px 18px;border-radius:0 6px 6px 0;font-family:-apple-system,BlinkMacSystemFont,PingFang SC,Hiragino Sans GB,sans-serif;">
    <p style="margin:0 0 6px;font-size:14px;line-height:1.8;color:#23251d;font-weight:600;"><span leaf="">“{quote_text}”</span></p>
    <p style="margin:0;font-size:12px;color:#65675e;text-align:right;"><span leaf="">—— {author_title}</span></p>
  </section>
</section>'''

def code_block(lang, code_lines, title="COMMAND CENTER"):
    """
    深色终端窗口代码块
    """
    code_html = "<br>".join([f'<span leaf="">{line}</span>' for line in code_lines])
    return f'''<section style="margin-top:24px;">
  <section style="background:#1e1f23;border-radius:6px;overflow:hidden;border:1px solid #333630;font-family:ui-monospace,Menlo,Monaco,Consolas,monospace;">
    <section style="padding:8px 14px;background:#2b2d32;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #383a40;">
      <span style="font-size:11px;color:#9ea096;font-weight:700;letter-spacing:1px;text-transform:uppercase;"><span leaf="">{lang}</span></span>
      <span style="font-size:10px;color:#6d7066;"><span leaf="">{title}</span></span>
    </section>
    <section style="padding:14px 16px;overflow-x:auto;color:#e6e7e3;font-size:12px;line-height:1.7;">
      {code_html}
    </section>
  </section>
</section>'''

def comparison_table(headers, rows):
    """
    高清双色细线对照大表
    """
    th_cells = "".join([f'<th style="border:1px solid #bfc1b7;padding:9px 12px;background:#eeefe9;font-weight:800;color:#23251d;font-size:13px;text-align:left;"><span leaf="">{h}</span></th>' for h in headers])
    tr_rows = []
    for r in rows:
        td_cells = "".join([f'<td style="border:1px solid #bfc1b7;padding:8px 12px;font-size:12px;line-height:1.7;color:#4d4f46;"><span leaf="">{c}</span></td>' for c in r])
        tr_rows.append(f'<tr>{td_cells}</tr>')
    rows_html = "".join(tr_rows)
    return f'''<section style="margin-top:24px;overflow-x:auto;">
  <table style="width:100%;border-collapse:collapse;font-family:-apple-system,BlinkMacSystemFont,PingFang SC,Hiragino Sans GB,sans-serif;margin:0;">
    <thead>
      <tr>{th_cells}</tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>
</section>'''

def divider():
    """
    居中 48px 极细分割线
    """
    return f'''<section style="margin:36px 0;text-align:center;">
  <span style="display:inline-block;width:48px;height:2px;background:#bfc1b7;vertical-align:middle;"><span leaf="">&nbsp;</span></span>
</section>'''

def header_meta(category_tag, title, author="奇点造物所", read_time="8 分钟", subtitle="深度拆解"):
    """
    推文顶部元数据卡片
    """
    return f'''<section style="margin-bottom:28px;">
  <section style="font-family:-apple-system,BlinkMacSystemFont,PingFang SC,Hiragino Sans GB,sans-serif;">
    <p style="margin:0 0 6px;font-size:12px;font-weight:700;color:#2e6cc4;letter-spacing:1.5px;text-transform:uppercase;"><span leaf="">{category_tag}</span></p>
    <h1 style="margin:0 0 12px;font-size:22px;line-height:1.45;color:#23251d;font-weight:800;"><span leaf="">{title}</span></h1>
    <section style="display:flex;align-items:center;gap:12px;font-size:12px;color:#65675e;">
      <span><span leaf="">文 / {author}</span></span>
      <span><span leaf="">•</span></span>
      <span><span leaf="">阅读时间约 {read_time}</span></span>
      <span><span leaf="">•</span></span>
      <span><span leaf="">{subtitle}</span></span>
    </section>
  </section>
</section>'''

def github_portal_card(github_url, online_mirror=None, stars="100,000+", forks="10,000+", maintainers="1,000+"):
    """
    文末高质感 GitHub 传送门卡片
    """
    mirror_html = ""
    if online_mirror:
        mirror_html = f'''<section style="background:#eeefe9;padding:10px 14px;border-radius:6px;border:1px dashed #bfc1b7;text-align:left;margin-top:8px;">
    <p style="margin:0;font-size:11px;color:#65675e;font-weight:600;"><span leaf="">官方网页版在线检索导航：</span></p>
    <p style="margin:2px 0 0;font-size:13px;font-weight:700;color:#2e6cc4;font-family:ui-monospace,Menlo,Monaco,Consolas,monospace;"><span leaf="">{online_mirror}</span></p>
  </section>'''
    return f'''<section style="margin-top:36px;padding:20px 20px;background:#fdfdf8;border-radius:8px;border:1.5px solid #23251d;text-align:center;font-family:-apple-system,BlinkMacSystemFont,PingFang SC,Hiragino Sans GB,sans-serif;">
  <p style="margin:0 0 8px;font-size:16px;font-weight:800;color:#23251d;"><span leaf="">🚀 开源项目传送门</span></p>
  <p style="margin:0 0 14px;font-size:12px;line-height:1.6;color:#65675e;"><span leaf="">项目完全开源免费，建议每位开发者立即收藏，随时随地查阅最新动态！</span></p>
  <section style="background:#eeefe9;padding:10px 14px;border-radius:6px;border:1px dashed #bfc1b7;text-align:left;">
    <p style="margin:0;font-size:11px;color:#65675e;font-weight:600;"><span leaf="">GitHub 官方开源地址：</span></p>
    <p style="margin:2px 0 0;font-size:13px;font-weight:700;color:#2e6cc4;font-family:ui-monospace,Menlo,Monaco,Consolas,monospace;"><span leaf="">{github_url}</span></p>
  </section>
  {mirror_html}
  <p style="margin:12px 0 0;font-size:11px;color:#9ea096;"><span leaf="">⭐ {stars} Stars · 🍴 {forks} Forks · 👥 {maintainers} 维护者</span></p>
</section>'''

def outro_follow_card(author="奇点造物所", tagline="深度拆解前沿 AI 智能体技术与开源前沿神作，让技术为每一个人所用。<br>如果觉得本文有启发，欢迎点赞、在看、转发与评论！"):
    """
    底部关注与互动卡片
    """
    return f'''<section style="margin-top:28px;padding:18px 20px;background:#f7f8f4;border-radius:8px;border:1px solid #bfc1b7;text-align:center;font-family:-apple-system,BlinkMacSystemFont,PingFang SC,Hiragino Sans GB,sans-serif;">
  <p style="margin:0 0 6px;font-size:14px;font-weight:800;color:#23251d;"><span leaf="">欢迎关注「{author}」</span></p>
  <p style="margin:0;font-size:12px;line-height:1.8;color:#65675e;"><span leaf="">{tagline}</span></p>
</section>'''

def lead_magnet_card(keyword, title, items, subtitle="🎁 读者专属福利 · 免配置一键自取"):
    """
    高转化涨粉诱饵卡片 (Lead Magnet Card)
    引导读者关注公众号并发送指定关键词获取整合包/脚本/备忘录，打破只看不粉的僵局！
    """
    items_html = "".join([f'<li style="margin-bottom:6px;font-size:13px;line-height:1.6;color:#3b3d36;"><span leaf="">• {it}</span></li>' for it in items])
    return f'''<section style="margin-top:32px;padding:22px 20px;background:#fdfdf8;border:2px solid #16a085;border-radius:10px;box-shadow:4px 4px 0px #16a085;font-family:-apple-system,BlinkMacSystemFont,PingFang SC,Hiragino Sans GB,sans-serif;">
  <section style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
    <span style="font-size:12px;font-weight:800;color:#16a085;letter-spacing:1px;background:#e8f8f5;padding:4px 10px;border-radius:4px;border:1px solid #16a085;"><span leaf="">{subtitle}</span></span>
    <span style="font-size:11px;color:#87897e;font-weight:600;"><span leaf="">限时无套路直取</span></span>
  </section>
  <h3 style="margin:0 0 10px;font-size:16px;font-weight:800;color:#23251d;"><span leaf="">{title}</span></h3>
  <ul style="margin:0 0 16px;padding-left:18px;list-style-type:none;">
    {items_html}
  </ul>
  <section style="background:#e8f8f5;border:1.5px dashed #16a085;padding:12px 14px;border-radius:6px;text-align:center;">
    <p style="margin:0 0 4px;font-size:13px;font-weight:700;color:#23251d;"><span leaf="">👇 获取方式（免百度网盘限速）：</span></p>
    <p style="margin:0;font-size:13px;line-height:1.7;color:#16a085;"><span leaf="">关注微信公众号【奇点造物所】，后台对话框回复「</span><strong style="color:#c0392b;font-size:15px;"><span leaf="">{keyword}</span></strong><span leaf="">」即可秒级自取！</span></p>
  </section>
</section>'''

def interactive_cta_card(question, sub_tip="精选留言将置顶展示，欢迎交流踩坑心得！"):
    """
    评论区盖楼卡片 (Interactive CTA Card)
    通过引发情绪共鸣或站队话题，提升留言率和算法热度
    """
    return f'''<section style="margin-top:28px;padding:18px 20px;background:#fefbf3;border:1.5px solid #d4a373;border-radius:8px;font-family:-apple-system,BlinkMacSystemFont,PingFang SC,Hiragino Sans GB,sans-serif;">
  <section style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
    <span style="font-size:18px;"><span leaf="">💬</span></span>
    <p style="margin:0;font-size:14px;font-weight:800;color:#936639;"><span leaf="">留言区互动话题</span></p>
  </section>
  <p style="margin:0 0 8px;font-size:13px;line-height:1.7;font-weight:700;color:#23251d;"><span leaf="">{question}</span></p>
  <p style="margin:0;font-size:11px;color:#a68a68;"><span leaf="">{sub_tip}</span></p>
</section>'''

def section_title_editorial(title, sub=None, num=None):
    """
    科技杂志风（Cyber-Zen / Editorial）小标题：
    Noto Serif SC 衬线体，21px 加粗，朱砂红 #cf4436，平实质感
    """
    num_html = f'<span style="font-size:13px;font-weight:700;color:#9e9e98;letter-spacing:1.5px;margin-right:8px;font-family:ui-monospace,Menlo,monospace;"><span leaf="">CASE {num} // </span></span>' if num else ''
    sub_html = f'<p style="margin:4px 0 0;font-size:12px;color:#85877e;font-family:-apple-system,BlinkMacSystemFont,PingFang SC,Hiragino Sans GB,sans-serif;letter-spacing:0.8px;"><span leaf="">{sub}</span></p>' if sub else ''
    return f'''<section style="margin-top:38px;margin-bottom:14px;">
  <section style="font-family:STSong,Songti SC,Georgia,serif;">
    <h2 style="margin:0;font-size:21px;font-weight:700;line-height:1.4;color:#cf4436;letter-spacing:0.3px;">
      {num_html}<span leaf="">{title}</span>
    </h2>
    {sub_html}
  </section>
</section>'''

def p_editorial(text, align="justify"):
    """
    科技杂志风温润正文：15px，行高 1.9，温润深灰 #4a4a45
    """
    return f'''<section style="margin-top:20px;">
  <section style="font-family:-apple-system,BlinkMacSystemFont,PingFang SC,Hiragino Sans GB,sans-serif;">
    <p style="margin:0;font-size:15px;line-height:1.9;text-align:{align};color:#4a4a45;letter-spacing:0.2px;">
      {text}
    </p>
  </section>
</section>'''

def strong_editorial(text):
    """
    科技杂志风朱砂红加粗重点
    """
    return f'<strong style="color:#cf4436;font-weight:700;"><span leaf="">{text}</span></strong>'

def test_case_card(case_no, title, prompt_text, result_summary, evidence=None):
    """
    真机硬核实测卡片 (Edge-Case Torture Test Card)
    对标顶级技术自媒体的实机探针测试，突出真实输入、分步响应与证据链
    """
    evidence_html = f'''<section style="margin-top:10px;padding-top:8px;border-top:1px dashed #dcded6;font-size:11px;color:#7c7e75;display:flex;align-items:center;justify-content:space-between;">
      <span><span leaf="">🔍 验证证据链：{evidence}</span></span>
      <span style="color:#16a085;font-weight:600;"><span leaf="">✓ 实测通过</span></span>
    </section>''' if evidence else ''
    return f'''<section style="margin-top:26px;border-radius:8px;border:1px solid #dcded6;background:#fcfcf9;overflow:hidden;font-family:-apple-system,BlinkMacSystemFont,PingFang SC,Hiragino Sans GB,sans-serif;">
  <section style="padding:10px 16px;background:#f3f4ee;border-bottom:1px solid #dcded6;display:flex;align-items:center;justify-content:space-between;">
    <span style="font-size:12px;font-weight:700;color:#cf4436;letter-spacing:1px;font-family:ui-monospace,Menlo,monospace;"><span leaf="">TEST CASE #{case_no:02d}</span></span>
    <span style="font-size:12px;font-weight:700;color:#23251d;"><span leaf="">{title}</span></span>
  </section>
  <section style="padding:14px 16px;">
    <section style="background:#ffffff;border:1px solid #e3e5dc;border-radius:6px;padding:10px 14px;margin-bottom:12px;">
      <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:#85877e;"><span leaf="">💬 刁钻提问 / 极限测试输入：</span></p>
      <p style="margin:0;font-size:13px;line-height:1.6;color:#1e1f23;font-style:italic;"><span leaf="">“{prompt_text}”</span></p>
    </section>
    <section style="font-size:13px;line-height:1.8;color:#4a4a45;">
      {result_summary}
    </section>
    {evidence_html}
  </section>
</section>'''


class LeafWrapper(HTMLParser):
    """
    自动确保所有文本节点 100% 被 <span leaf=""> 包裹
    """
    def __init__(self):
        super().__init__()
        self.output = []
        self.in_leaf = False
        self.leaf_depth = 0

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        is_leaf = (tag == 'span' and 'leaf' in attr_dict)
        if is_leaf:
            self.leaf_depth += 1
            self.in_leaf = True

        attrs_str = ''
        if attrs:
            formatted_attrs = []
            for k, v in attrs:
                if v is None:
                    formatted_attrs.append(k)
                else:
                    formatted_attrs.append(f'{k}="{v}"')
            attrs_str = ' ' + ' '.join(formatted_attrs)
        
        self.output.append(f'<{tag}{attrs_str}>')

    def handle_endtag(self, tag):
        self.output.append(f'</{tag}>')
        if tag == 'span' and self.leaf_depth > 0:
            self.leaf_depth -= 1
            if self.leaf_depth == 0:
                self.in_leaf = False

    def handle_startendtag(self, tag, attrs):
        attrs_str = ''
        if attrs:
            formatted_attrs = []
            for k, v in attrs:
                if v is None:
                    formatted_attrs.append(k)
                else:
                    formatted_attrs.append(f'{k}="{v}"')
            attrs_str = ' ' + ' '.join(formatted_attrs)
        self.output.append(f'<{tag}{attrs_str}>')

    def handle_data(self, data):
        if self.in_leaf or not data.strip():
            self.output.append(data)
        else:
            m = re.match(r'^(\s*)(.*?)(\s*)$', data, re.DOTALL)
            lead, text, trail = m.groups()
            self.output.append(f'{lead}<span leaf="">{text}</span>{trail}')

    @classmethod
    def wrap(cls, html_str):
        p = cls()
        p.feed(html_str)
        return "".join(p.output)

class LeafValidator(HTMLParser):
    """
    校验未包裹裸文本节点数量（目标为 0）
    """
    def __init__(self):
        super().__init__()
        self.tag_stack = []
        self.bare_texts = []

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        is_leaf = (tag == 'span' and 'leaf' in attr_dict)
        self.tag_stack.append((tag, is_leaf))

    def handle_endtag(self, tag):
        if self.tag_stack:
            self.tag_stack.pop()

    def handle_data(self, data):
        text = data.strip()
        if text:
            has_leaf = any(t[1] for t in self.tag_stack)
            if not has_leaf:
                parent = self.tag_stack[-1][0] if self.tag_stack else 'root'
                self.bare_texts.append((parent, text[:40]))

    @classmethod
    def validate(cls, html_str):
        v = cls()
        v.feed(html_str)
        return v.bare_texts, []

