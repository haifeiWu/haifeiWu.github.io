---
title: "Kafka Consumer 的 Rebalance 机制"
date: "2019-11-19T16:22:34+08:00"
tags: ["Java", "Kafka"]
categories: ["后端"]
summary: "如上图所示，Consumer 使用 Consumer Group 名称标记自己，并且发布到主题的每条记录都会传递到每个订阅消费者组中的一个 Consumer 实例。 Consumer 实例可以在单独的进程中或在单独的机器上。 如果所有 Consumer 实例都属于同一个 Con…"
translationKey: "kafka-consumer-de-rebalance-jizhi"
---

{{< include-post "content/posts/kafka-consumer-de-rebalance-jizhi/index.md" >}}
