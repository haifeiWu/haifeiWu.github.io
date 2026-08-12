---
categories: ["后端"]
title: "Netty 实战之第一个应用"
date: "2018-06-21T20:09:37+08:00"
tags: ["Netty", "Java", "源码", "TCP/IP", "Java EE"]
summary: "作为一个正在 Java 路上摸爬滚打的小菜鸡，之前在项目中也用过 Netty，也因为 Netty 报名阿里的中间件大赛，但终究功力太浅，最终不了了之，最近工作中又遇到了 Netty 的小姐妹 Mina。此时楼主觉得 Netty 还是需要潜心深入学习一下。"
translationKey: "nettyshizhanzhidiyigeyingyong"
---

> 📌 本文原发布于掘金社区：[Netty 实战之第一个应用](https://juejin.cn/post/6844903623592247303)

作为一个正在 Java 路上摸爬滚打的小菜鸡,之前在项目中也用过 Netty,也因为 Netty 报名阿里的中间件大赛,但终究功力太浅,最终不了了之,最近工作中又遇到了 Netty 的小姐妹 Mina。此时楼主觉得 Netty 还是需要潜心深入学习一下。就这样在成为大菜鸡的路上不消停地折腾……\
<span id="user-content-more"></span>

## [](#NIO简介 "#NIO简介")NIO 简介

- Netty 是 Java 世界知名的基于 NIO 的网络框架，因此说到 Netty，介绍一下 NIO 还是有必要的。

- Java NIO 又称 Non-blocking IO,NIO 可以让你非阻塞地使用 IO,例如:当线程从通道读取数据到缓冲区时,线程还可以做其他事情。当数据被写入到缓冲区时,线程可以继续处理它。从缓冲区写入通道也类似。

- Java NIO 主要由 Channels，Buffers，Selectors 组成，虽然 Java NIO 中除此之外还有很多类和组件,但总体来说,Channel,Buffer 和 Selector 构成了核心的 API。其他组件和类主要是围绕这三者进行的。对 NIO 感兴趣的小伙伴请移步<a href="https://link.juejin.cn?target=http%3A%2F%2Fifeve.com%2Fjava-nio-all%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://ifeve.com/java-nio-all/">Java NIO 系列教程</a>

## [](#Netty快速入门 "#Netty快速入门")Netty 快速入门

一般楼主在学习一项新技术时，首先得来个“Hello，World”暖暖场。当然 Netty 也不例外,这里楼主实现一个 echo 服务器,那么 echo 是什么呢?\
就是先启动客户端,然后建立一个连接并发送一个或多个消息到服务器，其中每条相呼应的消息返回给客户端。当然,这个应用程序没多大意义。但也可以帮助我们理解 Netty,以及学习 Netty 的模板代码。

### [](#添加maven依赖 "#添加maven依赖")添加 Maven 依赖

一般开源软件在 Maven 仓库里面都可以找到,请移步<a href="https://link.juejin.cn?target=http%3A%2F%2Fmvnrepository.com%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://mvnrepository.com/">Maven 仓库</a>\

    <dependency>
        <groupId>io.netty</groupId>
        <artifactId>netty-all</artifactId>
        <version>4.1.12.Final</version>
    </dependency>

### [](#代码实现 "#代码实现")代码实现

Echo 的服务端代码实现，下面代码实现的主要逻辑是绑定端口号，启动服务，是 Netty 中常见的模板代码。\

    public class EchoServer {
        private final int port;

        public EchoServer(int port) {
            this.port = port;
        }

        public static void main(String[] args)
            throws Exception {
            // 服务器监听端口号
            int port = 8080;
            new EchoServer(port).start();
        }

        public void start() throws Exception {
            // NioEventLoopGroup是处理I/O操作的多线程事件循环
            EventLoopGroup group = new NioEventLoopGroup();
            try {
                // ServerBootstrap是一个用于设置服务器的引导类。
                ServerBootstrap b = new ServerBootstrap();
                b.group(group)
                    .channel(NioServerSocketChannel.class) // 使用NioServerSocketChannel类，用于实例化新的通道以接受传入连接
                    .localAddress(new InetSocketAddress(port)) // 设置服务器监听端口号
                    .childHandler(new ChannelInitializer<SocketChannel>() {
                        @Override
                        public void initChannel(SocketChannel ch) throws Exception {
                            ch.pipeline().addLast(new EchoServerHandler()); // 添加请求处理
                        }
                    });
                // 绑定到端口和启动服务器
                ChannelFuture f = b.bind().sync();
                System.out.println(EchoServer.class.getName() +
                    " started and listening for connections on " + f.channel().localAddress());
                f.channel().closeFuture().sync();
            } finally {
                group.shutdownGracefully().sync();
            }
        }
    }

EchoServerHandler 实现代码，这里是使用 Netty 实现网络操作业务逻辑的主要阵地。在这里覆盖 channelRead()事件处理程序方法。每当从客户端接收到新数据时，使用该方法来接收客户端的消息。

    @Sharable
    public class EchoServerHandler extends ChannelInboundHandlerAdapter {
        @Override
        public void channelRead(ChannelHandlerContext ctx, Object msg) {
            // 覆盖channelRead()事件处理程序方法
            ByteBuf in = (ByteBuf) msg;
            System.out.println(
                    "Server received: " + in.toString(CharsetUtil.UTF_8));
            ctx.write(in);
        }

        @Override
        public void channelReadComplete(ChannelHandlerContext ctx)
                throws Exception {
            // channelRead()执行完成后，关闭channel连接
            ctx.writeAndFlush(Unpooled.EMPTY_BUFFER)
                    .addListener(ChannelFutureListener.CLOSE);
        }

        @Override
        public void exceptionCaught(ChannelHandlerContext ctx,
            Throwable cause) {
            cause.printStackTrace();
            ctx.close();
        }
    }

客户端代码跟上面的代码大体类似,楼主就不再贴出来了,就当留个小作业吧,感兴趣的小伙伴请自行搞定。

## [](#楼主使用Netty的姿势 "#楼主使用Netty的姿势")楼主使用 Netty 的姿势

楼主基于 Netty 开发了应用配置管理平台服务，实现了“为业务提供统一的配置管理服务”，可以做到开箱即用，主要功能有：

- 简单易用：上手非常简单，只需要引入 Maven 依赖和一行配置即可；
- 在线管理：提供配置管理中心，支持在线管理配置信息；
- 实时推送：配置信息更新后，实时推送配置信息，项目中配置数据会实时更新并生效，不需要重启线上机器；
- 配置备份:配置数据会在 MySQL 中对配置信息做备份,保证配置数据的安全性;

感兴趣的小伙伴请移步<a href="https://link.juejin.cn?target=https%3A%2F%2Fgithub.com%2FhaifeiWu%2Flightconf" target="_blank" data-ref="nofollow noopener noreferrer" title="https://github.com/haifeiWu/lightconf">楼主的 Netty 实践</a>

## [](#小结 "#小结")小结

虽然楼主经常使用到 Netty，但是很多时候对 Netty 的一些概念还是处于知其然，不知其所以然的状态，因此就萌生了重新捋一遍 Netty 实战，在有余力的情况下撸一下 Netty 的源码，并坚持写博客记录一下这个过程。由于楼主能力有限，博客中难免有不少错误之处，期望大家的建议，斧正。
