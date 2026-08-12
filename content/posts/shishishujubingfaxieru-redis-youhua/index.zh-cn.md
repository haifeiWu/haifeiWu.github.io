---
title: "实时数据并发写入 Redis 优化"
date: "2019-11-12T10:57:02+08:00"
tags: ["Lua", "Redis"]
categories: ["后端"]
summary: "当前架构的逻辑是将并发请求数据写入队列中，然后起一个单独的异步线程对数据进行串行处理。这种方式的好处就是不用考虑并发的问题，当然其弊端也是显而易见的~ 根据当前业务的数据更新在秒级，key 的碰撞率较低的情况。笔者打算采用使用 CAS 乐观锁方案：使用 Lua 脚本实现 Red…"
translationKey: "shishishujubingfaxieru-redis-youhua"
---

{{< include-post "content/posts/shishishujubingfaxieru-redis-youhua/index.md" >}}
