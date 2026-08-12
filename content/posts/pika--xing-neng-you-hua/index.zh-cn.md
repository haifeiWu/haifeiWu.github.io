---
title: "Pika 性能优化"
date: "2019-01-09T00:00:00+08:00"
tags: ["Android", "Docker", "Go", "Java", "Kafka", "Kotlin", "MySQL", "Nginx", "Python", "Raft", "Redis", "Shell", "Spring-Boot", "WebFlux", "go", "golang", "netty", "web", "学习笔记", "工具", "性能优化", "性能测试", "总结", "散列表", "旅游日记", "源码", "源码解析", "算法", "设计模式", "译文", "配置中心", "问题排查"]
categories: ["Java"]
summary: "最近在迁移线上 Redis 到 Pika 的过程中，因为业务需要，需要对项目中原有对 pika 读取操作的代码进行优化，最后结果就是读取百万级的数据由原来的30降低到10分钟左右。  Pika 是什么 Pika 是DBA需求，基础架构组开发"
translationKey: "pika--xing-neng-you-hua"
---

{{< include-post "content/posts/pika--xing-neng-you-hua/index.md" >}}
