---
aliases: ["/zh-cn/posts/wolijiede-tcp-lianjie/"]
categories: ["后端"]
title: "我理解的 TCP 连接"
date: "2019-11-27T12:01:51+08:00"
tags: ["Java", "TCP/IP"]
summary: "TCP 是面向连接的协议。运输连接是用来传输 TCP 报文的。TCP 运输连接的建立和释放是每一次面向连接通信中必不可少的过程。因此，运输连接有三个阶段，即：连接建立，数据传输和连接释放。在 TCP 连接建立过程中要解决一下三个问题。（1）要使一方明确知道对方的存在。（2）要…"
translationKey: "wolijiede-tcp-lianjie"
---

> 📌 本文原发布于掘金社区：[我理解的 TCP 连接](https://juejin.cn/post/6844904005676580871)

<a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2019%2F99ad%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/article/2019/99ad/">我理解的 TCP 连接-原文链接</a>\
<a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2019%2F99ad%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/article/2019/99ad/">我理解的 TCP 连接-原文链接</a>\
<a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2019%2F99ad%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/article/2019/99ad/">我理解的 TCP 连接-原文链接</a>\

## 总述

TCP 是面向连接的协议。运输连接是用来传输 TCP 报文的。TCP 运输连接的建立和释放是每一次面向连接通信中必不可少的过程。因此，运输连接有三个阶段，即：连接建立，数据传输和连接释放。

在 TCP 连接建立过程中要解决以下三个问题。

（1）要使一方明确知道对方的存在。（2）要允许双方协商一些参数（如最大窗口值等）。（3）能够对运输实体资源进行分配。

## TCP 的连接建立（三次握手）

<figure>
<img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2019/11/27/16eab03a29e887d7~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp" loading="lazy" alt="三次握手" />
</figure>

如上图所示，上图画出了 TCP 的连接过程。假定主机 A 运行的是 TCP 客户程序，而 B 运行的是 TCP 服务器程序。最初两端的 TCP 进程都处于 CLOSE 状态。图中在主机下面的方框中分别是 TCP 进程所处于的状态。请注意，A 主动打开连接，而 B 被动打开连接。

B 的 TCP 服务器进程先创建传输控制块 TCB，准备接受客户进程的连接请求。然后服务器进程处于 LISTEN 状态，等待客户的连接请求。如有，即作出响应。

A 的 TCP 客户进程也是首先创建传输控制块 TCB，然后向 B 发出连接请求报文段。其首部的同步位 SYN = 1，同时选择一个初始序号 seq = x。TCP 规定，SYN 报文段，不能携带数据，但要消耗掉一个序号，这时 TCP 客户程序进入 SYN-SEND（同步已发送）状态。

B 接收到连接请求报文段后，如同意连接，则向 A 发送确认。在确认报文段中应把 SYN 位和 ACK 位都设置为 1，确认号是 ack = x + 1，同时也为自己选择一个初始序号 seq = y。请注意，这个报文段也不能携带任何数据，但同样要消耗掉一个序号。这时，TCP 服务器程序进入 SYN-RCVD（同步收到）状态。

TCP 客户进程收到 B 的确认后，还要向 B 确认。确认报文段的 ACK 置 1，确认号 ack = y + 1，而自己的序号 seq = x + 1。TCP 的标准规定，ACK 报文段可以携带数据。但如果不携带数据则不消耗序号，在这种情况下，下一个数据报文段的序号仍然是 seq = x + 1。这时 TCP 连接建立完成，A 进入 ESTABLISHED（已建立连接）状态。当 B 收到 A 的确认后，也进入 ESTABLISHED 状态。

## TCP 连接的释放（四次挥手）

<figure>
<img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2019/11/27/16eab03a242a0ba7~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp" loading="lazy" alt="四次握手" />
</figure>

数据传输结束后，通信双方都可以释放连接。现在 A 和 B 都处于 ESTABLISHED 状态。A 的应用进程先向其 TCP 发出连接释放报文段，并不再发送数据，主动关闭 TCP 连接。A 把连接释放报文段首部的终止控制位 FIN 设置为 1，其序号 seq = u，它等于前面传送过的数据的最后一个字节序号加 1。这时 A 进入 FIN_WAIT_1（终止等待 1）状态，等待 B 的确认。请注意，TCP 规定，FIN 报文段即使不携带数据，它也消耗掉一个序号。

B 收到连接释放的报文段后立即发出确认，确认号 ack = u + 1，而这个报文段自己的序号是 v，等于 B 前面已传送过的数据的最后一个字节加 1。然后 B 进入 CLOSE_WAIT（关闭等待）状态。TCP 服务器进程这时通知高层的应用进程，因而从 A 到 B 这个方向的连接就释放了，这时的 TCP 连接处于半关闭（half-close）状态，即 A 已经没有数据要发送了，但是 B 若发送数据，A 仍要接收。也就是说，从 B 到 A 这个方向的连接并未关闭，这个状态可能会持续一段时间。

A 收到来自 B 的确认后，就进入 FIN_WAIT_2（终止等待 2）状态，等待 B 发出连接释放报文段。

若 B 已经没有要向 A 发送的数据，其应用进程就通知 TCP 释放连接。这时 B 发出连接释放报文段使 FIN = 1。现假定 B 的序号为 w（在半关闭状态 B 可能又发送了一些数据）。B 还必须重复上次已经发过的确认号 ack = u + 1。这时 B 就进入 LAST_ACK（最后确认）状态，等待 A 的确认。

A 在收到 B 的连接释放报文段后，必须对此发出确认。在确认报文段中把 ACK 设置为 1，确认号 ack = w + 1，而自己的序号是 seq = u + 1（根据 TCP 的标准，前面发送过的 FIN 报文要消耗一个序号）。然后进入到 TIME_WAIT（时间等待）状态。请注意，现在 TCP 连接还没有释放掉。必须经过时间等待计时器设置的时间 2MSL 后，A 才进入到 CLOSE 状态。时间 MSL 叫做最长报文段寿命，RFC 793 建议设置为 2 分钟。但这完全是从工程上来考虑，对于现在的网络，MSL = 2分钟可能太长了一些。因此 TCP 允许不同的实现可以根据实际情况使用更小的 MSL 值。因此，从 A 进入到 TIME_WAIT 状态后，要经过 4 分钟才能进入到 CLOSE 状态，才能建立下一个连接。当 A 撤销相应的传输控制块 TCB 后，就结束这次的 TCP 连接。

## 两个小问题

**在三次握手的过程中，为什么 A 还要发送一次确认呢？** 这主要是为了防止已失效的连接请求报文突然又传到了 B，因而产生错误。

**为什么 A 在 TIME_WAIT 状态必须等待 2MSL 的时间呢？**

第一，为了保证 A 发送的最后一个 ACK 报文段能够到达 B。

第二，防止刚提到的 “已失效的连接请求报文段” 出现在本连接中。A 在发送完最后一个 ACK 报文段后，再经过时间 2MSL，就可以使本连接持续时间内所产生的所有报文段从网络中消失。这样就可以使下一个连接中不会出现这种旧的连接请求报文段。

## 参考链接

<a href="https://link.juejin.cn?target=https%3A%2F%2Fwww.hchstudio.cn" target="_blank" data-ref="nofollow noopener noreferrer" title="https://www.hchstudio.cn">计算机网络第 6 版</a>

## 关注我们

<figure>
<img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2019/11/8/16e498848fb64e35~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp" loading="lazy" alt="关注我们" />
</figure>
