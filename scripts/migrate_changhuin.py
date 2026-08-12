#!/usr/bin/env python3
"""v2: 修复代码块/版权门槛/headerlink/summary 后重新迁移 23 篇"""
import re, json, time, os, glob, subprocess, html, urllib.request

BASE = "https://changhuin.github.io"
ROOT = "/Users/chenzhiyun/work/haifeiWu.github.io"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

def fetch(url):
    for _ in range(4):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read().decode('utf-8', 'ignore')
        except Exception:
            time.sleep(3)
    return None

def norm(s):
    return re.sub(r'[\s\u3000\-_【】\[\]（）()：:，,。.!！?？、/\\*"\']', '', s).lower()

def slugify(title):
    from pypinyin import lazy_pinyin
    s = re.sub(r'[^\w\u4e00-\u9fff]', ' ', title).strip()
    py = '-'.join(lazy_pinyin(s))
    py = re.sub(r'\s+', '-', py).strip('-')
    return py[:80].lower()

def fix_hexo_code(h):
    """Hexo 代码块（表格/行号形式）→ <pre><code>"""
    def strip_wrap(code):
        code = re.sub(r'<br\s*/?>', '\n', code)
        code = re.sub(r'</?(?:span|code|pre|div|p|table|tbody|thead|tr|td|figure|colgroup|col)[^>]*>', '', code)
        return code
    def to_code(m):
        code = strip_wrap(m.group(1))
        code = html.unescape(code).strip('\n')
        return f'<pre><code>{html.escape(code)}</code></pre>'
    # 1) 表格形式代码块（先于通用 pre 处理，整表消费）
    h = re.sub(r'<table>\s*<tr>\s*<td class="gutter">[\s\S]*?</td>\s*<td class="code">([\s\S]*?)</td>\s*</tr>\s*</table>',
               to_code, h, flags=re.S)
    # 2) 剥离 figure 包装
    h = re.sub(r'</?figure[^>]*>', '', h)
    # 3) 其余 pre 块
    h = re.sub(r'<pre[^>]*>([\s\S]*?)</pre>', to_code, h, flags=re.S)
    # 4) 残余 td class=code
    h = re.sub(r'<td class="code">([\s\S]*?)</td>', to_code, h, flags=re.S)
    return h

def clean_body(body):
    # 版权门槛：关注我们图片 + 由于版权原因段
    body = re.sub(r'<p[^>]*>\s*<img[^>]*alt="关注我们"[^>]*>\s*</p>', '', body)
    body = re.sub(r'<p[^>]*><span[^>]*>\s*由于版权原因[\s\S]*?</p>', '', body)
    body = re.sub(r'<p[^>]*>\s*<span> 由于版权原因[\s\S]*?</p>', '', body)
    body = re.sub(r'由于版权原因[^<]*', '', body)
    # headerlink 锚点
    body = re.sub(r'<a href="#[^"]*" class="headerlink"[^>]*></a>', '', body)
    # 空 span id="more"
    body = re.sub(r'<span id="more"[^>]*>.*?</span>', '', body)
    # 重复的作者/原文链接 blockquote（正文中后续出现）
    body = re.sub(r'<blockquote[^>]*>\s*<p[^>]*>\s*<span>\s*作\s*者\s*：[\s\S]*?</blockquote>', '', body)
    body = re.sub(r'<p[^>]*>\s*<span>\s*作\s*者\s*：[\s\S]*?(</p>|$)', '', body)
    body = re.sub(r'<span style="color:\s*red;">原文链接：</span>', '', body)
    # 分享/QR 尾部（base64 图等）从"分享"开始截断
    k = body.find('分享')
    if k != -1:
        body = body[:k]
    return body

def main():
    meta = json.load(open('/tmp/ch_meta.json', encoding='utf-8'))
    hw = [a for a in meta if a['author'] == 'haifeiWu']
    exist = set()
    for f in glob.glob(os.path.join(ROOT, 'content/posts/*/index.md')):
        t = open(f, encoding='utf-8').read()
        m = re.search(r'^title:\s*"([^"]+)"', t, re.M)
        if m:
            exist.add(norm(m.group(1)))
    new = [a for a in hw if norm(a['title']) not in exist]
    used_slugs = set(os.path.basename(d) for d in glob.glob(os.path.join(ROOT, 'content/posts/*')))
    print(f"待迁移: {len(new)} 篇")

    for a in new:
        h = fetch(BASE + a['url'])
        if not h:
            print(f"  ✗ 抓取失败: {a['title']}")
            continue
        i = h.find('class="post-content_private"')
        if i == -1:
            print(f"  ✗ 未找到正文: {a['title']}")
            continue
        seg = h[i:]
        j = seg.find('<div class="post-nav"')
        if j == -1:
            j = seg.find('<div class="tags"')
        body = seg[:j] if j != -1 else seg
        k = body.find('</blockquote>')
        if k != -1:
            body = body[k + 12:]
        # 去掉结尾作者块（从"作 者："第一次出现于文末的位置截断）
        k = body.find('作 者：')
        if k != -1:
            body = body[:k]
        body = re.sub(r'<script[\s\S]*?</script>', '', body)
        body = re.sub(r'<style[\s\S]*?</style>', '', body)
        body = clean_body(body)
        body = fix_hexo_code(body)

        p = subprocess.run(['pandoc', '-f', 'html', '-t', 'gfm', '--wrap=none'],
                           input=body.encode(), capture_output=True)
        md = p.stdout.decode('utf-8', 'ignore')
        # 清理 pandoc 残留
        md = md.replace('\\>', '>')
        md = re.sub(r'^>\s*$', '', md, flags=re.M)
        md = re.sub(r'\n{3,}', '\n\n', md).strip()
        md = re.sub(r'^<pre><code>$[\s\S]*?^</code></pre>$', lambda m: m.group(0), md)  # 保留代码块

        title = a['title']
        date = (a['date'] or '2019-01-01') + 'T00:00:00+08:00'
        cat = a['cat'] or '后端'
        tags_clean = [t for t in (a['tags'] or []) if t.lower() not in ('haifeiwu', 'changhuin', 'hexo')]

        plain = re.sub(r'<[^>]+>', '', md)
        plain = re.sub(r'[#>*`\-\[\]()!]', ' ', plain)
        plain = html.unescape(re.sub(r'\s+', ' ', plain)).strip()
        summary = plain[:120].rstrip('，。；：,.;:')
        summary = summary.replace('"', '“').replace('\\', ' ')

        slug = slugify(title)
        base, n = slug, 2
        while slug in used_slugs:
            slug = f"{base}-{n}"
            n += 1
        used_slugs.add(slug)

        post_dir = os.path.join(ROOT, 'content/posts', slug)
        os.makedirs(post_dir, exist_ok=True)
        tags_line = json.dumps(tags_clean, ensure_ascii=False)
        cats_line = json.dumps([cat], ensure_ascii=False)
        fm = (f'---\ncategories: {cats_line}\ntitle: "{title}"\ndate: "{date}"\ntags: {tags_line}\n'
              f'summary: "{summary}"\ntranslationKey: "{slug}"\n---\n\n'
              f'> 📌 本文原发布于代码星冰乐：[{title}]({BASE}{a["url"]})\n\n')
        with open(os.path.join(post_dir, 'index.md'), 'w', encoding='utf-8') as f:
            f.write(fm + md + '\n')
        stub = (f'---\ntitle: "{title}"\ndate: "{date}"\ntags: {tags_line}\ncategories: {cats_line}\n'
                f'summary: "{summary}"\ntranslationKey: "{slug}"\n---\n\n'
                f'{{{{< include-post "content/posts/{slug}/index.md" >}}}}\n')
        with open(os.path.join(post_dir, 'index.zh-cn.md'), 'w', encoding='utf-8') as f:
            f.write(stub)
        n_img = len(re.findall(r'!\[', md))
        n_code = len(re.findall(r'^```', md, re.M)) // 2
        print(f"  ✓ {date[:10]} | {title} | 图:{n_img} 代码块:{n_code} | {slug}")
        time.sleep(0.5)

    print("完成")

main()
