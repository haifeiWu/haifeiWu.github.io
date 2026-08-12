---
title: "使用 Go 优化我们的接口"
date: "2019-12-30T19:47:34+08:00"
tags: ["Go", "服务器"]
categories: ["后端"]
summary: "特征数据暴增，导致获取一个城市下所有的特征的接口延时高，下面是监控上看到的接口响应耗时，最慢的时候接口响应时间能达到 5s 多。1，使用缓存。分析业务需求，当前需要存储起来的数据是 ObjectId，ObjectId 是一个长度为 14 左右的字符串，我们假设平均下来 Object…"
translationKey: "shiyong-go-youhuawomendejiekou"
---

{{< include-post "content/posts/shiyong-go-youhuawomendejiekou/index.md" >}}
