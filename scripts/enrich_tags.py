#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补全掘金文章的 tags / categories（从页面 NUXT payload 提取）"""
import json, re, subprocess, time, urllib.request, os, glob

OUT_DIR = "/Users/chenzhiyun/work/haifeiWu.github.io/content/posts"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
NODE_EXTRACT = r"""
const fs = require('fs');
const expr = fs.readFileSync('/dev/stdin', 'utf8');
try {
  const ctx = eval(expr);
  const entry = (ctx.state && ctx.state.view && ctx.state.view.column && ctx.state.view.column.entry) || {};
  const tags = (entry.tags || []).map(t => t.tag_name).filter(Boolean);
  const cat = (entry.category && entry.category.category_name) || '';
  process.stdout.write(JSON.stringify({tags, category: cat}));
} catch (e) {
  process.stderr.write('EVAL_FAIL: ' + e.message);
  process.exit(1);
}
"""

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

def enrich(expr):
    p = subprocess.run(["node", "-e", NODE_EXTRACT], input=expr.encode("utf-8"),
                       capture_output=True, timeout=30)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.decode()[:200])
    return json.loads(p.stdout.decode("utf-8"))

def main():
    posts = sorted(glob.glob(os.path.join(OUT_DIR, "*", "index.md")))
    print(f"共 {len(posts)} 篇待补全")
    done = fail = 0
    for f in posts:
        src = open(f, encoding="utf-8").read()
        m = re.search(r"juejin\.cn/post/(\d+)", src)
        if not m:
            print(f"跳过（无掘金 id）: {f}"); continue
        aid = m.group(1)
        # 已有 tags 的跳过（防重复抓取）
        fm_m = re.search(r"tags:\s*\[[^\]]*\]", src)
        if fm_m and "]" in fm_m.group(0) and len(fm_m.group(0)) > 12:
            continue
        try:
            page = fetch_page(f"https://juejin.cn/post/{aid}")
            expr_m = re.search(r"window\.__NUXT__=(.*?)\s*</script>", page, re.S)
            if not expr_m:
                raise RuntimeError("NUXT 未找到")
            info = enrich(expr_m.group(1))
            tags = info.get("tags") or []
            cat = info.get("category") or ""
            tags_json = json.dumps(tags, ensure_ascii=False)
            new = re.sub(r"tags:\s*\[[^\]]*\]", f"tags: {tags_json}", src, count=1)
            if cat:
                new = re.sub(r"^(---\n)", "\\1categories: " + json.dumps([cat], ensure_ascii=False) + "\n", new, count=1, flags=re.M)
            if new != src:
                open(f, "w", encoding="utf-8").write(new)
            print(f"✓ {os.path.basename(os.path.dirname(f))}: tags={tags} cat={cat}")
            done += 1
        except Exception as e:
            fail += 1
            print(f"✗ {aid}: {e}")
        time.sleep(2.5)
    print(f"\n补全完成：成功 {done}，失败 {fail}")

if __name__ == "__main__":
    main()
