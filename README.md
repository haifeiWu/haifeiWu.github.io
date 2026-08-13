# haifeiWu.github.io

个人网站：作品集 + 技术博客（[haifeiWu.github.io](https://haifeiWu.github.io/)）。

- **技术栈**：Hugo + Blowfish（Hugo Modules 引入），GitHub Pages + GitHub Actions 自动部署
- **语言**：文章仅中文（zh-cn），静态页（首页/关于/项目）中英双语
- **内容**：81 篇技术文章（迁移自掘金社区与代码星冰乐）+ 项目作品集

## 常用命令

```bash
# 本地构建（国内网络需模块代理，直连 GitHub 会失败）
HUGO_MODULE_PROXY=https://goproxy.cn,direct hugo

# 完整构建（部署前检查）
HUGO_MODULE_PROXY=https://goproxy.cn,direct hugo --minify --cleanDestinationDir

# 新增文章：在 content/posts/{pinyin-slug}/index.md 按约定写 front matter（见 archetypes/default.md）
```

## 部署

推送到 `main` 分支后，GitHub Actions（`.github/workflows/deploy.yml`）自动构建并发布到 GitHub Pages。提交请使用站点身份：

```bash
git -c user.name="haifeiWu" -c user.email="whfstudio@163.com" commit -m "..."
```

## 约定与 FAQ

发布/迁移/排障的完整约定见 [`skills/publishing-haifeiwu-site/SKILL.md`](skills/publishing-haifeiwu-site/SKILL.md)（同步自 `~/.agents/skills/publishing-haifeiwu-site/`）。

## 目录

| 路径 | 说明 |
|---|---|
| `content/posts/` | 博客文章（中文，一篇一目录） |
| `content/about/` `content/projects/` | 双语静态页（`index.md` zh-cn + `index.en.md` en） |
| `config/_default/` | 站点/主题/菜单/多语言配置 |
| `layouts/partials/` | 自定义 partial（SEO、微信赞赏弹窗） |
| `assets/css/custom.css` | 补充主题预编译 CSS 缺失的工具类 |
| `static/llms.txt` | LLM 站点索引 |
| `scripts/` | 建站期一次性迁移脚本（掘金/代码星冰乐文章迁移、标签补全等） |
