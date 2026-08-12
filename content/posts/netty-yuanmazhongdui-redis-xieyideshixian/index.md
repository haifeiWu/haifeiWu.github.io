---
categories: ["后端"]
title: "Netty 源码中对 Redis 协议的实现"
date: "2018-08-09T08:13:02+08:00"
tags: ["Redis", "后端", "源码", "Netty"]
summary: "近期一直在做网络协议相关的工作，所以博客也就与之相关的比较多，今天楼主结合 Redis 的协议 RESP 看看在 Netty 源码中是如何实现的。RESP 是 Redis 序列化协议的简写。它是一种直观的文本协议，优势在于实现非常简单，解析性能极好。Redis 协议将传输的结…"
translationKey: "netty-yuanmazhongdui-redis-xieyideshixian"
---

> 📌 本文原发布于掘金社区：[Netty 源码中对 Redis 协议的实现](https://juejin.cn/post/6844903653791252488)

> 原文地址：<a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2F%3F_ref%3Djuejin" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/?_ref=juejin">haifeiWu 的博客</a>\
> 博客地址：<a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2018%2F8191%2F%3F_ref%3Djuejin" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/article/2018/8191/?_ref=juejin">www.hchstudio.cn</a>\
> 欢迎转载，转载请注明作者及出处，谢谢！

近期一直在做网络协议相关的工作，所以博客也就与之相关的比较多，今天楼主结合 Redis 的协议 RESP 看看在 Netty 源码中是如何实现的。

## RESP 协议

RESP 是 Redis 序列化协议的简写。它是一种直观的文本协议，优势在于实现非常简单，解析性能极好。

Redis 协议将传输的结构数据分为 5 种最小单元类型，单元结束时统一加上回车换行符号\r\n，来表示该单元的结束。

1.  单行字符串 以 + 符号开头。
2.  多行字符串 以 \$ 符号开头，后跟字符串长度。
3.  整数值 以 : 符号开头，后跟整数的字符串形式。
4.  错误消息 以 - 符号开头。
5.  数组 以 \* 号开头，后跟数组的长度。

关于 RESP 协议的具体介绍感兴趣的小伙伴请移步楼主的另一篇文章<a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2018%2Fe687%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/article/2018/e687/">Redis 协议规范（译文）</a>

## Netty 中 RESP 协议的定义

如下面代码中所表示的，Netty 中使用对应符号的 ASCII 码来表示，感兴趣的小伙伴可以查一下 ASCII 码表来验证一下。

``` java

public enum RedisMessageType {
    // 以 + 开头的单行字符串
    SIMPLE_STRING((byte)43, true),
    // 以 - 开头的错误信息
    ERROR((byte)45, true),
    // 以 : 开头的整型数据
    INTEGER((byte)58, true),
    // 以 $ 开头的多行字符串
    BULK_STRING((byte)36, false),
    // 以 * 开头的数组
    ARRAY_HEADER((byte)42, false),
    ARRAY((byte)42, false);

    private final byte value;
    private final boolean inline;

    private RedisMessageType(byte value, boolean inline) {
        this.value = value;
        this.inline = inline;
    }

    public byte value() {
        return this.value;
    }

    public boolean isInline() {
        return this.inline;
    }

    public static RedisMessageType valueOf(byte value) {
        switch(value) {
        case 36:
            return BULK_STRING;
        case 42:
            return ARRAY_HEADER;
        case 43:
            return SIMPLE_STRING;
        case 45:
            return ERROR;
        case 58:
            return INTEGER;
        default:
            throw new RedisCodecException("Unknown RedisMessageType: " + value);
        }
    }
}
```

## Netty 中 RESP 解码器实现

解码器，顾名思义，就是将服务器返回的数据根据协议反序列化成易于阅读的信息。RedisDecoder 就是根据 RESP 将服务端返回的信息反序列化出来。下面是指令的编码格式

``` bash
SET key value => *3\r\n$5\r\nSET\r\n$1\r\nkey\r\n$1\r\nvalue\r\n
```

指令是一个字符串数组，编码一个字符串数组，首先需要编码数组长度\*3\r\n。然后依次编码各个字符串参数。编码字符串首先需要编码字符串的长度\$5\r\n。然后再编码字符串的内容 SET\r\n。Redis 消息以\r\n作为分隔符，这样设计其实挺浪费网络传输流量的，消息内容里面到处都是\r\n符号。但是这样的消息可读性会比较好，便于调试。RESP 协议是牺牲性能换取可读，易于实现的一个经典例子。

指令解码器的实现，Socket 读取网络字节流的时候存在拆包问题。所谓拆包问题是指一次 Read 调用从 Socket 读到的字节数组可能只是一个完整消息的一部分。而另外一部分则需要发起另外一次 Read 调用才可能读到，甚至要发起多个 Read 调用才可以读到完整的一条消息。对于拆包问题感兴趣的小伙伴可以查看楼主的另一篇文章<a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2018%2Fd5b3%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/article/2018/d5b3/">TCP 粘包问题浅析及其解决方案</a>

如果我们拿部分消息去反序列化成输入消息对象肯定是要失败的，或者说生成的消息对象是不完整的。这个时候我们需要等待下一次 Read 调用，然后将这两次 Read 调用的字节数组拼起来，尝试再一次反序列化。

问题来了，如果一个输入消息对象很大，就可能需要多个 Read 调用和多次反序列化操作才能完整地解包出一个输入对象。那这个反序列化的过程就会重复多次。

针对这个问题，Netty 中很巧妙地解决了这个问题，如下所示，Netty 中通过 state 属性来保存当前序列化的状态，然后下次反序列化的时候就可以从上次记录的 state 直接继续反序列化。这样就避免了重复的问题。

``` java
    // 保持当前序列化状态的字段
    private RedisDecoder.State state;

    public RedisDecoder() {
        this(65536, FixedRedisMessagePool.INSTANCE);
    }

    public RedisDecoder(int maxInlineMessageLength, RedisMessagePool messagePool) {
        this.toPositiveLongProcessor = new RedisDecoder.ToPositiveLongProcessor();
        // 默认初始化状态为，反序列化指令类型
        this.state = RedisDecoder.State.DECODE_TYPE;
        if (maxInlineMessageLength > 0 && maxInlineMessageLength <= 536870912) {
            this.maxInlineMessageLength = maxInlineMessageLength;
            this.messagePool = messagePool;
        } else {
            throw new RedisCodecException("maxInlineMessageLength: " + maxInlineMessageLength + " (expected: <= " + 536870912 + ")");
        }
    }

    // 解码器的主要业务逻辑
    protected void decode(ChannelHandlerContext ctx, ByteBuf in, List<Object> out) throws Exception {
        try {
            // 循环读取信息，将信息完成的序列化
            while(true) {
                switch(this.state) {
                case DECODE_TYPE:
                    if (this.decodeType(in)) {
                        break;
                    }

                    return;
                case DECODE_INLINE:
                    if (this.decodeInline(in, out)) {
                        break;
                    }

                    return;
                case DECODE_LENGTH:
                    if (this.decodeLength(in, out)) {
                        break;
                    }

                    return;
                case DECODE_BULK_STRING_EOL:
                    if (this.decodeBulkStringEndOfLine(in, out)) {
                        break;
                    }

                    return;
                case DECODE_BULK_STRING_CONTENT:
                    if (this.decodeBulkStringContent(in, out)) {
                        break;
                    }

                    return;
                default:
                    throw new RedisCodecException("Unknown state: " + this.state);
                }
            }
        } catch (RedisCodecException var5) {
            this.resetDecoder();
            throw var5;
        } catch (Exception var6) {
            this.resetDecoder();
            throw new RedisCodecException(var6);
        }
    }
```

下面的代码，是针对每种数据类型进行反序列化的具体业务逻辑。有小伙伴可能会想，没有看到解码数组类型的逻辑呢？实际上在 RESP 协议中数组就是其他类型的组合，所以完全可以循环读取，按照单个元素解码。

``` java
// 解码消息类型
 private boolean decodeType(ByteBuf in) throws Exception {
        if (!in.isReadable()) {
            return false;
        } else {
            this.type = RedisMessageType.valueOf(in.readByte());
            this.state = this.type.isInline() ? RedisDecoder.State.DECODE_INLINE : RedisDecoder.State.DECODE_LENGTH;
            return true;
        }
    }

    // 解码单行字符串，错误信息，或者整型数据类型
    private boolean decodeInline(ByteBuf in, List<Object> out) throws Exception {
        ByteBuf lineBytes = readLine(in);
        if (lineBytes == null) {
            if (in.readableBytes() > this.maxInlineMessageLength) {
                throw new RedisCodecException("length: " + in.readableBytes() + " (expected: <= " + this.maxInlineMessageLength + ")");
            } else {
                return false;
            }
        } else {
            out.add(this.newInlineRedisMessage(this.type, lineBytes));
            this.resetDecoder();
            return true;
        }
    }

    // 解码消息长度
    private boolean decodeLength(ByteBuf in, List<Object> out) throws Exception {
        ByteBuf lineByteBuf = readLine(in);
        if (lineByteBuf == null) {
            return false;
        } else {
            long length = this.parseRedisNumber(lineByteBuf);
            if (length < -1L) {
                throw new RedisCodecException("length: " + length + " (expected: >= " + -1 + ")");
            } else {
                switch(this.type) {
                case ARRAY_HEADER:
                    out.add(new ArrayHeaderRedisMessage(length));
                    this.resetDecoder();
                    return true;
                case BULK_STRING:
                    if (length > 536870912L) {
                        throw new RedisCodecException("length: " + length + " (expected: <= " + 536870912 + ")");
                    }

                    this.remainingBulkLength = (int)length;
                    return this.decodeBulkString(in, out);
                default:
                    throw new RedisCodecException("bad type: " + this.type);
                }
            }
        }
    }

    // 解码多行字符串
    private boolean decodeBulkString(ByteBuf in, List<Object> out) throws Exception {
        switch(this.remainingBulkLength) {
        case -1:
            out.add(FullBulkStringRedisMessage.NULL_INSTANCE);
            this.resetDecoder();
            return true;
        case 0:
            this.state = RedisDecoder.State.DECODE_BULK_STRING_EOL;
            return this.decodeBulkStringEndOfLine(in, out);
        default:
            out.add(new BulkStringHeaderRedisMessage(this.remainingBulkLength));
            this.state = RedisDecoder.State.DECODE_BULK_STRING_CONTENT;
            return this.decodeBulkStringContent(in, out);
        }
    }
```

## Netty 中 RESP 编码器实现

编码器，顾名思义，就是将对象根据 RESP 协议序列化成字节流发送到服务端。编码器的实现非常简单，不用考虑拆包等问题，就是分配一个 ByteBuf，然后将消息输出对象序列化的字节数组塞到 ByteBuf 中输出就可以了。

下面代码中就是 encode 方法直接调用 writeRedisMessage 方法，根据消息类型进行写 buffer 操作。

``` java
    @Override
    protected void encode(ChannelHandlerContext ctx, RedisMessage msg, List<Object> out) throws Exception {
        try {
            writeRedisMessage(ctx.alloc(), msg, out);
        } catch (CodecException e) {
            throw e;
        } catch (Exception e) {
            throw new CodecException(e);
        }
    }

    private void writeRedisMessage(ByteBufAllocator allocator, RedisMessage msg, List<Object> out) {
        // 判断消息类型，然后调用写相应消息的方法。
        if (msg instanceof InlineCommandRedisMessage) {
            writeInlineCommandMessage(allocator, (InlineCommandRedisMessage) msg, out);
        } else if (msg instanceof SimpleStringRedisMessage) {
            writeSimpleStringMessage(allocator, (SimpleStringRedisMessage) msg, out);
        } else if (msg instanceof ErrorRedisMessage) {
            writeErrorMessage(allocator, (ErrorRedisMessage) msg, out);
        } else if (msg instanceof IntegerRedisMessage) {
            writeIntegerMessage(allocator, (IntegerRedisMessage) msg, out);
        } else if (msg instanceof FullBulkStringRedisMessage) {
            writeFullBulkStringMessage(allocator, (FullBulkStringRedisMessage) msg, out);
        } else if (msg instanceof BulkStringRedisContent) {
            writeBulkStringContent(allocator, (BulkStringRedisContent) msg, out);
        } else if (msg instanceof BulkStringHeaderRedisMessage) {
            writeBulkStringHeader(allocator, (BulkStringHeaderRedisMessage) msg, out);
        } else if (msg instanceof ArrayHeaderRedisMessage) {
            writeArrayHeader(allocator, (ArrayHeaderRedisMessage) msg, out);
        } else if (msg instanceof ArrayRedisMessage) {
            writeArrayMessage(allocator, (ArrayRedisMessage) msg, out);
        } else {
            throw new CodecException("unknown message type: " + msg);
        }
    }
```

下面代码主要是实现对应消息按照 RESP 协议 进行序列化操作，具体就是上面楼主说的，分配一个 ByteBuf，然后将消息输出对象序列化的字节数组塞到 ByteBuf 中输出即可。

``` java
private static void writeInlineCommandMessage(ByteBufAllocator allocator, InlineCommandRedisMessage msg,
                                                 List<Object> out) {
        writeString(allocator, RedisMessageType.INLINE_COMMAND, msg.content(), out);
    }

    private static void writeSimpleStringMessage(ByteBufAllocator allocator, SimpleStringRedisMessage msg,
                                                 List<Object> out) {
        writeString(allocator, RedisMessageType.SIMPLE_STRING, msg.content(), out);
    }

    private static void writeErrorMessage(ByteBufAllocator allocator, ErrorRedisMessage msg, List<Object> out) {
        writeString(allocator, RedisMessageType.ERROR, msg.content(), out);
    }

    private static void writeString(ByteBufAllocator allocator, RedisMessageType type, String content,
                                    List<Object> out) {
        ByteBuf buf = allocator.ioBuffer(type.length() + ByteBufUtil.utf8MaxBytes(content) +
                                         RedisConstants.EOL_LENGTH);
        type.writeTo(buf);
        ByteBufUtil.writeUtf8(buf, content);
        buf.writeShort(RedisConstants.EOL_SHORT);
        out.add(buf);
    }

    private void writeIntegerMessage(ByteBufAllocator allocator, IntegerRedisMessage msg, List<Object> out) {
        ByteBuf buf = allocator.ioBuffer(RedisConstants.TYPE_LENGTH + RedisConstants.LONG_MAX_LENGTH +
                                         RedisConstants.EOL_LENGTH);
        RedisMessageType.INTEGER.writeTo(buf);
        buf.writeBytes(numberToBytes(msg.value()));
        buf.writeShort(RedisConstants.EOL_SHORT);
        out.add(buf);
    }

    private void writeBulkStringHeader(ByteBufAllocator allocator, BulkStringHeaderRedisMessage msg, List<Object> out) {
        final ByteBuf buf = allocator.ioBuffer(RedisConstants.TYPE_LENGTH +
                                        (msg.isNull() ? RedisConstants.NULL_LENGTH :
                                                        RedisConstants.LONG_MAX_LENGTH + RedisConstants.EOL_LENGTH));
        RedisMessageType.BULK_STRING.writeTo(buf);
        if (msg.isNull()) {
            buf.writeShort(RedisConstants.NULL_SHORT);
        } else {
            buf.writeBytes(numberToBytes(msg.bulkStringLength()));
            buf.writeShort(RedisConstants.EOL_SHORT);
        }
        out.add(buf);
    }

    private static void writeBulkStringContent(ByteBufAllocator allocator, BulkStringRedisContent msg,
                                               List<Object> out) {
        out.add(msg.content().retain());
        if (msg instanceof LastBulkStringRedisContent) {
            out.add(allocator.ioBuffer(RedisConstants.EOL_LENGTH).writeShort(RedisConstants.EOL_SHORT));
        }
    }

    private void writeFullBulkStringMessage(ByteBufAllocator allocator, FullBulkStringRedisMessage msg,
                                            List<Object> out) {
        if (msg.isNull()) {
            ByteBuf buf = allocator.ioBuffer(RedisConstants.TYPE_LENGTH + RedisConstants.NULL_LENGTH +
                                             RedisConstants.EOL_LENGTH);
            RedisMessageType.BULK_STRING.writeTo(buf);
            buf.writeShort(RedisConstants.NULL_SHORT);
            buf.writeShort(RedisConstants.EOL_SHORT);
            out.add(buf);
        } else {
            ByteBuf headerBuf = allocator.ioBuffer(RedisConstants.TYPE_LENGTH + RedisConstants.LONG_MAX_LENGTH +
                                                   RedisConstants.EOL_LENGTH);
            RedisMessageType.BULK_STRING.writeTo(headerBuf);
            headerBuf.writeBytes(numberToBytes(msg.content().readableBytes()));
            headerBuf.writeShort(RedisConstants.EOL_SHORT);
            out.add(headerBuf);
            out.add(msg.content().retain());
            out.add(allocator.ioBuffer(RedisConstants.EOL_LENGTH).writeShort(RedisConstants.EOL_SHORT));
        }
    }

    /**
     * Write array header only without body. Use this if you want to write arrays as streaming.
     */
    private void writeArrayHeader(ByteBufAllocator allocator, ArrayHeaderRedisMessage msg, List<Object> out) {
        writeArrayHeader(allocator, msg.isNull(), msg.length(), out);
    }

    /**
     * Write full constructed array message.
     */
    private void writeArrayMessage(ByteBufAllocator allocator, ArrayRedisMessage msg, List<Object> out) {
        if (msg.isNull()) {
            writeArrayHeader(allocator, msg.isNull(), RedisConstants.NULL_VALUE, out);
        } else {
            writeArrayHeader(allocator, msg.isNull(), msg.children().size(), out);
            for (RedisMessage child : msg.children()) {
                writeRedisMessage(allocator, child, out);
            }
        }
    }

    private void writeArrayHeader(ByteBufAllocator allocator, boolean isNull, long length, List<Object> out) {
        if (isNull) {
            final ByteBuf buf = allocator.ioBuffer(RedisConstants.TYPE_LENGTH + RedisConstants.NULL_LENGTH +
                                                   RedisConstants.EOL_LENGTH);
            RedisMessageType.ARRAY_HEADER.writeTo(buf);
            buf.writeShort(RedisConstants.NULL_SHORT);
            buf.writeShort(RedisConstants.EOL_SHORT);
            out.add(buf);
        } else {
            final ByteBuf buf = allocator.ioBuffer(RedisConstants.TYPE_LENGTH + RedisConstants.LONG_MAX_LENGTH +
                                                   RedisConstants.EOL_LENGTH);
            RedisMessageType.ARRAY_HEADER.writeTo(buf);
            buf.writeBytes(numberToBytes(length));
            buf.writeShort(RedisConstants.EOL_SHORT);
            out.add(buf);
        }
    }
```

## 小结

对于 Netty 源码，楼主一直是一种敬畏的态度，没想到今天竟然从另一个方面对 Netty 的冰山一角展开解读，毕竟万事开头难，有了这一次，希望之后可以更顺利，在技术成长的道路上一起加油。

## 参考链接

- <a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2018%2Fe687%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/article/2018/e687/">Redis 协议规范（译文）</a>
- <a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2018%2Fd5b3%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/article/2018/d5b3/">TCP 粘包问题浅析及其解决方案</a>
- <a href="https://juejin.cn/post/6844903648875528206" target="_blank" title="https://juejin.cn/post/6844903648875528206">基于 Netty 实现 Redis 协议的编码解码器</a>
