---
title: "ZooKeeper 与分布式锁"
date: "2021-01-13T11:15:16+08:00"
tags: ["ZooKeeper", "Go"]
categories: ["后端"]
summary: "在上篇文章中讨论了基于 Redis 的单机分布式锁与集群分布式锁的方案，在数据一致性要求不是很高的情况下，Redis 实现的分布式锁可以满足我们的要求。最近在拜读了 ZooKeeper 的论文之后，对于 ZooKeeper 实现的分布式锁，也是有必要了解一下的。使用 Zook…"
translationKey: "zookeeper-yufenbushisuo"
---

{{< include-post "content/posts/zookeeper-yufenbushisuo/index.md" >}}
