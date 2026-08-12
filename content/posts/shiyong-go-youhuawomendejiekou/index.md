---
categories: ["后端"]
title: "使用 Go 优化我们的接口"
date: "2019-12-30T19:47:34+08:00"
tags: ["Go", "服务器"]
summary: "特征数据暴增，导致获取一个城市下所有的特征的接口延时高，下面是监控上看到的接口响应耗时，最慢的时候接口响应时间能达到 5s 多。1，使用缓存。分析业务需求，当前需要存储起来的数据是 ObjectId，ObjectId 是一个长度为 14 左右的字符串，我们假设平均下来 Object…"
translationKey: "shiyong-go-youhuawomendejiekou"
---

> 📌 本文原发布于掘金社区：[使用 Go 优化我们的接口](https://juejin.cn/post/6844904034839576590)

标题起的是有点大，不过还好本片文章主要也是使用 Go 来优化 HTTP 服务的，也算打个擦边球吧~

## 背景

特征数据暴增，导致获取一个城市下所有的特征的接口延时高，下面是监控上看到的接口响应耗时，最慢的时候接口响应时间能达到 5s 多。<img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2019/12/30/16f569dfd91758fb~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp#?w=1922&amp;h=714&amp;s=494546&amp;e=png&amp;b=fcfbfb" loading="lazy" alt="cost-time" />

## 缓存优化方案

代码优化思路：

1，使用缓存。

1.1 为什么使用内存，而不是 Redis？

分析业务需求，当前需要存储起来的数据是 ObjectId，ObjectId 是一个长度为 14 左右的字符串，我们假设平均下来 ObjectId 是长度为 16 的字符串，这样算下来就是每个 ObjectId 占用的内存大小是 2 个字节，当前业务需要存储的 ObjectId 大概是 30万条，这样算下来当前业务需要存储的 ObjectId 要占用的内存在 0.5M 完全可以在内存中进行操作。相比于使用 Redis 来说没有网络开销，效率更高。

1.2 缓存初始化：当服务启动时，本地缓存初始化为空。

1.3 关于缓存版本的概念。

缓存版本是离线特征生产任务更新后将数据版本更新到 DB 中。

下面三种方案都是基于内存存储 ObjectId 数据，在内存更新的时候策略有所不同。

### 方案一

2.1 缓存更新

使用主动更新缓存的方式，创建定时任务，每间隔 1分钟查一次 DB 的数据版本，若更新则更新缓存中的数据。

2.2 缺点

单独启动一个缓存更新线程，代码不好维护，也会有定时任务线程挂掉的情况，不易发现。还有就是需要提前把相关参数配置到代码中或者引入配置中心，维护成本较高。

### 方案二

3.1 缓存更新

采用被动触发的缓存更新策略，由接口调用触发。请求进来后检测当前缓存中的数据的版本与 DB 中的数据版本是否一致，若版本更新，则重新读取当前请求对应城市的所有数据到缓存中，并将更新后的数据返回给调用方。

3.2 缺点

由于是被动触发的是同步更新缓存的，容易造成接口调用时如果正好遇上版本更新，需要更新数据到内存中，会出现偶现的毛刺。

3.3 业务执行时序图 <img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2019/12/30/16f569dfdb3e11c7~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp#?w=1494&amp;h=1086&amp;s=355486&amp;e=png&amp;b=fdfefe" loading="lazy" alt="方案二时序图" />

### 方案三（最终采用的方案）

4.1，缓存更新

采用被动更新缓存的策略，由接口调用方触发。若当前缓存中有数据则直接返回缓存中的数据，然后检测当前缓存中的数据的版本与 DB 中的数据版本是否一致，若版本更新，则重新读取当前请求对应城市的所有 feature 数据到缓存中，反之结束缓存更新逻辑。

4.2 业务执行时序图 <img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2019/12/30/16f569dfe2ea3571~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp#?w=1493&amp;h=1075&amp;s=364363&amp;e=png&amp;b=feffff" loading="lazy" alt="方案三时序图" />

## 并发优化方案

### 使用 Goroutine 来优化我们的串行逻辑

Go 语言最大的特色就是从语言层面支持并发（Goroutine），Goroutine 是 Go 中最基本的执行单元。事实上每一个 Go 程序至少有一个 Goroutine：主 Goroutine。当程序启动时，它会自动创建。

为了更好理解 Goroutine，现讲一下线程和协程的概念：

线程（Thread）：有时被称为轻量级进程(Lightweight Process，LWP），是程序执行流的最小单元。一个标准的线程由线程 ID，当前指令指针(PC），寄存器集合和堆栈组成。另外，线程是进程中的一个实体，是被系统独立调度和分派的基本单位，线程自己不拥有系统资源，只拥有一点儿在运行中必不可少的资源，但它可与同属一个进程的其它线程共享进程所拥有的全部资源。

线程拥有自己独立的栈和共享的堆，共享堆，不共享栈，线程的切换一般也由操作系统调度。

协程（coroutine）：又称微线程与子例程（或者称为函数）一样，协程（coroutine）也是一种程序组件。相对子例程而言，协程更为一般和灵活，但在实践中使用没有子例程那样广泛。

和线程类似，共享堆，不共享栈，协程的切换一般由程序员在代码中显式控制。它避免了上下文切换的额外耗费，兼顾了多线程的优点，简化了高并发程序的复杂。

### golang 中的 map 是线程不安全的

很显然，我们可以用锁机制解决 Map 的并发读写问题。我们将上面的 map 结构改成如下：

``` go
// M
type M struct {
    Map    map[string]string
    lock sync.RWMutex // 加锁
}

// Set ...
func (m *M) Set(key, value string) {
    m.lock.Lock()
    defer m.lock.Unlock()
    m.Map[key] = value
}

// Get ...
func (m *M) Get(key string) string {
    return m.Map[key]
}
```

在上面的代码中，我们引入了锁机制操作，从而保证了 map 在多个 goroutine 中的安全。

## 使用策略模式优化我们的逻辑

这块主要是因为代码中存在太多的 if/else，故采用策略模式来优化我们的代码结构。这里先放上一篇网上找到的<a href="https://juejin.im/post/6844903709483204622" target="_blank" title="https://juejin.im/post/6844903709483204622">文章</a>，之后有时间再单独出一篇相关文章吧。优化后的代码相较于之前代码量少了 50%，更加清晰与便于维护。下面是优化的代码上线后的效果，请求耗时都在 100ms 以下：<img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2019/12/30/16f569dfe32850fe~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp#?w=2550&amp;h=678&amp;s=331943&amp;e=png&amp;b=fefdfd" loading="lazy" alt="监控接口耗时" />

## 小结

上面整体介绍了下当我们的接口耗时较长的时候的一般处理方案，当然具体问题还得具体分析，所以当出现接口反应慢的情况的时候，我们应该具体分析接口反应慢的具体原因，方可对症下药！
