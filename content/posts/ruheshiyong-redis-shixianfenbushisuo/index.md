---
categories: ["后端"]
title: "如何使用 Redis 实现分布式锁"
date: "2023-12-19T11:18:09+08:00"
tags: ["后端", "分布式", "Redis"]
summary: "锁是我们在设计和实现大多数系统时绕不过的话题。一旦有竞争条件出现，在没有保护的操作的前提下，可能会出现不可预知的问题。"
translationKey: "ruheshiyong-redis-shixianfenbushisuo"
---

> 📌 本文原发布于掘金社区：[如何使用 Redis 实现分布式锁](https://juejin.cn/post/7313979273974038537)

锁是我们在设计和实现大多数系统时绕不过的话题。一旦有竞争条件出现，在没有保护的操作的前提下，可能会出现不可预知的问题。

而现代系统大多为分布式系统，这就引入了分布式锁，要求具有在分布各处的服务上保护资源的能力。

而实现分布式锁，目前大多有以下三种方式：

- 使用数据库实现。
- 使用 Redis 等缓存系统实现。
- 使用 ZooKeeper 等分布式协调系统实现。

其中 Redis 简便灵活，高可用分布式，且支持持久化。本文即介绍基于 Redis 实现分布式锁。

## SETNX 语义

使用 Redis 实现分布式锁，根本原理是 SETNX 指令。其语义如下：

```
SETNX key value
```

> 命令执行时，如果 `key` 不存在，则设置 `key` 值为 `value`（同`set`）；如果 `key` 已经存在，则不执行赋值操作。并使用不同的返回值标识。<a href="https://link.juejin.cn?target=https%3A%2F%2Fredis.io%2Fcommands%2Fsetnx" target="_blank" data-ref="nofollow noopener noreferrer" title="https://redis.io/commands/setnx">命令描述文档</a>

还可以通过 SET 命令的 NX 选项使用：

``` css
SET key value [expiration EX seconds|PX milliseconds] [NX|XX]
```

> NX - 仅在 key 不存在时执行赋值操作。<a href="https://link.juejin.cn?target=https%3A%2F%2Fredis.io%2Fcommands%2Fset" target="_blank" data-ref="nofollow noopener noreferrer" title="https://redis.io/commands/set">命令描述文档</a> 而如下文所述，通过 SET 的 NX 选项使用，可同时使用其它选项，如 EX/PX 设置超时时间，是更好的方式。

## SETNX 实现分布式锁

下面我们对比下几种具体实现方式。

### 方案 1：SETNX + delete

伪代码如下：

```
setnx lock_a random_value
// do sth
delete lock_a
```

此实现方式的问题在于：一旦服务获取锁之后，因某种原因挂掉，则锁一直无法自动释放。从而导致死锁。

### 方案 2：SETNX + SETEX

伪代码如下：

```
setnx lock_a random_value
setex lock_a 10 random_value // 10s超时
// do sth
delete lock_a
```

按需设置超时时间。此方案解决了方案 1 死锁的问题，但同时引入了新的死锁问题：如果 setnx 之后，setex 之前服务挂掉，会陷入死锁。根本原因为 setnx/setex 分为了两个步骤，非原子操作。

### 方案 3：SET NX PX

伪代码如下：

```
SET lock_a random_value NX PX 10000 // 10s超时
// do sth
delete lock_a
```

此方案通过 set 的 NX/PX 选项，将加锁、设置超时两个步骤合并为一个原子操作，从而解决方案 1、2 的问题。(PX 与 EX 选项的语义相同，差异仅在单位。) 此方案目前大多数 sdk、Redis 部署方案都支持，因此是推荐使用的方式。但此方案也有如下问题：

如果锁被错误的释放（如超时），或被错误的抢占，或因 Redis 问题等导致锁丢失，无法很快的感知到。

### 方案 4：SET key randomvalue NX PX

方案 4 在 3 的基础上，增加对 value 的检查，只解除自己加的锁。类似于 CAS，不过是 compare-and-delete。此方案 Redis 原生命令不支持，为保证原子性，需要通过 lua 脚本实现：。

伪代码如下：

``` css
SET lock_a random_value NX PX 10000
// do sth
eval "if redis.call('get',KEYS[1]) == ARGV[1] then return redis.call('del',KEYS[1]) else return 0 end" 1 lock_a random_value
```

此方案更严谨：即使因为某些异常导致锁被错误的抢占，也能部分保证锁的正确释放。并且在释放锁时能检测到锁是否被错误抢占、错误释放，从而进行特殊处理。

## 注意事项

### 超时时间

从上述描述可看出，超时时间是一个比较重要的变量：

超时时间不能太短，否则在任务执行完成前就自动释放了锁，导致资源暴露在锁保护之外。超时时间不能太长，否则会导致意外死锁后长时间的等待。除非人为接入处理。因此建议是根据任务内容，合理衡量超时时间，将超时时间设置为任务内容的几倍即可。如果实在无法确定而又要求比较严格，可以采用定期 setex/expire 更新超时时间实现。

### 重试

如果拿不到锁，建议根据任务性质、业务形式进行轮询等待。等待次数需要参考任务执行时间。

### 与 Redis 事务的比较

setnx 使用更为灵活方案。multi/exec 的事务实现形式更为复杂。且部分 Redis 集群方案(如 codis)，不支持 multi/exec 事务。
