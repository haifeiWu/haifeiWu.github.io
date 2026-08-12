---
categories: ["总结"]
title: "从 0 到 1：用 Hugo + Blowfish 搭建个人博客（建站复盘）"
date: "2026-08-12T00:00:00+08:00"
tags: ["个人网站", "Hugo", "GitHub Pages", "博客", "复盘"]
summary: "从 GitHub 主页 README 到个人博客与作品集，记录了 Hugo + Blowfish 建站、掘金与旧博客 87 篇文章迁移、GitHub Actions 自动部署的全过程，以及那些让人印象深刻的坑。"
translationKey: "cong-0-dao-1-yong-hugo-blowfish-da-jian-ge-ren-bo-ke-jian-zhan-fu-pan"
---

> 📌 本文为建站复盘原创文章，发布于本站：[haifeiWu.github.io](https://haifeiWu.github.io/)

> 说来惭愧，从 "想搭一个个人博客" 到 "博客真的跑起来了"，中间隔了整整一个 2026 年的夏天。

## 缘起：为什么会有这个站

程序员嘛，总得有个自己的地盘。

GitHub 主页的 README 用了一年多，摆着技术栈徽章、统计卡片、精选项目，倒也算体面。但 README 终究是 README——它装不下几十篇文章，也撑不起一个"作品集 + 博客"的门面。恰逢这段时间在掘金和代码星冰乐写了不少东西，散落在各个平台，总觉得缺一个**自己说了算**的地方。

于是决定：**搭一个 GitHub Pages 上的个人站点，把文章全部搬过来，以后首发都在这。**

## 技术选型：为什么是 Hugo + Blowfish

选型时其实没纠结太久：

- **Hugo**：Go 写的静态站点生成器，构建快到离谱（87 篇文章本地构建也就一两秒），而且咱本身就是写 Go 的，亲切。
- **Blowfish**：Hugo 生态里非常成熟的主题，内置了 Projects（项目展示）、i18n（多语言）、明暗主题、SEO 全套，基本开箱即用。

定了之后就一个目标：**中英双语，作品集 + 博客混合，全部文章带过来。**

## 内容迁移：87 篇文章是怎么搬过来的

这是整个建站过程中最耗时、也最"有意思"的部分。我一共迁移了两拨内容。

### 第一波：掘金 64 篇

掘金的文章列表 API 是公开的，翻页拉元数据很顺利。但**文章详情 API 需要登录态**，直接调不通。绕路方案：直接抓文章页面，从页面的 Nuxt 数据里把 `web_html_content` 抠出来。

新文章好办，字段就在明面上；**老文章（2019 年那批）web_html_content 是 null**，内容被压缩在 `window.__NUXT__=` 这个表达式里。咋办？用 node 把表达式 eval 出来，再一层层剥到 `article_info.content`。

再就是限流。掘金对高频抓取不太友好，重试 + 延迟 + 断点续跑，折腾了一晚上，总算 64 篇全须全尾地进了 `content/posts/`。

### 第二波：代码星冰乐 23 篇

代码星冰乐是我和朋友合写的老博客，我是其中一个作者。这波迁移有几个记忆点：

- **双作者筛选**：站点上 91 篇文章，作者标签是 haifeiWu 的有 64 篇，其中有 41 篇和掘金迁移过来的重复，最终新增 23 篇。
- **Hexo 的代码块**：老博客是 Hexo，代码渲染成"行号表格"结构（`<table><td class="gutter">…<td class="code">…`），直接转 markdown 会碎成一地 HTML。写了个预处理，先把表格还原成 `<pre><code>`，再交给 pandoc 转。
- **图床没了**：最扎心的一环。老博客的图片挂在 `img.hchstudio.cn`（DNS 已删）和七牛云老空间（已失效），试了 Wayback Machine，被限流到怀疑人生。最后忍痛**把图片去掉，只保留图注文字**——文字、代码、表格都在，图丢了，也算是给"云端的东西不归你管"交了一笔学费。

## 踩坑记：印象深刻的几个坑

建站全程踩坑无数，挑几个有代表性的记录一下，给后来人排雷。

### 坑 1：主题的 CSS 是预编译的，自定义类会被"裁剪"

Blowfish 的 CSS 是主题发布时预编译好的，Tailwind 扫描不到我站点 `layouts/` 里写的类。结果就是：我写的"请我喝杯咖啡"弹窗，点击后**在屏幕外渲染**——类没了，样式全塌。排查了半天，最后在 `assets/css/custom.css` 里手动补齐缺失的 Tailwind 工具类，问题解决。

教训：**改主题之前，先搞清楚它的构建产物是不是"成品"。**

### 坑 2：Pages 的 Source 设成了 Deploy from a branch，Hugo 站点变 404

这是最惊险的一个。第一次部署后站点正常，第二次 push 之后整个站点 404。查了半天：Pages 的构建方式被设成了 **Jekyll（Deploy from a branch）**，GitHub 直接拿 Hugo 源码去跑 Jekyll，构建出来的自然是空壳。在仓库 Settings → Pages 里把 Source 改回 **GitHub Actions**，站点立刻恢复。

教训：**GitHub Actions 部署的站点，Source 必须是 GitHub Actions。**

### 坑 3：菜单配置文件会"隐式定义语言"

exampleSite 残留了 7 种语言的 `languages.*.toml` 和 `menus.*.toml`，结果站点悄悄构建出了 8 种语言（连德语都有）。删掉 `menus.de.toml` 这类文件后，语言才只剩 en / zh-cn。

### 坑 4：文章归属默认语言，中文站一篇都没有

Hugo 多语言站点里，不带语言后缀的 `index.md` 默认归属 en。于是 `/zh-cn/posts/` 一直是空的——明明 87 篇文章都是中文内容。

解决方案：给每篇文章生成一个 `index.zh-cn.md` stub（只带 front matter + `translationKey`），再用一个 `include-post` 短代码，在中文页里渲染英文页的内容。文章内容只存一份，两个语言站共用。

### 坑 5：掘金图床有 Referer 防盗链

文章图片从掘金 CDN 加载时，带了 `github.io` 的 Referer 会被 403。解法是一行 meta：`<meta name="referrer" content="no-referrer">`，图片立刻恢复。

### 坑 6：主题作者留下的"彩蛋"

Blowfish 的 exampleSite 配置里有不少作者自己的东西：Buy Me a Coffee 组件（收款人还是主题作者）、Firebase 演示项目（阅读数永远 loading 的来源）、默认的 blowfish banner（社交分享图）。全部替换成了自己的：微信收款码弹窗、自制的 OG 图。

## SEO / GEO：让搜索引擎和 AI 都能读懂

内容搬完了，还做了一轮可见性优化：

- **结构化数据**：Person / Article / BreadcrumbList JSON-LD，作者、日期、关键词齐全
- **OG 分享图**：自制的 1200×630 品牌图，微信/社交分享不再显示主题作者横幅
- **llms.txt**：给 AI 引擎（ChatGPT / Perplexity / 文心）的站点摘要，站里放一份，AI 就能更好地"读懂"我
- **hreflang + sitemap**：多语言声明 + 自动生成的 sitemap，Google / Bing / 百度验证都已就位

## 一点总结

回头看看，这趟建站之旅最大的收获不是站点本身，而是**把"发布内容"这件事重新掌握在了自己手里**。

几个比较深的体会：

1. **内容永远比平台重要**。掘金的文章说删就删（老文章连 API 都不给你），云存储的图说没就没。自己的站点 + 自己的仓库，东西才是自己的。
2. **读源码胜过读文档**。主题的坑、Pages 的坑，最后都是靠翻模板源码、看构建产物才定位到的。
3. **自动化是安全感**。push 即部署，`git push origin main` 之后站点自动上线，再也不用记"部署流程"。

最后，站点在 [haifeiWu.github.io](https://haifeiWu.github.io/)，欢迎来逛。如果你也在考虑搭自己的博客，希望这篇复盘能帮你少踩几个坑——毕竟，我已经替你踩过了。

