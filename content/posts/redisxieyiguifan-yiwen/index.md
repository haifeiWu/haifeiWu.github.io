---
categories: ["后端"]
title: "Redis 协议规范（译文）"
date: "2018-08-08T00:57:50+08:00"
tags: ["Redis", "后端", "Java", "服务器"]
summary: "Redis 客户端使用名为 RESP（Redis 序列化协议）的协议与 Redis 服务器进行通信。虽然该协议是专为 Redis 设计的，但它可以用于其他 CS 软件项目的通讯协议。RESP 可以序列化不同的数据类型，如整型，字符串，数组。还有一种特定的错误类型。请求将要执行的命令作为字符…"
---

> 📌 本文原发布于掘金社区：[Redis 协议规范（译文）](https://juejin.cn/post/6844903653141118983)

> 原文地址：<a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2F%3F_ref%3Djuejin" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/?_ref=juejin">haifeiWu 的博客</a>\
> 博客地址：<a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2018%2Fe687%2F%3F_ref%3Djuejin" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/article/2018/e687/?_ref=juejin">www.hchstudio.cn</a>\
> 欢迎转载，转载请注明作者及出处，谢谢！

Redis 客户端使用名为 RESP（Redis 序列化协议）的协议与 Redis 服务器进行通信。虽然该协议是专为 Redis 设计的，但它也可以用作其他 CS 软件项目的通信协议。

RESP 的设计考虑了以下几个方面：

- 易于实现
- 快速解析
- 可读性高

RESP 可以序列化不同的数据类型，如整型，字符串，数组。还有一种特定的错误类型。请求将要执行的命令作为字符串数组从 Redis 客户端发送到 Redis 服务器。Redis 使用特定数据类型进行回复。

RESP 是二进制安全的，不需要处理从一个进程传输到另一个进程的批量数据，因为它使用前缀长度来传输批量数据。

**注意：** 此处概述的协议仅用于客户端 - 服务器通信。Redis Cluster 使用不同的二进制协议，以便在节点之间交换消息。

## 网络层

客户端连接到 Redis 服务器，即创建一个到端口 6379 的 TCP 连接。虽然 RESP 在技术上是非 TCP 特定的，但在 Redis 的上下文中，协议仅用于 TCP 连接（或类似的面向流的连接，如 Unix 套接字）。\

## 请求 - 响应模型

Redis 接受由不同参数组成的命令。收到命令后，将对其进行处理并将回复发送回客户端。这是最简单的模型，但有两个例外：

- Redis 支持流水线操作（本文档稍后介绍）。因此，客户端可以一次发送多个命令，并等待稍后的回复。
- 当 Redis 客户端处于 Pub/Sub 时，协议会更改语义并成为推送协议，即客户端不再需要发送命令，因为服务器会在它们接收到命令时自动向客户端发送新消息。

排除上述两个例外，Redis 协议是一个简单的请求 - 响应协议。\

## RESP 协议描述

RESP 协议在 Redis 1.2 中引入，但它成为与 Redis 2.0 中的 Redis 服务器通信的标准方式。这是每一个 Redis 客户端都应该实现的协议。

RESP 实际上是一个支持以下数据类型的序列化协议：单行字符串，错误信息，整型，多行字符串和数组。RESP 在 Redis 中用作请求 - 响应协议的方式如下：

- 客户端将命令作为字符串数组发送到 Redis 服务器。
- 服务器根据命令回复一种 RESP 类型的数据。

在 RESP 中，一些数据的类型通过它的第一个字节进行判断：

- 单行回复：回复的第一个字节是 "+"

- 错误信息：回复的第一个字节是 "-"

- 整形数字：回复的第一个字节是 ":"

- 多行字符串：回复的第一个字节是 "\$"

- 数组：回复的第一个字节是 "\*"

此外，RESP 能够使用稍后指定的 Bulk Strings 或 Array 的特殊变体来表示 Null 值。在 RESP 中，协议的不同部分始终以“\\ r \\ n”（CRLF）结束。\

## RESP 单行字符串（简单字符串）

简单字符串按以下方式编码：加号字符，后跟不能包含 CR 或 LF 字符的字符串（不允许换行），由 CRLF 终止（即“\\ r \\ n”）。\
Simple Strings 用于以最小的开销传输非二进制安全字符串。例如，许多 Redis 命令成功回复时只有“OK”，因为 RESP 单行字符串使用以下 5 个字节进行编码：

``` bash
"+OK\r\n"
```

为了发送二进制安全字符串，使用 RESP 多行字符串代替。\
当 Redis 使用 Simple String 回复时，客户端库应该向调用者返回一个字符串，该字符串从“+”之后的第一个字符开始，一直到字符串结尾，不包括最终的 CRLF 字节。

## RESP 错误信息

RESP 具有错误的特定数据类型。实际上错误与 RESP 单行字符串完全相同，但第一个字符是减号' - '字符而不是加号。

RESP 中单行字符串和错误之间的真正区别在于客户端将错误视为异常，组成错误类型的字符串是错误消息本身。基本格式如下：

``` bash
"-Error message\r\n"
```

错误回复仅在发生错误时发送，例如，如果您尝试对错误的数据类型执行操作，或者命令不存在等等。收到错误回复时，客户端应将异常抛出。

以下是错误回复的示例：

``` bash
-ERR unknown command 'foobar'
-WRONGTYPE Operation against a key holding the wrong kind of value
```

“ - ”之后的第一个单词，直到第一个空格或换行符，表示返回的错误类型。这只是 Redis 使用的约定，不是 RESP 错误格式的一部分。

例如，ERR 是一般错误，而 WRONGTYPE 是一个更具体的错误，意味着客户端尝试对错误的数据类型执行操作。这称为错误前缀，是一种允许客户端理解服务器返回的错误类型的方法，而不依赖于给定的确切消息，这可能随时间而变化。

客户端实现可以针对不同的错误返回不同类型的异常，或者可以通过直接将错误名称作为字符串提供给调用者来提供捕获错误的通用方法。

但是，这样的功能不应该被认为是至关重要的，因为它很少有用，并且有限的客户端实现可能只返回通用的错误条件，例如 false。

## RESP 整型数据

此类型只是一个 CRLF 终止的字符串，表示一个以“：”字节为前缀的整数。例如“：0 \\ r \\ n”或“：1000 \\ r \\ n”是整数回复。许多 Redis 命令返回 RESP 整型，如 INCR，LLEN 和 LASTSAVE。

返回的整数没有特殊含义，它只是 INCR 的增量编号，LASTSAVE 的 UNIX 时间等等。但是，返回的整数应保证在有符号的 64 位整数范围内。

整数回复也被广泛使用，以便返回真或假。例如，EXISTS 或 SISMEMBER 之类的命令将返回 1 表示 true，0 表示 false。

如果实际执行操作，其他命令（如 SADD，SREM 和 SETNX）将返回 1，否则返回 0。

以下命令将回复整数回复：SETNX，DEL，EXISTS，INCR，INCRBY，DECR，DECRBY，DBSIZE，LASTSAVE，RENAMENX，MOVE，LLEN，SADD，SREM，SISMEMBER，SCARD。

## RESP 多行字符串

多行字符串用于表示长度最大为 512 MB 的单个二进制安全字符串。

多行字符串按以下方式编码：

- 一个“\$”字节后跟组成字符串的字节数（一个前缀长度），由 CRLF 终止。
- 字符串数据。
- 最终的 CRLF。

所以字符串“foobar”的编码如下：

``` bash
"$6\r\nfoobar\r\n"
```

当只是一个空字符串时：

``` bash
"$0\r\n\r\n"
```

RESP 多行字符串也可以使用用于表示 Null 值的特殊格式来表示值的不存在。在这种特殊格式中，长度为-1，并且没有数据，因此 Null 表示为：

``` bash
"$-1\r\n"
```

当服务器使用 Null 多行字符串回复时，客户端库 API 不应返回空字符串，而应返回 nil 对象。例如，Ruby 库应返回'nil'，而 C 库应返回 NULL（或在 reply 对象中设置特殊标志），依此类推。

## RESP 数组

客户端使用 RESP 数组将命令发送到 Redis 服务器。类似地，某些 Redis 命令将元素集合返回给客户端使用 RESP 数组是回复类型。一个例子是 LRANGE 命令，它返回列表的元素。

RESP 数组使用以下格式发送：

- \*字符作为第一个字节，后跟数组中的元素数作为十进制数，后跟 CRLF。
- 数组的每个元素的附加 RESP 类型。

所以空数组就是以下内容：

``` bash
"*0\r\n"
```

那么两个 RESP 批量字符串“foo”和“bar”的数组编码为：

``` bash
"*2\r\n$3\r\nfoo\r\n$3\r\nbar\r\n"
```

正如您在数组前面加上\* CRLF 部分之后所看到的那样，组成数组的其他数据类型将一个接一个地连接起来。例如，三个整数的数组编码如下：

``` bash
"*3\r\n:1\r\n:2\r\n:3\r\n"
```

数组可以包含混合类型，元素不必具有相同的类型。例如，四个整数和批量字符串的列表可以编码如下：

``` bash
*5\r\n
:1\r\n
:2\r\n
:3\r\n
:4\r\n
$6\r\n
foobar\r\n
```

服务器发送的第一行是\* 5 \\ r \\ n，以指定将跟随五个回复。然后发送构成多重回复项目的每个回复。

Null 数组的概念也存在，并且是指定 Null 值的替代方法（通常使用 Null 多行字符串，但由于历史原因，我们有两种格式）。

例如，当 BLPOP 命令超时时，它返回一个计数为-1 的 Null 数组，如下例所示：

``` bash
"*-1\r\n"
```

当 Redis 使用 Null 数组回复时，客户端库 API 应返回 nil 对象而不是空数组。这是区分空列表和不同条件（例如 BLPOP 命令的超时条件）所必需的。

RESP 中可以使用数组中嵌套数组。例如，两个数组的数组编码如下：

``` bash
*2\r\n
*3\r\n
:1\r\n
:2\r\n
:3\r\n
*2\r\n
+Foo\r\n
-Bar\r\n
```

第二个元素是 Null。客户端库应返回如下内容：

``` bash
["foo",nil,"bar"]
```

注意，这不是前面部分中所述的例外，而只是进一步说明协议的示例。

## 发送命令到 Redis 服务端

既然熟悉了 RESP 序列化格式，那么编写 Redis 客户端库就很容易了。我们可以进一步讲述客户端和服务器之间的交互如何工作：

- 客户端向 Redis 服务器发送仅由 Bulk Strings 组成的 RESP 数组。
- Redis 服务器回复客户端，发送任何有效的 RESP 数据类型作为回复。

因此，例如，典型的交互可以是以下所示。

客户端发送命令 LLEN mylist 以获取存储在密钥 mylist 中的列表长度，服务器返回一个 Integer 回复，如下例所示（C：是客户端，S：服务器）。

``` bash
C: *2\r\n
C: $4\r\n
C: LLEN\r\n
C: $6\r\n
C: mylist\r\n
S: :48293\r\n
```

通常我们将协议的不同部分与换行符分开以简化，但实际的交互是客户端发送 \* 2 \\ r \\ n <img src="https://juejin.cn/equation?tex=4%20%5C%20r%20%5C%20nLLEN%20%5C%20r%20%5C%20n" class="equation" loading="lazy" alt="4 \ r \ nLLEN \ r \ n" /> 6 \\ r \\ nmylist \\ r \\ n 整体。

## 小结

这是楼主第一次尝试翻译一篇技术文档，相对来说技术文档的英文阅读起来还是比较舒服的，相信有了第一次尝试，之后肯定会越来越顺利。由于楼主水平有限，文章中难免有纰漏，期望小伙伴们的指正，感谢……。

## 参考链接

- <a href="https://link.juejin.cn?target=https%3A%2F%2Fredis.io%2Ftopics%2Fprotocol" target="_blank" data-ref="nofollow noopener noreferrer" title="https://redis.io/topics/protocol">Redis Protocol specification</a>
