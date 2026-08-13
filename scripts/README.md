# scripts/ — 建站期一次性工具

> ⚠️ 这些脚本是 2026-08 建站/迁移期间的一次性工具（掘金、代码星冰乐文章迁移、标签补全、机械修正），
> **日常发布文章不需要运行它们**。保留在此供复现迁移过程、或在需要批量回改时参考。
> `enrich_tags.py` 与 `fix_articles_mechanical.py` 可重跑（支持 `--dry-run`），两个迁移脚本依赖旧平台接口，可能已失效。

| 脚本 | 用途 |
|---|---|
| `migrate_juejin.py` | 掘金文章迁移（列表 API + 文章内容抓取） |
| `migrate_changhuin.py` | changhuin.github.io（代码星冰乐）Hexo 文章迁移 |
| `enrich_tags.py` | 文章标签补全 |
| `fix_articles_mechanical.py` | 文章机械修正（HTML 表格转代码块、图片清理等） |
