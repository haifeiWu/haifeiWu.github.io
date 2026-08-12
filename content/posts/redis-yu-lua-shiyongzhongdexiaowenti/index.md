---
categories: ["后端"]
title: "Redis 与 Lua 使用中的小问题"
date: "2019-11-08T13:35:42+08:00"
tags: ["Redis", "Lua"]
summary: "通过上面的脚本可以看到，当 Redis 返回的结果为 (nil) 时候，其真实的数据类型为 boolean，因此我们直接判断 nil 是有问题的。 Redis to Lua conversion table. Lua to Redis conversion table. Lua…"
---

> 📌 本文原发布于掘金社区：[Redis 与 Lua 使用中的小问题](https://juejin.cn/post/6844903990107324423)

## 问题

在 Redis 里执行 `get` 或 `hget` 不存在的 `key` 或 `field` 时返回值在终端显式的是 `(nil)`，类似于下面这样

``` ruby
127.0.0.1:6379> get test_version
(nil)
```

如果在 Lua 脚本中判断获取到的值是否为空值时，就会产生比较迷惑的问题，以为判断空值的话就用 `nil` 就可以了，然鹅事实却并不是这样的，如下所示：

``` csharp
127.0.0.1:6379> get test_version
(nil)
127.0.0.1:6379> EVAL "local a = redis.call('get',KEYS[1]) print(a) if a == 'nil' then return 1 else return 0 end" 1 test_version test_version
(integer) 0
```

我们来看下执行 Lua 脚本返回结果的数据类型是什么

``` ruby
127.0.0.1:6379> get test_version
(nil)
127.0.0.1:6379> EVAL "local a = redis.call('get',KEYS[1]) return type(a)" 1 test_version test_version
"boolean"
```

通过上面的脚本可以看到，当 Redis 返回的结果为 `(nil)` 时候，其真实的数据类型为 `boolean`，因此我们直接判断 `nil` 是有问题的。

## Redis 官方文档

通过翻阅<a href="https://link.juejin.cn?target=https%3A%2F%2Fredis.io%2Fcommands%2Feval" target="_blank" data-ref="nofollow noopener noreferrer" title="https://redis.io/commands/eval">官方文档</a>，找到下面所示的一段话，

**Redis to Lua** conversion table.

- Redis integer reply -\> Lua number
- Redis bulk reply -\> Lua string
- Redis multi bulk reply -\> Lua table (may have other Redis data types nested)
- Redis status reply -\> Lua table with a single ok field containing the status
- Redis error reply -\> Lua table with a single err field containing the error
- Redis Nil bulk reply and Nil multi bulk reply -\> Lua false boolean type

**Lua to Redis** conversion table.

- Lua number -\> Redis integer reply (the number is converted into an integer)
- Lua string -\> Redis bulk reply
- Lua table (array) -\> Redis multi bulk reply (truncated to the first nil inside the Lua array if any)
- Lua table with a single ok field -\> Redis status reply
- Lua table with a single err field -\> Redis error reply
- Lua boolean false -\> Redis Nil bulk reply.

## 解决方案

通过<a href="https://link.juejin.cn?target=https%3A%2F%2Fredis.io%2Fcommands%2Feval" target="_blank" data-ref="nofollow noopener noreferrer" title="https://redis.io/commands/eval">官方文档</a>，我们知道判断 Lua 脚本返回空值使用，应该直接判断 `true/false`，修改判断脚本如下所示

``` csharp
127.0.0.1:6379> get test_version
(nil)
127.0.0.1:6379>  EVAL "local a = redis.call('get',KEYS[1]) if a == false then return 'empty' else return 'not empty' end" 1 test_version test_version
"empty"
```

## 关注我们

<img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2019/11/8/16e498848fb64e35~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp#?w=430&amp;h=430&amp;s=40293&amp;e=jpg&amp;b=ffffff" loading="lazy" alt="关注我们" />
