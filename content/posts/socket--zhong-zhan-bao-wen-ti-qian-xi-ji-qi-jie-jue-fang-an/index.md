---
categories: ["Java"]
title: "Socket 中粘包问题浅析及其解决方案"
date: "2018-07-16T00:00:00+08:00"
tags: ["Android", "Docker", "Go", "Java", "Kafka", "Kotlin", "MySQL", "Nginx", "Python", "Raft", "Redis", "Shell", "Spring-Boot", "WebFlux", "go", "golang", "netty", "web", "学习笔记", "工具", "性能优化", "性能测试", "总结", "散列表", "旅游日记", "源码", "源码解析", "算法", "设计模式", "译文", "配置中心", "问题排查"]
summary: "最近一直在做中间件相关的东西，所以接触到的各种协议比较多，总的来说有TCP，UDP，HTTP等各种网络传输协议，因此楼主想先从协议最基本的TCP粘包问题搞起，把计算机网络这部分基础夯实一下。  TCP协议的简单介绍 TCP是面向连接的运输层"
translationKey: "socket--zhong-zhan-bao-wen-ti-qian-xi-ji-qi-jie-jue-fang-an"
---

> 📌 本文原发布于代码星冰乐：[Socket 中粘包问题浅析及其解决方案](https://changhuin.github.io/article/2018/d5b3/)

最近一直在做中间件相关的东西，所以接触到的各种协议比较多，总的来说有TCP，UDP，HTTP等各种网络传输协议，因此楼主想先从协议最基本的TCP粘包问题搞起，把计算机网络这部分基础夯实一下。\

## TCP协议的简单介绍

**TCP是面向连接的运输层协议**

简单来说，在使用TCP协议之前，必须先建立TCP连接，就是我们常说的三次握手。在数据传输完毕之后，必须是释放已经建立的TCP连接，否则会发生不可预知的问题，造成服务的不可用状态。

**每一条TCP连接都是可靠连接，且只有两个端点**

TCP连接是从Server端到Client端的点对点的，通过TCP传输数据，无差错，不重复不丢失。

**TCP协议的通信是全双工的**

TCP协议允许通信双方的应用程序在任何时候都能发送数据。TCP 连接的两端都设有发送缓冲区和接收缓冲区，用来临时存放双向通信的数据。发送数据时，应用程序把数据传送给TCP的缓冲后，就可以做自己的事情，而TCP在合适的时候将数据发送出去。在接收的时候，TCP把收到的数据放入接收缓冲区，上层应用在合适的时候读取数据。

**TCP协议是面向字节流的**

TCP中的流是指流入进程或者从进程中流出的字节序列。所以向Java，golang等高级语言在进行TCP通信是都需要将相应的实体序列化才能进行传输。还有就是在我们使用Redis做缓存的时候，都需要将放入Redis的数据序列化才可以，原因就是Redis底层就是实现的TCP协议。

**TCP并不知道所传输的字节流的含义，TCP并不能保证接收方应用程序和发送方应用程序所发出的数据块具有对应大小的关系（这就是TCP传输过程中产生的粘包问题）。**但是应用程序接收方最终受到的字节流与发送方发送的字节流是一定相同的。因此，我们在使用TCP协议的时候应该制定合理的粘包拆包策略。

下图是TCP的协议传输的整个过程：

![TCP面向字节流](https://img.hchstudio.cn/TCP-face-to-feed.jpg)

下面这个图是从<a href="https://juejin.im/post/5b344ad6e51d4558892eeb46" target="_blank" rel="noopener">老钱</a>的博客里面取到的，非常生动\
![TCP传输动图](https://img.hchstudio.cn/TCP.gif)

## TCP粘包问题复现

### 理论推敲

如下图所示，出现的粘包问题一共有三种情况

![TCP粘包问题](https://img.hchstudio.cn/TCP-package.jpg)

**第一种情况：**\
如上图中的第一根**bar**所示，服务端一共读到两个数据包，每个数据包都是完成的，并没有发生粘包的问题，这种情况比较好处理，服务器只需要简单的从网络缓冲区去读就好了，每次服务端读取到的消息都是完成的，并不会出现数据不正确的情况。

**第二种情况：**\
服务端仅收到一个数据包，这个数据包包含客户端发出的两条消息的完整信息，这个时候基于第一种情况的逻辑实现的服务端就蒙了，因为服务端并不能很好的处理这个数据包，甚至不能处理，这种情况其实就是TCP的粘包问题。

**第三种情况：**\
服务端收到了两个数据包，第一个数据包只包含了第一条消息的一部分，第一条消息的后半部分和第二条消息都在第二个数据包中，或者是第一个数据包包含了第一条消息的完整信息和第二条消息的一部分信息，第二个数据包包含了第二条消息的剩下部分，这种情况其实是发送了TCP拆包问题，因为发生了一条消息被拆分在两个包里面发送了，同样上面的服务器逻辑对于这种情况是不好处理的。

**为什么会发生TCP粘包、拆包**

1.  应用程序写入的数据大于套接字缓冲区大小，这将会发生拆包。

2.  应用程序写入数据小于套接字缓冲区大小，网卡将应用多次写入的数据发送到网络上，这将会发生粘包。

3.  进行MSS（最大报文长度）大小的TCP分段，当TCP报文长度-TCP头部长度>MSS的时候将发生拆包。

4.  接收方法不及时读取套接字缓冲区数据，这将发生粘包。

**如何处理粘包、拆包**

通常会有以下一些常用的方法：

1.  使用带消息头的协议、消息头存储消息开始标识及消息长度信息，服务端获取消息头的时候解析出消息长度，然后向后读取该长度的内容。

2.  设置定长消息，服务端每次读取既定长度的内容作为一条完整消息，当消息不够长时，空位补上固定字符。

3.  设置消息边界，服务端从网络流中按消息编辑分离出消息内容，一般使用‘\n’。

4.  更为复杂的协议，例如楼主最近接触比较多的车联网协议808,809协议。

### TCP粘包拆包的代码实践

下面代码楼主主要演示了使用规定消息头，消息体的方式来解决TCP的粘包，拆包问题。

**server端代码：** server端代码的主要逻辑是接收客户端发送过来的消息，重新组装出消息，并打印出来。

    import java.io.*;
    import java.net.InetSocketAddress;
    import java.net.ServerSocket;
    import java.net.Socket;

    /**
     * @author wuhf
     * @Date 2018/7/16 15:50
     **/
    public class TestSocketServer {
        public static void main(String args[]) {
            ServerSocket serverSocket;
            try {
                serverSocket = new ServerSocket();
                serverSocket.bind(new InetSocketAddress(8089));
                while (true) {
                    Socket socket = serverSocket.accept();
                    new ReceiveThread(socket).start();

                }
            } catch (IOException e) {
                // TODO Auto-generated catch block
                e.printStackTrace();
            }
        }

        static class ReceiveThread extends Thread {
            public static final int PACKET_HEAD_LENGTH = 2;//包头长度
            private Socket socket;
            private volatile byte[] bytes = new byte[0];

            public ReceiveThread(Socket socket) {
                this.socket = socket;
            }

            public byte[] mergebyte(byte[] a, byte[] b, int begin, int end) {
                byte[] add = new byte[a.length + end - begin];
                int i = 0;
                for (i = 0; i < a.length; i++) {
                    add[i] = a[i];
                }
                for (int k = begin; k < end; k++, i++) {
                    add[i] = b[k];
                }
                return add;
            }

            @Override
            public void run() {
                int count = 0;
                while (true) {
                    try {
                        InputStream reader = socket.getInputStream();
                        if (bytes.length < PACKET_HEAD_LENGTH) {
                            byte[] head = new byte[PACKET_HEAD_LENGTH - bytes.length];
                            int couter = reader.read(head);
                            if (couter < 0) {
                                continue;
                            }
                            bytes = mergebyte(bytes, head, 0, couter);
                            if (couter < PACKET_HEAD_LENGTH) {
                                continue;
                            }
                        }
                        // 下面这个值请注意，一定要取2长度的字节子数组作为报文长度，你懂得
                        byte[] temp = new byte[0];
                        temp = mergebyte(temp, bytes, 0, PACKET_HEAD_LENGTH);
                        String templength = new String(temp);
                        int bodylength = Integer.parseInt(templength);//包体长度
                        if (bytes.length - PACKET_HEAD_LENGTH < bodylength) {//不够一个包
                            byte[] body = new byte[bodylength + PACKET_HEAD_LENGTH - bytes.length];//剩下应该读的字节(凑一个包)
                            int couter = reader.read(body);
                            if (couter < 0) {
                                continue;
                            }
                            bytes = mergebyte(bytes, body, 0, couter);
                            if (couter < body.length) {
                                continue;
                            }
                        }
                        byte[] body = new byte[0];
                        body = mergebyte(body, bytes, PACKET_HEAD_LENGTH, bytes.length);
                        count++;
                        System.out.println("server receive body:  " + count + new String(body));
                        bytes = new byte[0];
                    } catch (Exception e) {
                        e.printStackTrace();
                    }
                }
            }
        }

    }

**client端代码：**客户端代码主要逻辑是组装要发送的消息，确定消息头，消息体，然后发送到服务端。

    import java.io.*;
    import java.net.InetSocketAddress;
    import java.net.Socket;

    /**
     * @author wuhf
     * @Date 2018/7/16 15:45
     **/
    public class TestSocketClient {
        public static void main(String args[]) throws IOException {
            Socket clientSocket = new Socket();
            clientSocket.connect(new InetSocketAddress(8089));
            new SendThread(clientSocket).start();

        }

        static class SendThread extends Thread {
            Socket socket;
            PrintWriter printWriter = null;

            public SendThread(Socket socket) {
                this.socket = socket;
                try {
                    printWriter = new PrintWriter(new OutputStreamWriter(socket.getOutputStream()));
                } catch (IOException e) {
                    // TODO Auto-generated catch block
                    e.printStackTrace();
                }
            }

            @Override
            public void run() {
                String reqMessage = "HelloWorld！ from clientsocket this is test half packages!";
                for (int i = 0; i < 100; i++) {
                    sendPacket(reqMessage);
                }
                if (socket != null) {
                    try {
                        socket.close();
                    } catch (IOException e) {
                        // TODO Auto-generated catch block
                        e.printStackTrace();
                    }
                }

            }

            public void sendPacket(String message) {
                try {
                    OutputStream writer = socket.getOutputStream();
                    writer.write(message.getBytes());
                    writer.flush();
                } catch (IOException e) {
                    // TODO Auto-generated catch block
                    e.printStackTrace();
                }
            }
        }

    }

## 小结

最近一直在写一些框架性的博客，专门针对某些问题进行原理性的技术探讨的博客还比较少，所以楼主想着怎样能在自己学到东西的同时也可以给一同在技术这条野路子上奋斗的小伙伴们一些启发，是楼主一直努力的方向。

这篇文章因为标题使用不当，也就导致有小伙伴指出说在误人子弟，所以为了不引起误会，将文章的名称更正，楼主写博客也是自己平时的积累，难免因为眼界的问题出现纰漏，请小伙伴不吝指出。

## 参考文章

- <a href="https://my.oschina.net/andylucc/blog/625315" target="_blank" rel="noopener" title="Netty精粹之TCP粘包拆包问题">Netty精粹之TCP粘包拆包问题</a>
- [计算机网络-谢希仁-第七版](https://www.hchstudio.cn/ "Netty精粹之TCP粘包拆包问题")

