---
categories: ["后端"]
title: "Kafka的Replica机制"
date: "2021-05-12T12:19:58+08:00"
tags: ["后端", "Kafka", "Java"]
summary: "Kafka 是一个分布式的发布-订阅消息系统。它最初是在 LinkedIn 开发的，2011年7月成为一个 Apache 项目。"
---

> 📌 本文原发布于掘金社区：[Kafka的Replica机制](https://juejin.cn/post/6961253310233837599)

Kafka 是一个分布式的发布-订阅消息系统。它最初是在 LinkedIn 开发的，2011年7月成为一个 Apache 项目。今天，Kafka 被 LinkedIn、 Twitter 和 Square 用于日志聚合、队列、实时监控和事件处理等应用程序。在下面的文章中，我们将讨论下 Kafka 的 replication 设计。

replication 的目的是为了提供服务的高可用， 即使有些节点出现了失败，Producer可以继续发布消息，Consumer可以继续接收消息。

## 保证数据一致性的方式

有两种典型的方式来保证数据的强一致。这两种方式都要求指定一个leader，所有的写都是发送给leader。leader负责接收所有的写请求，并以相同的顺序将这些写传播给其他follower。

### 多数复制

基于多数提交的方式。leader 要等到大多数 fellower 接收到数据之后才认为数据是可提交的状态。在 leader 失败的情况下，通过多数 fellower 的协调选出新的 leader 。这种方式的算法有raft、paxos等算法， 比如Zookeeper、 Google Spanner、etcd等。这种方式在有 2n + 1个节点的情况下，最多可以容忍n个节点失败。

### 主从复制

基于主从复制的方式。需要等 leader 和 fellower 都写入成功才算消息接收成功， 在有n个节点的情况下，最多可以容忍n-1节点失败。

Kafka使用的是主从复制的方式来实现集群之间的日志复制。原因如下：

基于主从复制的方式可以在相同数量的副本中容忍更多故障。 也就是说，它可以容忍带有 n + 1个副本的 n 个故障，而基于多数复制的方式通常只能容忍带有2n +1个副本的n个故障。 例如，如果只有2个副本，则基于多数复制的方式不能容忍任何故障。 Kafka的日志复制主要考虑的是同一个数据中心机器之间的数据复制，相对来说延迟并不会成为日志复制的瓶颈。

## 几个概念

在 Kafka 中，消息流是由 topic 定义的，topic被划分为一个或多个partition。而复制发生在 partition 级别，每个 partition 都有一个或多个副本（replica）。 <img src="https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/6da05f7449b54d34bde097018e543a06~tplv-k3u1fbpfcp-zoom-in-crop-mark:1512:0:0:0.awebp?" style="width:70.0%" loading="lazy" alt="topic的逻辑关系" />

在 Kafka 集群中，将副本均匀地分配到不同的broker上，每个副本都在磁盘上维护一个日志。发布的消息按顺序附加到日志中，每条消息都通过日志中的单调递增offset来标识。 offset 是分区中的逻辑概念。给定一个offset，可以在每个分区副本中标识相同的消息。当 consumer 订阅某个主题时，它会跟踪每个分区中用于消费的偏移量，并使用它向 broker 发出读取请求。

<img src="https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/1176ac165a9642148c5c7a3fdcb787bf~tplv-k3u1fbpfcp-zoom-in-crop-mark:1512:0:0:0.awebp" style="width:100.0%" loading="lazy" alt="kafka_replication_diagram.png" />

如上图所示当 producer 将消息发布到topic的某个 partition 时，该消息首先被转发到该 partition 的leader副本，并追加到其日志中。fellower 的副本不断地从 leader 那里获取新的信息。一旦有足够多的副本接收到消息，leader 就提交消息。 有个问题就是说 leader 如何决定到什么程度是足够的。leader 不能总是等待所有副本的写操作完成。这样为了保证数据一致性而降低我们服务的可用性是不可行的，这是因为任何跟随者副本可以失败和领导者不能无限地等待。那么如何解决这个问题呢？kafka 为了解决这种情况下出现的问题，提出了一种新的解决方案ISR，下面是ISR的详细介绍。

## Kafka的ISR模型

为了解决上面提出的问题，Kafka采用了一种折中的方案，引入了 ISR的概念。ISR是in-sync replicas的简写。ISR的副本保持和leader的同步，当然leader本身也在ISR中。初始状态所有的副本都处于ISR中，当一个消息发送给leader的时候，leader会等待ISR中所有的副本告诉它已经接收了这个消息，如果一个副本失败了，那么它会被移除ISR。下一条消息来的时候，leader就会将消息发送给当前的ISR中节点了。

同时，leader还维护着HW(high watermark)，这是一个分区的最后一条消息的offset。leader会持续的将HW发送给fellower，broker可以将它写入到磁盘中以便将来恢复。

当一个失败的副本重启的时候，它首先恢复磁盘中记录的HW，然后将它的消息同步到HW这个offset。这是因为HW之后的消息不保证已经commit。这时它变成了一个fellower， 从HW开始从Leader中同步数据，一旦追上leader，它就可以重新加入到ISR中。

kafka使用Zookeeper实现leader选举。如果leader失败，controller会从ISR选出一个新的leader。leader 选举的时候可能会有数据丢失，但是已经提交的消息保证不会丢失。

## 数据一致性与服务可用性的权衡

为了保证数据的一致性，Kafka提出了ISR，在同步日志到 fellower 的时候为了提高服务的可用性，fellow在将leader同步的日志写入内存后就返回给leader日志写入成功的标志。然后这些操作都是可以通过Kafka的配置来实现的。

## 参考文档

- <a href="https://link.juejin.cn?target=https%3A%2F%2Fkafka.apache.org%2Fdocumentation%2F%23replication" target="_blank" data-ref="nofollow noopener noreferrer" title="https://kafka.apache.org/documentation/#replication">kafka.apache.org/documentati…</a>
- <a href="https://link.juejin.cn?target=https%3A%2F%2Fcolobu.com%2F2017%2F11%2F02%2Fkafka-replication%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="https://colobu.com/2017/11/02/kafka-replication/">colobu.com/2017/11/02/…</a>
- <a href="https://link.juejin.cn?target=https%3A%2F%2Fengineering.linkedin.com%2Fkafka%2Fintra-cluster-replication-apache-kafka" target="_blank" data-ref="nofollow noopener noreferrer" title="https://engineering.linkedin.com/kafka/intra-cluster-replication-apache-kafka">engineering.linkedin.com/kafka/intra…</a>
- <a href="https://link.juejin.cn?target=https%3A%2F%2Fcwiki.apache.org%2Fconfluence%2Fdisplay%2FKAFKA%2Fkafka%2BDetailed%2BReplication%2BDesign%2BV3" target="_blank" data-ref="nofollow noopener noreferrer" title="https://cwiki.apache.org/confluence/display/KAFKA/kafka+Detailed+Replication+Design+V3">cwiki.apache.org/confluence/…</a>
