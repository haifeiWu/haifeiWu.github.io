---
categories: ["后端"]
title: "实时数据并发写入 Redis 优化"
date: "2019-11-12T10:57:02+08:00"
tags: ["Lua", "Redis"]
summary: "当前架构的逻辑是将并发请求数据写入队列中，然后起一个单独的异步线程对数据进行串行处理。这种方式的好处就是不用考虑并发的问题，当然其弊端也是显而易见的~ 根据当前业务的数据更新在秒级，key 的碰撞率较低的情况。笔者打算采用使用 CAS 乐观锁方案：使用 Lua 脚本实现 Red…"
translationKey: "shishishujubingfaxieru-redis-youhua"
---

> 📌 本文原发布于掘金社区：[实时数据并发写入 Redis 优化](https://juejin.cn/post/6844903992519049230)

<a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2019%2Fa5e3%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/article/2019/a5e3/">实时数据并发写入 Redis 优化-原文链接</a>\

对于并发请求如何在不强制加锁的情况下快速更新呢？这里有热腾腾的线上实践……

## 背景

当前架构的逻辑是将并发请求数据写入队列中，然后起一个单独的异步线程对数据进行串行处理。这种方式的好处就是不用考虑并发的问题，当然其弊端也是显而易见的~

## 乐观锁实现数据的并发更新

根据当前业务的数据更新在秒级，`key` 的碰撞率较低的情况。笔者打算采用使用 `CAS` 乐观锁方案：使用 `Lua` 脚本实现 `Redis` 对数据的原子更新，即便是在并发的情况下其性能也会上一个级别。下面是 CAS 乐观锁实现数据并发更新的流程图：

<img src="https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/58f531fd911343ed8479b128211c190f~tplv-k3u1fbpfcp-jj-mark:3024:0:0:0:q75.awebp#?w=367&amp;h=1240&amp;s=51445&amp;e=png&amp;b=fefefe" loading="lazy" alt="image.png" />

根据上面的流程图设计出了 `Lua` 脚本：

``` lua
local keys,values=KEYS,ARGV
local version = redis.call('get',keys[1]) 
if  values[1] == '' and version == false
then
    redis.call('SET',keys[1],'1')
    redis.call('SET',keys[2],values[2])
    return 1
end

if version == values[1]
then
    redis.call('SET',keys[2],values[2])
    redis.call('INCR',keys[1])
    return 1
else
    return 0
end
```

## 可能存在问题及其解决方案

1，在并发冲突概率大的高竞争环境下，如果CAS一直失败，会一直重试，CPU开销较大。针对这个问题的一个思路是引入退出机制，如重试次数超过一定阈值后失败退出。如：

``` go
func main() {
    for i := 0; i < 10; i++ {
        isRetry := execLuaScript()
        if !isRetry {
            break    
        }
    }
}

func execLuaScript() bool {
    ctx := context.Background()
    r := client.GetRedisKVClient(ctx)
    defer r.Close()

    luaScript := `
local keys,values=KEYS,ARGV
local version = redis.call('get',keys[1]) 
if  values[1] == '' and version == false
then
    redis.call('SET',keys[1],'1')
    redis.call('SET',keys[2],values[2])
    return 1
end

if version == values[1]
then
    redis.call('SET',keys[2],values[2])
    redis.call('INCR',keys[1])
    return 1
else
    return 0
end`

    casVersion, err := r.Get("test_version")

    kvs := make([]redis.KeyAndValue, 0)
    kvs = append(kvs, redis.KeyAndValue{"test_version", casVersion.String()})
    kvs = append(kvs, redis.KeyAndValue{"test", "123123123"})
    mv, err := r.Eval(luaScript, kvs...)

    if err != nil {
        log.Errorf("%v", err)
    }

    val, _ := mv.Int64()
    log.Debugf(">>>>>> lua 脚本运行结果 ：%d", val)
    if val == 1 {
        // lua 脚本执行成功，无需重试    
        return false
    } else if val == 0 {
        return true
    }
}
```

2，`Lua` 脚本执行时只能在同一台机器上生效，因此在 `Redis` 集群在就要求相关联的 `key` 分配到相同机器。这里很多同学可能会问为什么，其实很简单，`Redis` 是单线程的，倘若 `Lua` 脚本操作的 `key` 在不同机器上执行，也就无法保证其执行的原子性了。

解决方法还是从分片技术的原理上找： 数据分片，就是一个 `hash` 的过程：对 `key` 做 `md5`，`sha1` 等 `hash` 算法，根据 `hash` 值分配到不同的机器上。

为了实现将key分到相同机器，就需要相同的 `hash` 值，即相同的 `key`（改变 `hash` 算法也行，但比较复杂）。但 `key` 相同是不现实的，因为 `key` 都有不同的用途。但是我们让 `key` 的一部分相同对我们业务实现来说是可以实现的。那么能不能拿 `key` 一部分来计算 `hash` 呢？答案是肯定的，

这就是 <a href="https://link.juejin.cn?target=https%3A%2F%2Fgithub.com%2Ftwitter%2Ftwemproxy%2Fblob%2Fmaster%2Fnotes%2Frecommendation.md%23hash-tags" target="_blank" data-ref="nofollow noopener noreferrer" title="https://github.com/twitter/twemproxy/blob/master/notes/recommendation.md#hash-tags">Hash Tag</a> 。允许用key的部分字符串来计算hash。当一个key包含 {} 的时候，就不对整个key做hash，而仅对 {} 包括的字符串做 hash。假设 hash 算法为sha1。对 user:{user1}:ids和user:{user1}:tweets ，其 hash 值都等同于 sha1(user1)。

## 小结

对于上面的优化过程，目前代码重构开发工作已经完成，但是还未正式上线，等上线之后再来补一下优化之后性能的提升情况~

## 关注我们

<img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2019/11/8/16e498848fb64e35~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp#?w=430&amp;h=430&amp;s=40293&amp;e=jpg&amp;b=ffffff" loading="lazy" alt="关注我们" />
