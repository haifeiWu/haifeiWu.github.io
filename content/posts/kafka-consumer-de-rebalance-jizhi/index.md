---
categories: ["后端"]
title: "Kafka Consumer 的 Rebalance 机制"
date: "2019-11-19T16:22:34+08:00"
tags: ["Java", "Kafka"]
summary: "如上图所示，Consumer 使用 Consumer Group 名称标记自己，并且发布到主题的每条记录都会传递到每个订阅消费者组中的一个 Consumer 实例。Consumer 实例可以在单独的进程中或在单独的机器上。如果所有 Consumer 实例都属于同一个 Con…"
translationKey: "kafka-consumer-de-rebalance-jizhi"
---

> 📌 本文原发布于掘金社区：[Kafka Consumer 的 Rebalance 机制](https://juejin.cn/post/6844904000479821832)

<a href="https://link.juejin.cn?target=https%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2019%2Fdb6d%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="https://www.hchstudio.cn/article/2019/db6d/">Kafka Consumer 的 Rebalance 机制-原文链接</a>\
<a href="https://link.juejin.cn?target=https%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2019%2Fdb6d%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="https://www.hchstudio.cn/article/2019/db6d/">Kafka Consumer 的 Rebalance 机制-原文链接</a>\
<a href="https://link.juejin.cn?target=https%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2019%2Fdb6d%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="https://www.hchstudio.cn/article/2019/db6d/">Kafka Consumer 的 Rebalance 机制-原文链接</a>\

上周参加了 Kafka Meetup 北京站的技术分享，本文简单介绍下 Kafka Consumer 的 Rebalance 机制以及其新版本中的优化策略~

## Kafka 之前版本的 Consumer Groups

### Consumer Group

<figure>
<img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2019/11/19/16e82bf2d623075e~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp" loading="lazy" />
</figure>

如上图所示，`Consumer` 使用 `Consumer Group` 名称标记自己，并且发布到主题的每条记录都会传递到每个订阅消费者组中的一个 `Consumer` 实例。`Consumer` 实例可以在单独的进程中或在单独的机器上。

如果所有 `Consumer` 实例都属于同一个 `Consumer Group`，那么这些 `Consumer` 实例将以负载均衡的方式来消费 `Kafka`。

如果所有 `Consumer` 实例具有不同的 `Consumer Group`，则每条记录将被广播到所有 `Consumer` 进程。

### Group Coordinator

`Group Coordinator` 是一个服务，每个 `Broker`在启动的时候都会启动该服务。`Group Coordinator` 的作用是存储 `Group` 的相关 `Meta` 信息，并将对应 `Partition` 的 `Offset` 信息记录到 `Kafka` 内置`Topic(__consumer_offsets)` 中。`Kafka` 在 0.9 之前是基于 `Zookeeper` 来存储 `Partition` 的 `Offset` 信息 `(consumers/{group}/offsets/{topic}/{partition})`，因为 `Zookeeper` 并不适用于频繁的写操作，所以在 0.9 之后通过内置 `Topic` 的方式来记录对应 `Partition` 的 `Offset`。如下图所示：

在 `Kafka 0.8.2` 之前是这样的

<figure>
<img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2019/11/19/16e82bf3544f43ee~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp" loading="lazy" />
</figure>

之后是这样的：

<figure>
<img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2019/11/19/16e82bf30624d9dc~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp" loading="lazy" />
</figure>

每个 `Group` 都会选择一个 `Coordinator` 来记录自己组内各 `Partition` 的 `Offset` 信息，选择的规则如下：

1.  计算 `Group` 对应在 `__consumer_offsets` 上的 `Partition`
2.  根据对应的 Partition 寻找该 Partition 的 leader 所对应的 Broker，该 Broker 上的 Group Coordinator 就是该 Group 的 Coordinator

Partition 计算规则：

``` bash
partition-Id(__consumer_offsets) = Math.abs(groupId.hashCode() % groupMetadataTopicPartitionCount)
```

其中 `groupMetadataTopicPartitionCount` 对应 `offsets.topic.num.partitions` 参数值，默认值是 50 个分区

## Consumer Rebalance Protocol

### 发生 rebalance 的时机

1.  组成员个数发生变化。例如有新的 `consumer` 实例加入该消费组或者离开组。
2.  订阅的 `Topic` 个数发生变化。
3.  订阅 `Topic` 的分区数发生变化。

### 消费者进程挂掉的情况

1.  `session` 过期
2.  `heartbeat` 过期

`Rebalance` 发生时，`Group` 下所有 `Consumer` 实例都会共同参与，`Kafka` 能够保证尽量达到最公平的分配。但是 `Rebalance` 过程对 `Consumer Group` 会造成比较严重的影响。在 `Rebalance` 的过程中 `Consumer Group` 下的所有消费者实例都会停止工作，等待 `Rebalance` 过程完成。

## 消费者的 Rebalance 协议

### Rebalance 发生后的执行过程

1，有新的 `Consumer` 加入 `Consumer Group`

2，从 `Consumer Group` 选出 `leader`

3，`leader` 进行分区的分配

### Issues

Known Issue \#1: Stop-the-world Rebalance

<figure>
<img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2019/11/19/16e82bf309b51c0b~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp" loading="lazy" />
</figure>

如上图所示：之前版本的 `Kafka` 在发生 `Rebalance` 的时候会释放 `Consumer Group` 的所有资源，造成比较长的 `Stop-the-world`

Known Issue \#2: Back-and-forth Rebalance

<figure>
<img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2019/11/19/16e82bf352865c95~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp" loading="lazy" />
</figure>

如上图所示：在发生 `Rebalance` 的时候发生了不必要的资源释放与重新分配。

## 当前的 Rebalance 与 改进后的 ReBalance 对比

<figure>
<img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2019/11/19/16e82bf222819b78~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp" loading="lazy" />
</figure>

## 渐进式 Rebalance 协议

<figure>
<img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2019/11/19/16e82bf267963509~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp" loading="lazy" />
</figure>

如上图所示，新的渐进式 Rebalance 协议，在 Rebalance 的时候不需要当前所有的 Consumer 释放所拥有的资源，而是当需要触发 Rebalance 的时候对当前资源进行登记，然后进行渐进式的 Rebalance。这样做产生的优化效果如下

- 相较之前进行了更多次数的 Rebalance，但是每次 Rebalance 对资源的消耗都是比较廉价的
- 发生迁移的分区相较之前更少了
- Consumer 在 Rebalance 期间可以继续运行

## 参考文章

- <a href="https://link.juejin.cn?target=https%3A%2F%2Fwww.confluent.io%2Fblog%2Fincremental-cooperative-rebalancing-in-kafka" target="_blank" data-ref="nofollow noopener noreferrer" title="https://www.confluent.io/blog/incremental-cooperative-rebalancing-in-kafka">Incremental Cooperative Rebalancing in Apache Kafka: Why Stop the World When You Can Change It?</a>
- <a href="https://link.juejin.cn?target=https%3A%2F%2Fcwiki.apache.org%2Fconfluence%2Fdisplay%2FKAFKA%2FKIP-429%253A%2BKafka%2BConsumer%2BIncremental%2BRebalance%2BProtocol" target="_blank" data-ref="nofollow noopener noreferrer" title="https://cwiki.apache.org/confluence/display/KAFKA/KIP-429%3A+Kafka+Consumer+Incremental+Rebalance+Protocol">KIP-429: Kafka Consumer Incremental Rebalance Protocol</a>
- <a href="https://link.juejin.cn?target=https%3A%2F%2Fcwiki.apache.org%2Fconfluence%2Fdisplay%2FKAFKA%2FIncremental%2BCooperative%2BRebalancing%253A%2BSupport%2Band%2BPolicies" target="_blank" data-ref="nofollow noopener noreferrer" title="https://cwiki.apache.org/confluence/display/KAFKA/Incremental+Cooperative+Rebalancing%3A+Support+and+Policies">Incremental Cooperative Rebalancing: Support and Policies</a>

## 关注我们

<figure>
<img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2019/11/8/16e498848fb64e35~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp" loading="lazy" alt="关注我们" />
</figure>
