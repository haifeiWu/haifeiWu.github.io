---
name: publishing-haifeiwu-site
description: Use when publishing to or updating the haifeiWu personal site (haifeiWu.github.io, Hugo + Blowfish). Triggers: adding or migrating blog articles, editing site content/config, pushing to the repo, or debugging why a deploy failed or a page 404s/renders wrong. Covers the China-network build, single-language Chinese post conventions, git identity for commits, and GitHub Actions deploy verification.
---

# Publishing haifeiWu Site

## Overview

The site is a **Hugo + Blowfish** blog + portfolio: **Chinese (zh-cn) default** with an English (en) variant for static pages. **Posts/articles are Chinese-only** — no /en/ article URLs, no language switcher on post pages at `haifeiWu.github.io`, source in `/Users/chenzhiyun/work/haifeiWu.github.io`. Flow: **edit content → local build → commit (as haifeiWu) → push to main (SSH) → GitHub Actions deploys → verify live**.

## When to Use

- Adding a new article, migrating articles from juejin / changhuin.github.io, or editing site pages/config
- Pushing to the repo or checking deploy status
- Debugging: 404 pages, broken images, wrong rendering, failed pushes

**NOT for:** changing the GitHub repo's Pages setting (must stay "GitHub Actions" — never switch to "Deploy from a branch" or the site 404s via Jekyll).

## Quick Reference

```bash
cd /Users/chenzhiyun/work/haifeiWu.github.io

# Build (module proxy required in China — direct GitHub fails)
HUGO_MODULE_PROXY=https://goproxy.cn,direct hugo
# or full deploy-check build:
HUGO_MODULE_PROXY=https://goproxy.cn,direct hugo --minify --cleanDestinationDir

# Commit — ALWAYS with explicit identity (global git identity is wrong)
git add -A
git -c user.name="haifeiWu" -c user.email="whfstudio@163.com" commit -m "..."

# Push — SSH only (HTTPS push fails: "could not read Username"). Retry on "access rights" error — it is transient.
GIT_SSH_COMMAND="ssh -o ConnectTimeout=30 -o ServerAliveInterval=15" git push origin main
```

**Branch:** always work on `main`. There is a stray `optimize/articles` branch — never commit there; if HEAD is on it, `git checkout main` first, then merge with `git merge --ff-only optimize/articles` if needed.

## New Post Workflow (Recipe)

1. **Create** `content/posts/{pinyin-slug}/index.md` (slug = pypinyin of title, lowercase, hyphens; keep under 80 chars)
2. **Front matter** (exact conventions):
   ```yaml
   ---
   categories: ["后端"]        # or ["总结"] for life/retrospective posts
   title: "中文标题"
   date: "2026-08-12T00:00:00+08:00"   # ISO with +08:00
   tags: ["标签A", "标签B"]     # 3-5 REAL topic tags, never more than 5
   summary: "纯文本摘要，不能含 HTML 或未转义引号"   # plain text only — HTML/quotes in summary breaks YAML
   ---
   ```
3. **Body**: Chinese content, `##` sections. Migrated posts start with `> 📌 本文原发布于<来源>：[标题](url)`
4. **Single file per post** — posts are Chinese-only (no en variant, no `translationKey`). Article URLs: `/posts/{slug}/`. Static pages (home `/`, `/about/`, `/projects/`, `/tags/`) are bilingual: Chinese at root, English at `/en/` — keep both `index.md` (zh-cn) and `index.en.md` in sync
5. Build locally, confirm `/posts/{slug}/` renders
6. Commit + push (see Quick Reference)
7. Poll deploy: `https://api.github.com/repos/haifeiWu/haifeiWu.github.io/actions/runs?per_page=1` until `completed|success` (~2-4 min), then verify the live URL returns 200

> **Language model (2026-08):** `defaultContentLanguage = "zh-cn"`; `languages.en.toml` + `menus.en.toml` give static pages an English variant at `/en/`. The en menu points Blog/Tags at the shared `/posts/` `/tags/` (absolute `url`), not `/en/` paths. Posts live only in zh-cn so the theme renders NO language switcher on them (`translations.html` gates on `.IsTranslated`). Do NOT recreate `/zh-cn/` paths or zh-cn stubs — that system is retired. The tags taxonomy auto-generates an English list page (`/en/tags/`) with no articles — harmless, leave it.

## Image Conventions

- Juejin CDN images (byteimg.com) work — a global `<meta name="referrer" content="no-referrer">` (in `layouts/partials/extend-head.html`) defeats their referer hotlink protection.
- Dead image hosts (e.g., `img.hchstudio.cn`, old Qiniu buckets): **remove the image, keep a meaningful caption** as `> 📷 图注：xxx`. Drop junk alts like "这里写图片描述".

## Custom Styling Gotcha

The theme ships **precompiled** CSS — Tailwind never scans site `layouts/`. Any utility class unique to your partials (e.g., `bottom-40`, `w-64`, `scale-95`, `dark:*` variants) is silently purged and the element renders unstyled/offscreen. Add missing classes to `assets/css/custom.css` (Tailwind v4 syntax, e.g. `.dark\:bg-neutral-800:is(.dark *){...}`).

## Migration Scripts (`scripts/`)

- `migrate_juejin.py` — juejin articles: list API pagination; new articles via `web_html_content`; old articles via node-eval of the `window.__NUXT__=` payload. Respect rate limits (retries + delays).
- `migrate_changhuin.py` — changhuin.github.io: filter `author == haifeiWu`; converts Hexo line-number code tables (`<table><td class="gutter">…<td class="code">…`) to `<pre><code>` BEFORE pandoc.
- `enrich_tags.py`, `fix_articles_mechanical.py` — tag enrichment / mechanical polish (rerunnable, `--dry-run` supported).

## Common Mistakes

| Symptom | Cause / Fix |
|---|---|
| Push fails "access rights…repository exists" | Transient SSH/network issue — retry the same push |
| Site 404 after deploy | Pages Source changed to "Deploy from a branch" (Jekyll builds Hugo source into nothing). User must set Settings → Pages → Source = **GitHub Actions** |
| `/zh-cn/posts/` empty | **Retired design (2026-08)**: the zh-cn posts section no longer exists — the site is unified, all articles at `/posts/`. Do NOT recreate `index.zh-cn.md` stubs. Old `/zh-cn/posts/{slug}/` links 301-redirect via aliases |
| Element unstyled/invisible | Utility classes purged — add to `assets/css/custom.css` |
| Article cards show "loading" forever | `[article] showViews` + demo Firebase config — disabled already; don't re-enable without a real Firebase project |
| Extra language dirs (de/es/…) built | Leftover `menus.*.toml` / `languages.*.toml` files implicitly define languages — delete them |
| Broken YAML / build error in a post | HTML or quotes leaked into `summary:` — keep summary plain text |

## Verifying a Deploy

```bash
# 1. wait for the Actions run
curl -sL "https://api.github.com/repos/haifeiWu/haifeiWu.github.io/actions/runs?per_page=1" | python3 -c "import json,sys; r=(json.load(sys.stdin)['workflow_runs'] or [{}])[0]; print(r['status'], r.get('conclusion'))"
# 2. check live pages (homepage, the new post, zh-cn variant)
curl -sL -o /dev/null -w "%{http_code}\n" "https://haifeiWu.github.io/"
```
