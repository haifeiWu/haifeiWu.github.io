#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从掘金迁移文章到 Hugo 站点（v2）：node 求值 NUXT payload 取内容"""
import json, re, subprocess, sys, time, urllib.request, os, html
from datetime import datetime, timezone, timedelta

USER_ID = "1574156379896103"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
      "Content-Type": "application/json"}
OUT_DIR = "/Users/chenzhiyun/work/haifeiWu.github.io/content/posts"
CST = timezone(timedelta(hours=8))
NODE_EXTRACT = r"""
const fs = require('fs');
const expr = fs.readFileSync('/dev/stdin', 'utf8');
try {
  const ctx = eval(expr);
  const entry = (ctx.state && ctx.state.view && ctx.state.view.column && ctx.state.view.column.entry) || {};
  const ai = entry.article_info || {};
  const c = ai.web_html_content || ai.content || '';
  process.stdout.write(c);
} catch (e) {
  process.stderr.write('EVAL_FAIL: ' + e.message);
  process.exit(1);
}
"""

def api_post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={**UA, "Origin": "https://juejin.cn", "Referer": "https://juejin.cn/"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def fetch_page(url, tries=3):
    last = None
    for t in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            last = e
            time.sleep(8 * (t + 1))
    raise RuntimeError(f"页面获取失败: {last}")

def extract_web_html_direct(page):
    """新文章：web_html_content:\"<json string>\" 直接提取"""
    marker = 'web_html_content:"'
    idx = page.find(marker)
    if idx == -1:
        return None
    start = idx + len(marker)
    i, n = start, len(page)
    while i < n:
        c = page[i]
        if c == "\\":
            i += 2; continue
        if c == '"':
            return json.loads('"' + page[start:i] + '"')
        i += 1
    return None

def extract_nuxt_expr(page):
    m = re.search(r"window\.__NUXT__=(.*?)\s*</script>", page, re.S)
    return m.group(1) if m else None

def get_content_via_node(expr):
    p = subprocess.run(["node", "-e", NODE_EXTRACT], input=expr.encode("utf-8"),
                       capture_output=True, timeout=30)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.decode()[:200])
    return p.stdout.decode("utf-8")

def html_to_markdown(h):
    h = re.sub(r"<style[\s\S]*?</style>", "", h, flags=re.I)
    p = subprocess.run(["pandoc", "-f", "html", "-t", "gfm", "--wrap=none", "--markdown-headings=atx"],
                       input=h.encode("utf-8"), capture_output=True)
    if p.returncode != 0:
        raise RuntimeError("pandoc error: " + p.stderr.decode()[:300])
    return p.stdout.decode("utf-8")

def slugify(title, used):
    from pypinyin import lazy_pinyin
    s = "".join(lazy_pinyin(title))
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    s = re.sub(r"-{2,}", "-", s)[:60].strip("-")
    if not s:
        s = "article"
    base, k, cand = s, 2, s
    while cand in used:
        cand = f"{base}-{k}"; k += 1
    used.add(cand)
    return cand

def main():
    arts = api_post("https://api.juejin.cn/content_api/v1/article/query_list",
                    {"user_id": USER_ID, "cursor": "0", "sort_type": 2, "limit": 20})
    arts = arts.get("data") or []
    print(f"列表获取成功：{len(arts)} 篇（本页，如有更多页再续）")
    # 完整分页
    all_arts, cursor, seen = [], "0", 0
    for _ in range(15):
        d = api_post("https://api.juejin.cn/content_api/v1/article/query_list",
                     {"user_id": USER_ID, "cursor": cursor, "sort_type": 2, "limit": 20})
        data = d.get("data") or []
        for it in data:
            ai = it.get("article_info", {})
            all_arts.append({
                "id": ai.get("article_id"), "title": (ai.get("title") or "").strip(),
                "ctime": int(ai.get("ctime") or 0), "brief": ai.get("brief_content") or "",
                "tags": [t.get("tag_name") for t in (ai.get("tags") or []) if t.get("tag_name")],
            })
        if not d.get("has_more"):
            break
        cursor = d.get("cursor") or cursor
    arts = all_arts
    print(f"共 {len(arts)} 篇")
    json.dump(arts, open("/tmp/juejin_meta.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    os.makedirs(OUT_DIR, exist_ok=True)
    used, ok, fail = set(), 0, 0
    for i, a in enumerate(arts, 1):
        aid, title = a["id"], a["title"]
        slug = slugify(title, used)
        dest = os.path.join(OUT_DIR, slug, "index.md")
        if os.path.exists(dest):
            print(f"[{i}/{len(arts)}] 跳过（已存在）: {title}"); ok += 1; continue
        print(f"[{i}/{len(arts)}] {title} ({aid})", flush=True)
        try:
            page = fetch_page(f"https://juejin.cn/post/{aid}")
            h = extract_web_html_direct(page)
            if h is None:
                expr = extract_nuxt_expr(page)
                if not expr:
                    raise RuntimeError("NUXT 表达式未找到")
                h = get_content_via_node(expr)
            if not h or not h.strip():
                raise RuntimeError("内容为空")
            md = html_to_markdown(h).strip()
            if not md:
                raise RuntimeError("转换后为空")
            date_s = datetime.fromtimestamp(a["ctime"], CST).strftime("%Y-%m-%dT%H:%M:%S+08:00")
            tags = json.dumps(a["tags"], ensure_ascii=False)
            brief = html.unescape(a["brief"] or md[:150]).replace("\n", " ")[:160]
            fm = (f'---\ntitle: "{title}"\ndate: "{date_s}"\n'
                  f'tags: {tags}\nsummary: "{brief}"\n---\n\n'
                  f'> 📌 本文原发布于掘金社区：[{title}](https://juejin.cn/post/{aid})\n\n')
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "w", encoding="utf-8") as f:
                f.write(fm + md + "\n")
            ok += 1
        except Exception as e:
            fail += 1
            print(f"  ✗ 失败: {e}", flush=True)
            with open("/tmp/juejin_fail.log", "a", encoding="utf-8") as f:
                f.write(f"{aid}\t{title}\t{e}\n")
        time.sleep(2.5)
    print(f"\n完成：成功 {ok}，失败 {fail}")

if __name__ == "__main__":
    main()
