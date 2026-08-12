---
aliases: ["/zh-cn/posts/kafka-de-ri-zhi-fu-zhi-ji-zhi/"]
categories: ["Java"]
title: "Kafka 的日志复制机制"
date: "2021-01-14T00:00:00+08:00"
tags: ["Kafka", "分布式", "源码"]
summary: "Kafka 是一个分布式的发布 订阅消息系统。它最初是在 LinkedIn 开发的，2011年7月成为一个 Apache 项目。今天，Kafka 被 LinkedIn、Twitter 和 Square 用于日志聚合、队列、实时监控和事件处"
translationKey: "kafka-de-ri-zhi-fu-zhi-ji-zhi"
---

> 📌 本文原发布于代码星冰乐：[Kafka 的日志复制机制](https://changhuin.github.io/article/2021/7cba/)

Kafka 是一个分布式的发布-订阅消息系统。它最初是在 LinkedIn 开发的，2011年7月成为一个 Apache 项目。今天，Kafka 被 LinkedIn、Twitter 和 Square 用于日志聚合、队列、实时监控和事件处理等应用程序。在下面的文章中，我们将讨论 Kafka 的 replication 设计。\

replication 的目的是提供服务的高可用，即使有些节点失败了，Producer 可以继续发布消息，Consumer 可以继续接收消息。

## 保证数据一致性的方式

有两种典型的方式来保证数据的强一致。这两种方式都要求指定一个 leader，所有的写都是发送给 leader。leader 负责接收所有的写请求，并以相同的顺序将这些写传播给其他 follower。

### 多数复制

基于多数提交的方式。leader 要等到大多数 follower 接收到数据之后才认为数据是可提交的。在 leader 失败的情况下，通过多数 follower 的协调选出新的 leader。这种方式的算法有 raft、paxos 等，比如 ZooKeeper、Google Spanner、etcd 等。这种方式在有 2n + 1 个节点的情况下，最多可以容忍 n 个节点失败。

### 主从复制

基于主从复制的方式。需要等 leader 和 follower 都写入成功才算消息接收成功，在有 n 个节点的情况下，最多可以容忍 n-1 个节点失败。

Kafka 使用主从复制的方式来实现集群之间的日志复制。原因如下：

基于主从复制的方式可以在相同数量的副本中容忍更多故障。也就是说，它可以容忍带有 n + 1 个副本的 n 个故障，而基于多数复制的方式通常只能容忍带有 2n +1 个副本的 n 个故障。例如，如果只有 2 个副本，则基于多数复制的方式不能容忍任何故障。\
Kafka 的日志复制主要考虑的是同一个数据中心的机器之间的数据复制，相对来说延迟并不会成为日志复制的瓶颈。

## 几个概念

在 Kafka 中，消息流是由 topic 定义的，topic 被划分为一个或多个 partition。而复制发生在 partition 级别，每个 partition 都有一个或多个副本。
> 📷 图注：topic 的逻辑关系
> 📷 图注：topic 的屋里存储关系

在 Kafka 集群中，将副本均匀地分配到不同的 broker 上。每个副本都在磁盘上维护一个日志。发布的消息按顺序附加到日志中，每条消息都通过日志中的单调递增 offset 来标识。\
offset 是分区中的逻辑概念。给定一个 offset，可以在每个分区副本中标识相同的消息。当 consumer 订阅某个主题时，它会跟踪每个分区中用于消费的偏移量，并使用它向 broker 发出读取请求。\
\
如上图所示当 producer 将消息发布到 topic 的某个 partition 时，该消息首先被转发到该 partition 的 leader 副本，并追加到其日志中。follower 的副本不断地从 leader 那里获取新的信息。一旦有足够多的副本接收到消息，leader 就提交消息。\
有个问题是 leader 如何决定到什么程度是足够的。leader 不能总是等待所有副本的写操作完成。这样为了保证数据一致性而降低我们服务的可用性是不可行的，这是因为任何跟随者副本可以失败，而领导者不能无限地等待。

## Kafka 的 ISR 模型

为了解决上面提出的问题，Kafka 采用了一种折中的方案，引入了 ISR 的概念。ISR 是 in-sync replicas 的简写。ISR 的副本保持和 leader 的同步，当然 leader 本身也在 ISR 中。初始状态所有的副本都处于 ISR 中，当一个消息发送给 leader 的时候，leader 会等待 ISR 中所有的副本告诉它已经接收了这个消息，如果一个副本失败了，那么它会被移出 ISR。下一条消息来的时候，leader 就会将消息发送给当前 ISR 中的节点了。

同时，leader 还维护着 HW(high watermark),这是一个分区的最后一条消息的 offset。HW 会被持续地发送给 follower，broker 可以将它写入到磁盘中以便将来恢复。

当一个失败的副本重启的时候，它首先恢复磁盘中记录的 HW，然后将它的消息同步到 HW 这个 offset。这是因为 HW 之后的消息不保证已经 commit。这时它变成了一个 follower，从 HW 开始，从 Leader 中同步数据，一旦追上 leader，它就可以再加入到 ISR 中。

Kafka 使用 ZooKeeper 实现 leader 选举。如果 leader 失败，controller 会从 ISR 选出一个新的 leader。leader 选举的时候可能会有数据丢失，但是 committed 的消息保证不会丢失。

故障恢复，leader 重新选举的表述~

## 数据一致性与服务可用性的权衡

为了保证数据的一致性，Kafka 提出了 ISR，在同步日志到 follower 的时候为了提高服务的可用性，follower 在将 leader 同步的日志写入内存后就返回给 leader 日志写入成功的标志。然后这些操作都是可以通过 Kafka 的配置来实现的。

## 参考文档

- <a href="https://kafka.apache.org/documentation/#replication" target="_blank" rel="noopener">https://kafka.apache.org/documentation/#replication</a>
- <a href="https://colobu.com/2017/11/02/kafka-replication/" target="_blank" rel="noopener">https://colobu.com/2017/11/02/kafka-replication/</a>
- <a href="https://engineering.linkedin.com/kafka/intra-cluster-replication-apache-kafka" target="_blank" rel="noopener">https://engineering.linkedin.com/kafka/intra-cluster-replication-apache-kafka</a>
- <a href="https://cwiki.apache.org/confluence/display/KAFKA/kafka+Detailed+Replication+Design+V3" target="_blank" rel="noopener">https://cwiki.apache.org/confluence/display/KAFKA/kafka+Detailed+Replication+Design+V3</a>

