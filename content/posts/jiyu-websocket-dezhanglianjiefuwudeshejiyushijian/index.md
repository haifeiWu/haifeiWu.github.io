---
categories: ["后端"]
title: "基于 websocket 的长连接服务的设计与实践"
date: "2024-06-18T18:29:44+08:00"
tags: ["后端", "架构", "程序员"]
summary: "业务场景 在常见的 pk 游戏的场景下，pk 双方需要实时感知双方的做题状态，因此长连接在这种场景下的应用极为常见，本文将基于此来讨论下长连接服务的设计与实现。"
---

> 📌 本文原发布于掘金社区：[基于 websocket 的长连接服务的设计与实践](https://juejin.cn/post/7381669580471173157)

# 业务场景

在常见的 pk 游戏的场景下，pk 双方需要实时感知双方的做题状态，因此长连接在这种场景下的应用极为常见，本文将基于此来讨论下长连接服务的设计与实现。

# 实现方案

## 轮询

<img src="https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/5927dd07c40f40099f810686651d4c69~tplv-k3u1fbpfcp-jj-mark:3024:0:0:0:q75.awebp#?w=1149&amp;h=1191&amp;s=164356&amp;e=png&amp;b=fefefe" loading="lazy" />

轮询是一种客户端定期询问服务器是否有可用消息的技术。 根据轮询频率，轮询的成本可能很高。大多数轮询是无效的，QPS 会特别高，导致服务器资源的浪费。

## 长轮询

<img src="https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/a0f09e50eab24b1da6ceab55fdb82d8a~tplv-k3u1fbpfcp-jj-mark:3024:0:0:0:q75.awebp#?w=1392&amp;h=1186&amp;s=153753&amp;e=png&amp;b=ffffff" loading="lazy" />

在长轮询中，客户端保持连接打开，直到实际有新消息可用或连接超时。 一旦客户端收到新消息，它会立即向服务器发送另一个请求，重新启动进程。 长轮询有一些缺点：

- 发送者和接收者不能连接到同一个聊天服务器。 基于 HTTP 的服务器通常是无状态的。 如果在分布式的场景下，接收消息的服务器可能与接收消息的客户端没有长轮询连接。
- 服务器没有很好的方法来判断客户端是否断开连接。
- 这是低效的。 跟轮询的方案类似，如果用户不多，长轮询仍会在超时后进行周期性连接。消耗服务器资源。

## 长连接

<img src="https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/e070a1eb520b4a259cd7cbe6fbb601f6~tplv-k3u1fbpfcp-jj-mark:3024:0:0:0:q75.awebp#?w=1954&amp;h=1184&amp;s=230926&amp;e=png&amp;b=ffffff" loading="lazy" />

WebSocket 连接由客户端发起， 它是一个全双工的长连接。 它以 HTTP 连接开始，并且可以通过一些定义明确的握手“升级”到 WebSocket 连接。 通过这种持久连接，服务器可以向客户端发送更新。

websocket 可以实现实时通信，但是存在的问题是它是长连接，需要连接到具体的实例上，如果是客户端 a 与客户端 b 之间相互通信的话，就需要保证这两个连接在同一个实例上，因此就需要我们维护一套服务发现的机制实现不同长连接之间的通信。

## 分布式长连接

维持大量的长连接对单台服务器的压力也挺大的，这里也就要求该服务需要可以扩容，也就是分布式地扩展。分布式对于可存储的公共资源有一套完整的解决方案，但对于 WebSocket 来说，操作对象就是每一个连接，它是维持在每一个程序中的。每一个连接不能存储起来共享、不能在不同的程序之间共享。所以我能想到的方案是不同程序之间进行通讯。那么，怎样知道某个连接在哪个应用呢？下面两种方案我们来一一讨论下

### IP 直连

通过 ip + port 去判断。每个连接都保存在本应用，然后用对称加密加密服务器 IP 和端口，得到的值作为 client id。对指定 client id 进行操作时，只需要解密这个 key，就能得到相应的 IP 和端口。判断是否为本机，不是本机的话进行 RPC 通讯告诉相应的程序。长连接的连接数据不可迁移，程序挂掉了相应的连接也就挂了，在该程序上的连接也就断开了，这时重连的话会找到另一个可用的程序。

<img src="https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/4b251e7562f5408db0e9f6b7014b3b12~tplv-k3u1fbpfcp-jj-mark:3024:0:0:0:q75.awebp#?w=1693&amp;h=1186&amp;s=181776&amp;e=png&amp;b=fbfbfb" loading="lazy" />

#### 时序图

**单发消息**

<img src="https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/54ba9056418f456fad8c38a89138f9ec~tplv-k3u1fbpfcp-jj-mark:3024:0:0:0:q75.awebp#?w=1597&amp;h=1188&amp;s=188938&amp;e=png&amp;b=fafafa" loading="lazy" />

1.  客户端发送连接请求，连接请求通过 nginx 负载均衡找到一台 ws 服务器；
2.  ws 服务器响应连接请求，通过对称加密服务器 IP 和端口号，得到的值作为 client id，并返回。
3.  客户端拿到 client id 之后，交给业务系统；
4.  业务系统拿到 client id 之后，通过 http 发送相关消息，经过 nginx 负载分配到一台 ws 服务器；
5.  这台 ws 服务器拿到 clinet id 和消息，解密出对应的服务器 IP 和端口；
6.  拿到 IP 地址和端口，通过 HTTP/PRC 协议给指定 ws 程序发送信息；
7.  该 ws 程序接收到 client id 和信息，给指定的连接发送信息；
8.  客户端收到信息。

**群发消息**

<img src="https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/b9b1dbd850a24b888615b475fbbf24a3~tplv-k3u1fbpfcp-jj-mark:3024:0:0:0:q75.awebp#?w=1896&amp;h=1184&amp;s=217045&amp;e=png&amp;b=fafafa" loading="lazy" />

1.  前 3 个步骤跟单发的一样；
2.  业务系统拿到 client id 之后，通过 http 给指定分组发送消息，经过 nginx 负载分配到一台 ws 服务器；
3.  这台 ws 服务器拿到分组 ID 和消息，去 redis 获取服务器列表，然后发送 HTTP/RPC 广播；
4.  所有收到广播的 ws 长连接服务，找到本机所有该分组的连接，给所有这些连接发送消息；
5.  客户端收到信息。

### MQ 分布式方案

<img src="https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/34abdfed1b4d4f8cace97747e259b531~tplv-k3u1fbpfcp-jj-mark:3024:0:0:0:q75.awebp#?w=1499&amp;h=927&amp;s=198268&amp;e=png&amp;b=fdfdfd" loading="lazy" />

- ws-server：长连接接入层，可以通过服务发现组件实现长连接服务的无限横向扩展；
- nacos：这里作为服务发现组件来实现连接服务的横向扩展；
- push-server：无状态服务 push 层，理论上可以无限横向扩展；
- MQ：这里我们可以使用 kafka 或者 Rocketmq，来实现消息的异步发送；
- push-consumer：push 消息发送层，负责 push 消息的投递。

#### 时序图

**单发消息**

<img src="https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/61b6c7f35ff94a52825e24eb831f1c13~tplv-k3u1fbpfcp-jj-mark:3024:0:0:0:q75.awebp#?w=1647&amp;h=1189&amp;s=163315&amp;e=png&amp;b=fffcfc" loading="lazy" />

1.  客户端发送连接请求，连接请求通过 nginx 负载均衡找到一台 ws 服务器；
2.  ws 服务器响应连接请求，将用户的 deviceid 或者 uid 与建立长连接的 ws 长连接服务器的 ip+port 存储到 redis 或者是 nacos 存储中，并将连接升级成 ws 长连接，并返回。
3.  业务系统就可以通过调用 push-server 的接口发送消息到指定的 deviceid 或者 uid，push-server 收到消息后将消息打包并发送给 mq，并返回发送成功；
4.  push-consumer 作为一个常驻任务，不停的消费 mq 中的消息，收到消息后，通过 deviceid 或者 uid 查询用户的长连接所在的服务，通过 http 或者 rpc 调用将消息发送到指定的 ws 长连接服务；
5.  该 ws 程序接收到信息，给指定的连接发送信息；
6.  客户端收到信息。

**群发消息**

<img src="https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/efdfa33ca48042a18622139286a3380a~tplv-k3u1fbpfcp-jj-mark:3024:0:0:0:q75.awebp#?w=1655&amp;h=1194&amp;s=214397&amp;e=png&amp;b=fffcfc" loading="lazy" />

1.  前 2 个步骤跟单发的一样；
2.  业务系统就可以通过调用 push-server 的接口发送消息到指定的房间 roomid，push-server 收到消息后，通过查询 redis 获取到房间中的 uid 或者 deviceid，将消息打包并发送给 mq，并返回发送成功；
3.  push-consumer 作为一个常驻任务，不停的消费 mq 中的消息，收到消息后，通过 deviceid 或者 uid 查询用户的长连接所在的服务，通过 http 或者 rpc 调用将消息发送到指定的 ws 长连接服务；
4.  该 ws 程序接收到信息，给指定的连接发送信息；
5.  房间中的所有客户端收到信息。

# 方案对比

## 轮询 VS 长连接

|            | 轮询 | 长轮询 | 长连接 | 分布式长连接 |
|------------|------|--------|--------|--------------|
| 实现复杂度 | 低   | 低     | 高     | 较高         |
| 资源利用率 | 低   | 低     | 高     | 高           |
| 可扩展性   | 低   | 低     | 低     | 高           |
| 可复用性   | 低   | 低     | 高     | 较高         |

## IP 直连 VS MQ 异步

|            | IP 直连  | MQ 异步                |
|------------|----------|------------------------|
| 实现复杂度 | 低       | 高                     |
| 可复用性   | 业务定制 | 模块各司其职，通用性高 |
| 可扩展性   | 高       | 较高                   |
