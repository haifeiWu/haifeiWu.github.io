---
categories: ["后端"]
title: "基于 Redis 的分布式锁到底安全吗？"
date: "2020-02-11T13:18:42+08:00"
tags: ["Redis", "分布式"]
summary: "4，那么部署 Redis 的主从可以保证吗？主要原因是 Redis 主节点与从节点之间的数据同步是异步的。Redlock 算法是基于 N 个完全独立的 Redis 节点（通常情况下 N 可以设置成 5）。1，获取当前时间（毫秒数）。2，按顺序依次向 N 个 Redis 节…"
translationKey: "jiyu-redis-defenbushisuodaodianquanma"
---

> 📌 本文原发布于掘金社区：[基于 Redis 的分布式锁到底安全吗？](https://juejin.cn/post/6844904062723293198)

## 单机 Redis 实现的分布式锁

1，单机实现分布式锁的脚本（官方推荐实现）

``` bash
SET lock_key random_value NX PX 10000
// do sth
eval "if redis.call("get",KEYS[1]) == ARGV[1] then
          return redis.call("del",KEYS[1])
      else
          return 0
      end"
```

2，注意事项（对释放锁的控制，以及锁超时的控制）：random_value 要保证唯一，可以用 trace_id 来保证！\
3，存在的问题：单机 Redis 只是依赖单台 Redis，当依赖的 Redis 挂掉之后会造成比较大的问题！\
4，那么部署 Redis 的主从可以保证吗？主要原因是 Redis 主节点与从节点之间的数据同步是异步的。

## 分布式 Redis 实现的分布式锁

### Redlock 算法

Redlock 算法是基于 N 个完全独立的 Redis 节点（通常情况下 N 可以设置成 5）。\
1，获取当前时间（毫秒数）。

2，按顺序依次向 N 个 Redis 节点执行获取锁的操作。这个获取操作跟基于单 Redis 节点的获取锁的过程相同。为了保证在某个 Redis 节点不可用的时候算法能够继续运行，这个获取锁的操作还有一个超时时间(time out)，它要远小于锁的有效时间（几十毫秒量级）。客户端在向某个 Redis 节点获取锁失败（**比如该 Redis 节点不可用，或者该 Redis 节点上的锁已经被其它客户端持有**）以后，应该立即尝试下一个 Redis 节点。

3，计算整个获取锁的过程总共消耗了多长时间，计算方法是用当前时间减去第 1 步记录的时间。如果客户端从大多数 Redis 节点（\>= N/2+1）成功获取到了锁，并且获取锁总共消耗的时间没有超过锁的有效时间(lock validity time)，那么这时客户端才认为最终获取锁成功；否则，认为最终获取锁失败。

4，如果最终获取锁成功了，那么这个锁的有效时间应该重新计算，它等于最初的锁的有效时间减去第 3 步计算出来的获取锁消耗的时间。

5，如果最终获取锁失败了（**可能由于获取到锁的 Redis 节点个数少于 N/2+1，或者整个获取锁的过程消耗的时间超过了锁的最初有效时间**），那么客户端应该立即向所有 Redis 节点发起释放锁的操作（以保证所有 Redis 节点上已获取的锁都能被释放掉）。

Redlock 算法实现的前提是假设不同的机器具有相同的时钟，或者误差很小，可以忽略不计。(**这也是 DDIA 作者喷的一点**)

存在的问题：1，关于 Redis 的持久化的问题：假设一共有 5 个 Redis 节点：A, B, C, D, E。设想发生了如下的事件序列：\
1.1 客户端 1 成功锁住了 A, B, C，获取锁成功（但 D 和 E 没有锁住）。\
1.2 节点 C 崩溃重启了，但客户端 1 在 C 上加的锁没有持久化下来，丢失了。\
1.3 节点 C 重启后，客户端 2 锁住了 C, D, E，获取锁成功。\

**Redis 给出的解决方案：延迟重启，即当 Redis 节点挂掉之后不要立刻重启，而要等待一个锁的过期时间之后再重启。**

2，如果获取锁消耗的时间过多以至于无法完成后续的操作，如何释放锁？个人认为需要业务方自己拿捏一个业务操作需要消耗的时长，

3，Redis 作者在设计 Redlock 的时候，是充分考虑了网络延迟和程序停顿所带来的影响的。但是，对于客户端和资源服务器之间的延迟（即发生在算法第 3 步之后的延迟），他承认所有的分布式锁的实现，包括 Redlock，是没有什么好办法来应对的。

### DDIA 作者对于 Redlock 的观点

在 Martin 的这篇文章中，他把锁的用途分为两种：

- 为了效率(efficiency)，协调各个客户端避免做重复的工作。即使锁偶尔失效了，只是可能把某些操作多做一遍而已，不会产生其它的不良后果。比如重复发送了一封同样的 email。
- 为了正确性(correctness)。在任何情况下都不允许锁失效的情况发生，因为一旦发生，就可能意味着数据不一致(inconsistency)，数据丢失，文件损坏，或者其它严重的问题。

1，带有自动过期功能的分布式锁，必须提供某种 fencing 机制来保证对共享资源的真正的互斥保护。Redlock 提供不了这样一种机制。

<figure>
<img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2020/2/11/17032abfaf961a16~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp" loading="lazy" />
</figure>

上图展示的是：由于 GC 停顿造成的共享资源被多个客户端访问的问题。原因是：客户端因 GC 停顿造成锁的等待超时，从而被释放，然而客户端并不知道，认为自己还是处于持有锁的状态。

<figure>
<img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2020/2/11/17032abfafabdba9~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp" loading="lazy" />
</figure>

上图展示的是：通过使用 fencing tokens 来解决锁失效未释放的问题。Redis 指出上图的漏洞，如果客户端 1 和客户端 2 都发生了 GC pause，两个 fencing token 都延迟了，它们几乎同时到达了资源服务器，但保持了顺序，那么资源服务器是不是就检查不出问题了？这时对于资源的访问是不是就发生冲突了？

2，Redlock 构建在一个不够安全的系统模型之上。它对于系统的计时假设(timing assumption)有比较强的要求，而这些要求在现实的系统中是无法保证的。Redlock 算法对机器时钟有强依赖，Martin 认为算法的实现不应该对时序做任何假设：进程可能会暂停任意时长，数据包可能会在网络中被任意延迟，时钟可能会任意出错，即便如此，该算法仍可以正确执行并给出正确结果。\
关于时钟的不可靠性：Redis 作者认为 Redlock 对时钟的要求，并不需要完全精确，它只需要时钟差不多精确就可以了。

3，在 Redlock 第三步完成之后的网络延迟，也可能造成 Redlock 算法的失效，但是这个问题并不是 Redlock 算法独有的

Martin 得出了如下的结论：

- 如果是为了效率(efficiency)而使用分布式锁，允许锁的偶尔失效，那么使用单 Redis 节点的锁方案就足够了，简单而且效率高。Redlock 则是个过重的实现(heavy weight)。
- 如果是为了正确性(correctness)在很严肃的场合使用分布式锁，那么不要使用 Redlock。它不是一个建立在异步模型上的足够强的算法，它对于系统模型的假设中包含很多危险的成分(对于 timing)。而且，它没有一个机制能够提供 fencing token。那应该使用什么技术呢？Martin 认为，应该考虑类似 ZooKeeper 的方案，或者支持事务的数据库。

## 最后的讨论

在了解了 Redlock 算法的逻辑及其可能存在的问题之后，我们可以针对自己的业务场景进行选择~

## 参考

<a href="https://link.juejin.cn?target=https%3A%2F%2Fmartin.kleppmann.com%2F2016%2F02%2F08%2Fhow-to-do-distributed-locking.html" target="_blank" data-ref="nofollow noopener noreferrer" title="https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html">How to do distributed locking</a>

<a href="https://link.juejin.cn?target=http%3A%2F%2Fantirez.com%2Fnews%2F101" target="_blank" data-ref="nofollow noopener noreferrer" title="http://antirez.com/news/101">Is Redlock safe?</a>

<a href="https://link.juejin.cn?target=https%3A%2F%2Fredis.io%2Ftopics%2Fdistlock" target="_blank" data-ref="nofollow noopener noreferrer" title="https://redis.io/topics/distlock">Distributed locks with Redis</a>

## 关注我们

<figure>
<img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2019/12/23/16f330eaf05c368d~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp" loading="lazy" alt="关注我们" />
</figure>
