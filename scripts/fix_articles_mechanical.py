#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文章机械性修正（方案A·第一遍）

处理对象：content/posts/*/index.md（正文）与 index.zh-cn.md（仅 front matter）
修正项：
  1. 专用名词大小写统一（仅正文中的独立单词，跳过代码/URL/HTML/标识符）
  2. 中文与英文/数字间距（万字/亿/千/百/十/年月日等计数单位紧贴数字不加空格）
  3. 已核实的错别字 / 重复字
  4. 半角标点（, ; . ! ? :）在中文语境转全角，并清理全角标点后的多余空格

跳过：围栏代码块、4 空格缩进代码块、行内代码、URL、HTML 标签、front matter 中的
tags/categories/date/translationKey。

用法：
  python3 scripts/fix_articles_mechanical.py --dry-run   # 仅统计
  python3 scripts/fix_articles_mechanical.py            # 实际写回
"""
import glob
import re
import sys

POSTS = "content/posts/*/index*.md"

# ── 专用名词大小写映射（仅匹配"独立单词"，边界字符见 _BOUNDARY）──
CASE_MAP = {
    "redis": "Redis",
    "java": "Java",
    "mysql": "MySQL",
    "spring": "Spring",
    "netty": "Netty",
    "kafka": "Kafka",
    "dubbo": "Dubbo",
    "json": "JSON",
    "xml": "XML",
    "sql": "SQL",
    "api": "API",
    "websocket": "WebSocket",
    "zookeeper": "ZooKeeper",
    "docker": "Docker",
    "http": "HTTP",
    "hive": "Hive",
    "rocketmq": "RocketMQ",
    "elasticsearch": "Elasticsearch",
    "cpu": "CPU",
    "url": "URL",
    "linux": "Linux",
    "maven": "Maven",
    "hexo": "Hexo",
    "jdbc": "JDBC",
    "nginx": "Nginx",
    "gitlab": "GitLab",
}

# 混合大小写变体（仅独立单词，逻辑同 CASE_MAP）
MIXED_CASE_MAP = {
    "Mysql": "MySQL",
    "JAVA": "Java",
    "Gitlab": "GitLab",
    "Zookeeper": "ZooKeeper",
    "DUBBO": "Dubbo",
    "NETTY": "Netty",
    "Rocketmq": "RocketMQ",
}

# 前后不能出现的字符（避免误改 java.util / pom.xml / redis-cli / ${dubbo.version}
# / flavor = "mysql" / http: / git@ 等）
_BOUNDARY = r"A-Za-z0-9_\-.$/{#\"':@="

def fix_case(text):
    for low, proper in CASE_MAP.items():
        text = re.sub(
            r"(?<![" + _BOUNDARY + r"])" + re.escape(low) + r"(?![" + _BOUNDARY + r"])",
            proper, text,
        )
    for variant, proper in MIXED_CASE_MAP.items():
        text = re.sub(
            r"(?<![" + _BOUNDARY + r"])" + re.escape(variant) + r"(?![" + _BOUNDARY + r"])",
            proper, text,
        )
    return text

# ── 中文与数字之间：紧贴计数单位（万亿千百十兆年月日时分秒点号）时不加空格 ──
_COUNTING = "万亿千百十兆年月日时分秒点号"

def fix_spacing(text):
    text = re.sub(r"([\u4e00-\u9fff])([A-Za-z])", r"\1 \2", text)
    # 转义序列（\r \n \$ 等）中的字母不与中文加空格
    text = re.sub(r"(?<!\\)([A-Za-z])([\u4e00-\u9fff])", r"\1 \2", text)
    text = re.sub(
        r"([\u4e00-\u9fff])([0-9])",
        lambda m: m.group(0) if m.group(1) in _COUNTING else m.group(1) + " " + m.group(2),
        text,
    )
    text = re.sub(
        r"([0-9])([\u4e00-\u9fff])",
        lambda m: m.group(0) if m.group(2) in _COUNTING else m.group(1) + " " + m.group(2),
        text,
    )
    return text

# ── 半角标点 → 全角（左侧是中文时）──
def fix_punct(text):
    text = re.sub(r"(?<=[\u4e00-\u9fff]),", "，", text)
    text = re.sub(r"(?<=[\u4e00-\u9fff]);", "；", text)
    text = re.sub(r"(?<=[\u4e00-\u9fff])!", "！", text)
    text = re.sub(r"(?<=[\u4e00-\u9fff])\?", "？", text)
    text = re.sub(r"(?<=[\u4e00-\u9fff]):", "：", text)
    # 句号：仅当后面不是字母/数字/点/星号（避免 .gitlab-ci、3.14、… 等）
    text = re.sub(r"(?<=[\u4e00-\u9fff])\.(?![A-Za-z0-9.*])", "。", text)
    # 全角标点后的多余空格
    text = re.sub(r"([，。；：、！？）】」』…])[ ]+", r"\1", text)
    text = re.sub(r"[ ]+([，。；：、！？（【「『])", r"\1", text)
    return text

# ── 已核实的错别字 / 重复字（逐一核对过上下文）──
TYPO_FIXES = [
    ("标明填入", "表明填入"),          # sanliebiao: α 越小，标明→表明
    ("做为一个", "作为一个"),          # gitlab-runner 文章（summary + 正文）
    ("文件文件中", "文件中"),          # LightConf 三篇
    ("位于在", "放在"),                # LightConf 三篇
    ("只是是对", "只是对"),            # HashSet 文章
    ("搜索的的字段", "搜索的字段"),    # i-team ES 文章（注释）
    ("还学要", "还需要"),              # gitlab-runner 文章
    ("包括有:", "包括："),            # LightConf 三篇
]

def fix_typos(text):
    for old, new in TYPO_FIXES:
        text = text.replace(old, new)
    return text

# ── 受保护区间：URL / HTML 标签 / 行内代码 ──
_URL_RE = re.compile(r"https?://[^\s<>\"'\]\)]+")
_HTML_RE = re.compile(r"<[^>]*>")
_CODE_RE = re.compile(r"`[^`]*`")
# markdown 链接目标：[text](...) 中的 `](...)` 部分（含锚点 fragment 与 title）
_LINK_RE = re.compile(r"\]\([^)\n]*\)")

def protected_ranges(line):
    ranges = []
    for m in _URL_RE.finditer(line):
        ranges.append(m.span())
    for m in _HTML_RE.finditer(line):
        ranges.append(m.span())
    for m in _CODE_RE.finditer(line):
        ranges.append(m.span())
    for m in _LINK_RE.finditer(line):
        ranges.append(m.span())
    ranges.sort()
    merged = []
    for s, e in ranges:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return merged

def apply_to_text(text):
    """在非保护区间依次执行 case → typo → punct → spacing。"""
    if not re.search(r"[\u4e00-\u9fffA-Za-z]", text):
        return text
    ranges = protected_ranges(text)
    out = []
    pos = 0
    for s, e in ranges:
        chunk = text[pos:s]
        chunk = fix_case(chunk)
        chunk = fix_typos(chunk)
        chunk = fix_punct(chunk)
        chunk = fix_spacing(chunk)
        out.append(chunk)
        out.append(text[s:e])  # 保护段原样保留
        pos = e
    chunk = text[pos:]
    chunk = fix_case(chunk)
    chunk = fix_typos(chunk)
    chunk = fix_punct(chunk)
    chunk = fix_spacing(chunk)
    out.append(chunk)
    return "".join(out)

def is_fence_marker(line):
    s = line.strip()
    return s.startswith("```") or s.startswith("~~~")

def fix_front_matter(lines, start, end, stats):
    """处理 front matter：仅 title / summary 两个字段的值。返回修改后的行。"""
    out = list(lines)
    for i in range(start, end):
        m = re.match(r"^(title|summary):\s*\"(.*)\"(\s*)$", out[i])
        if not m:
            continue
        key, value, tail = m.group(1), m.group(2), m.group(3)
        new_value = apply_to_text(value)
        if new_value != value:
            out[i] = f'{key}: "{new_value}"{tail}'
            stats["fm_changes"] += 1
    return out

def process_file(path, dry_run):
    with open(path, encoding="utf-8") as fh:
        lines = fh.readlines()
    stats = {"spacing": 0, "case": 0, "punct": 0, "typo": 0, "fm_changes": 0}

    # 定位 front matter（前两行是 ---）
    fm_end = 0
    if len(lines) >= 2 and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                fm_end = i + 1
                break

    lines = fix_front_matter(lines, 0, fm_end, stats)

    in_fence = False
    for i in range(fm_end, len(lines)):
        line = lines[i]
        if is_fence_marker(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if re.match(r"^ {4,}", line):  # 4 空格缩进代码块
            continue
        new = apply_to_text(line)
        if new != line:
            # 统计变更类别
            for m in re.finditer(r"(?<=[\u4e00-\u9fff])[A-Za-z]", line):
                stats["spacing"] += 1
            for m in re.finditer(r"[A-Za-z](?=[\u4e00-\u9fff])", line):
                stats["spacing"] += 1
            for low in CASE_MAP:
                if re.search(r"(?<![" + _BOUNDARY + r"])" + re.escape(low) + r"(?![" + _BOUNDARY + r"])", line):
                    stats["case"] += 1
            stats["punct"] += len(re.findall(r"(?<=[\u4e00-\u9fff])[,;.!?:]", line))
            for old, _ in TYPO_FIXES:
                if old in line:
                    stats["typo"] += 1
            lines[i] = new

    changed = False
    with open(path, encoding="utf-8") as fh:
        orig = fh.read()
    new_content = "".join(lines)
    if new_content != orig:
        changed = True
        if not dry_run:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(new_content)
    return changed, stats


def main():
    dry_run = "--dry-run" in sys.argv
    files = sorted(glob.glob(POSTS))
    total = {"spacing": 0, "case": 0, "punct": 0, "typo": 0, "fm_changes": 0}
    n_changed = 0
    for f in files:
        changed, stats = process_file(f, dry_run)
        if changed:
            n_changed += 1
            for k in total:
                total[k] += stats[k]
            if dry_run:
                print(f"  {f}: 间距{stats['spacing']} 大小写{stats['case']} 标点{stats['punct']} 错字{stats['typo']} front-matter{stats['fm_changes']}")
    print(f"\n{'[dry-run] ' if dry_run else ''}共 {n_changed}/{len(files)} 个文件将被修改")
    print(f"  间距修正: {total['spacing']}")
    print(f"  大小写修正: {total['case']}")
    print(f"  标点修正: {total['punct']}")
    print(f"  错字修正: {total['typo']}")
    print(f"  front-matter 字段修正: {total['fm_changes']}")


if __name__ == "__main__":
    main()
