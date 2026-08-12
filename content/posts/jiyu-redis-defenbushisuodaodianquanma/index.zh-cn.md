---
title: "基于 Redis 的分布式锁到底安全吗？"
date: "2020-02-11T13:18:42+08:00"
tags: ["Redis", "分布式"]
categories: ["后端"]
summary: "4，那么部署 Redis 的主从可以保证吗？主要原因是 Redis 主节点与从节点之间的数据同步是异步的。Redlock 算法是基于 N 个完全独立的 Redis 节点（通常情况下 N 可以设置成 5）。1，获取当前时间（毫秒数）。2，按顺序依次向 N 个 Redis 节…"
translationKey: "jiyu-redis-defenbushisuodaodianquanma"
---

{{< include-post "content/posts/jiyu-redis-defenbushisuodaodianquanma/index.md" >}}
