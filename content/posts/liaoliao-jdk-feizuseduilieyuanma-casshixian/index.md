---
aliases: ["/zh-cn/posts/liaoliao-jdk-feizuseduilieyuanma-casshixian/"]
categories: ["后端"]
title: "聊聊 JDK 非阻塞队列源码（CAS 实现）"
date: "2018-08-02T14:23:33+08:00"
tags: ["Java", "RxJava", "Java EE", "求职", "面试"]
summary: "正如上篇文章聊聊 JDK 阻塞队列源码（ReentrantLock 实现）所说，队列在我们现实生活中队列随处可见，最经典的就是去银行办理业务，超市买东西排队等。今天楼主要讲的就是 JDK 中安全队列的另一种实现使用 CAS 算法实现的安全队列。"
translationKey: "liaoliao-jdk-feizuseduilieyuanma-casshixian"
---

> 📌 本文原发布于掘金社区：[聊聊 JDK 非阻塞队列源码（CAS 实现）](https://juejin.cn/post/6844903650456780807)

正如上篇文章<a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2018%2F22ff%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/article/2018/22ff/">聊聊 JDK 阻塞队列源码（ReentrantLock 实现）</a>所说，队列在我们现实生活中随处可见，最经典的就是去银行办理业务，超市买东西排队等。今天楼主要讲的就是 JDK 中使用 CAS 算法实现的另一种安全队列。\
<span id="user-content-more"></span>

## [](#JDK-中的队列 "#JDK-中的队列")JDK 中的队列

在**JDK**中的队列都实现了 **java.util.Queue** 接口，下面就是楼主要说的无锁版本的队列实现：

| 队列名字              | 是否加锁 | 数据结构 | 关键技术点 | 是否有锁 | 是否有界 |
|-----------------------|----------|----------|------------|----------|----------|
| LinkedTransferQueue   | 否       | 链表     | CAS        | 无锁     | 无界     |
| ConcurrentLinkedQueue | 否       | 链表     | CAS        | 无锁     | 无界     |

## [](#LinkedTransferQueue-源码分析 "#LinkedTransferQueue-源码分析")LinkedTransferQueue 源码分析

LinkedTransferQueue 的原理就是通过使用原子变量 compare and swap（简称“CAS”）这种不加锁的方式来实现并发控制，LinkedTransferQueue 是一个无界的安全队列，其长度可以无限延伸，当然其带来的问题也是显而易见的。\

### [](#主要方法源码实现 "#主要方法源码实现")主要方法源码实现

1.  add：添加元素到队列里，添加成功返回 true；\
2.  offer：添加元素到队列里，添加成功返回 true，添加失败返回 false；\
3.  put：添加元素到队列里，如果容量满了会阻塞直到容量不满；\
4.  poll：删除队列头部元素，如果队列为空，返回 null。否则返回元素；\
5.  take：删除队列头部元素，如果队列为空，一直阻塞到队列有元素并删除。\

`add`方法：\
\

    public boolean add(E e) {
        xfer(e, true, ASYNC, 0);
        return true;
    }

`offer`方法：\
\

    public boolean offer(E e) {
        xfer(e, true, ASYNC, 0);
        return true;
    }

`poll`方法：\
\

    public E poll() {
        return xfer(null, false, NOW, 0);
    }

`take`方法：\
\

    public E take() throws InterruptedException {
        E e = xfer(null, false, SYNC, 0);
        if (e != null)
            return e;
        Thread.interrupted();
        throw new InterruptedException();
    }

从上面代码中可以看出，这些方法最终都指向了 `xfer` 方法，只不过传入的参数不同。

    /**
     * Implements all queuing methods. See above for explanation.
     *
     * @param e the item or null for take
     * @param haveData true if this is a put, else a take
     * @param how NOW, ASYNC, SYNC, or TIMED
     * @param nanos timeout in nanosecs, used only if mode is TIMED
     * @return an item if matched, else e
     * @throws NullPointerException if haveData mode but e is null
     */

从源码的 doc 注释中可以知道\
第一个参数，如果是 put 类型，就是实际的值，反之就是 null。\
第二个参数，是否包含数据，put 类型就是 true，take 就是 false。\
第三个参数，执行类型，有立即返回的 NOW，有异步的 ASYNC，有阻塞的 SYNC，有带超时的 TIMED。\
第四个参数，只有在 TIMED 类型才有作用。

接下来我们来看看 `xfer` 到底是何方神圣\

    private E xfer(E e, boolean haveData, int how, long nanos) {
        if (haveData && (e == null))
            throw new NullPointerException();
        Node s = null;                        // the node to append, if needed

        retry:
        for (;;) {                            // restart on append race
            // 从  head 开始
            for (Node h = head, p = h; p != null;) { // find & match first node
                // head 的类型。
                boolean isData = p.isData;
                // head 的数据
                Object item = p.item;
                // item != null 有 2 种情况,一是 put 操作, 二是 take 的 itme 被修改了(匹配成功)
                // (itme != null) == isData 要么表示 p 是一个 put 操作, 要么表示 p 是一个还没匹配成功的 take 操作
                if (item != p && (item != null) == isData) { 
                    // 如果当前操作和 head 操作相同，就没有匹配上，结束循环，进入下面的 if 块。
                    if (isData == haveData)   // can't match
                        break;
                    // 如果操作不同,匹配成功, 尝试替换 item 成功,
                    if (p.casItem(item, e)) { // match
                        // 更新 head
                        for (Node q = p; q != h;) {
                            Node n = q.next;  // update by 2 unless singleton
                            if (head == h && casHead(h, n == null ? q : n)) {
                                h.forgetNext();
                                break;
                            }                 // advance and retry
                            if ((h = head)   == null ||
                                (q = h.next) == null || !q.isMatched())
                                break;        // unless slack < 2
                        }
                        // 唤醒原 head 线程.
                        LockSupport.unpark(p.waiter);
                        return LinkedTransferQueue.<E>cast(item);
                    }
                }
                // 找下一个
                Node n = p.next;
                p = (p != n) ? n : (h = head); // Use head if p offlist
            }
            // 如果这个操作不是立刻就返回的类型    
            if (how != NOW) {                 // No matches available
                // 且是第一次进入这里
                if (s == null)
                    // 创建一个 node
                    s = new Node(e, haveData);
                // 尝试将 node 追加对队列尾部，并返回他的上一个节点。
                Node pred = tryAppend(s, haveData);
                // 如果返回的是 null, 表示不能追加到 tail 节点,因为 tail 节点的模式和当前模式相反.
                if (pred == null)
                    // 重来
                    continue retry;           // lost race vs opposite mode
                // 如果不是异步操作(即立刻返回结果)
                if (how != ASYNC)
                    // 阻塞等待匹配值
                    return awaitMatch(s, pred, e, (how == TIMED), nanos);
            }
            return e; // not waiting
        }
    }

代码有点长，其实逻辑很简单。就是找到 `head` 节点，如果 `head` 节点是匹配的操作，就直接赋值，如果不是，添加到队列中。\
注意：队列中永远只有一种类型的操作，要么是 `put` 类型，要么是 `take` 类型。

## [](#ConcurrentLinkedQueue-源码分析 "#ConcurrentLinkedQueue-源码分析")ConcurrentLinkedQueue 源码分析

与 `LinkedTransferQueue` 一样，ConcurrentLinkedQueue 也是采用原子变量实现的并发控制，`ConcurrentLinkedQueue` 是一个基于链接节点的无界线程安全队列，它采用先进先出的规则对节点进行排序，当我们添加一个元素的时候，它会将该元素添加到队列的尾部，当我们获取一个元素时，它会返回队列头部的元素。它采用了“wait－free”算法来实现。

### [](#主要方法源码实现-1 "#主要方法源码实现-1")主要方法源码实现

1.  add：添加元素到队列里，添加成功返回 true；\
2.  offer：添加元素到队列里，添加成功返回 true，添加失败返回 false；\
3.  put：添加元素到队列里，如果容量满了会阻塞直到容量不满；\
4.  poll：删除队列头部元素，如果队列为空，返回 null。否则返回元素；\
5.  remove：基于对象找到对应的元素，并删除。删除成功返回 true，否则返回 false；\

`add`方法：\
\

    public boolean add(E e) {
        return offer(e);
    }

`offer`方法：\
\
`ConcurrentLinkedQueue`是无界的，所以`offer`永远返回 true，不能通过返回值来判断是否入队成功，

    public boolean offer(E e) {
        // 校验是否为空
        checkNotNull(e);
        //入队前，创建一个入队节点
        final Node<E> newNode = new Node<E>(e);

        //循环CAS直到入队成功。
        // 1、根据tail节点定位出尾节点（last node）；
        // 2、将新节点置为尾节点的下一个节点，
        // 3、更新尾节点casTail。
        for (Node<E> t = tail, p = t;;) {
            Node<E> q = p.next;
            //判断p是不是尾节点，tail节点不一定是尾节点，判断是不是尾节点的依据是该节点的next是不是null
            if (q == null) { 
                // p is last node
                if (p.casNext(null, newNode)) {
                     //设置P节点的下一个节点为新节点，如果p的next为null，说明p是尾节点，casNext返回true；
                     // 如果p的next不为null，说明有其他线程更新过队列的尾节点，casNext返回false。
                    // Successful CAS is the linearization point
                    // for e to become an element of this queue,
                    // and for newNode to become "live".
                    if (p != t) // hop two nodes at a time
                        casTail(t, newNode);  // Failure is OK.
                    return true;
                }
                // Lost CAS race to another thread; re-read next
            }
            else if (p == q)
                //p节点是null的head节点刚好被出队，更新head节点时h.lazySetNext(h)把旧的head节点指向自己
                // We have fallen off list.  If tail is unchanged, it
                // will also be off-list, in which case we need to
                // jump to head, from which all live nodes are always
                // reachable.  Else the new tail is a better bet.
                p = (t != (t = tail)) ? t : head;
            else
                // Check for tail updates after two hops.
                //判断tail节点有没有被更新，如果没被更新，1）p=q：p指向p.next继续寻找尾节点;
                //如果被更新了，2)p=t:P赋值为新的tail节点
                p = (p != t && t != (t = tail)) ? t : q;
        }
    }

`poll`方法：\
\

    public E poll() {
        restartFromHead:
        //两层循环
        for (;;) {
            for (Node<E> h = head, p = h, q;;) {
                E item = p.item;

                if (item != null && p.casItem(item, null)) {
                    // Successful CAS is the linearization point
                    // for item to be removed from this queue.
                    if (p != h) // hop two nodes at a time
                        updateHead(h, ((q = p.next) != null) ? q : p);
                    return item;
                }
                //队列为空，更新head节点
                else if ((q = p.next) == null) {
                    updateHead(h, p);
                    return null;
                }
                else if (p == q)
                    //p节点是null的head节点刚好被出队，更新head节点时h.lazySetNext(h);把旧的head节点指向自己。
                    //重新从head节点开始
                    continue restartFromHead;
                else
                    p = q;    //将p执行p的下一个节点
            }
        }
    }

    //更新head节点
    final void updateHead(Node<E> h, Node<E> p) {
        //通过CAS将head更新为P
        if (h != p && casHead(h, p))
            h.lazySetNext(h);//把旧的head节点指向自己
    }

    void lazySetNext(Node<E> val) {
        UNSAFE.putOrderedObject(this, nextOffset, val);
    }

`remove`方法：\
\

    public boolean remove(Object o) {
        if (o != null) {
            Node<E> next, pred = null;
            // 循环CAS直到删除节点
            for (Node<E> p = first(); p != null; pred = p, p = next) {
                boolean removed = false;
                E item = p.item;
                if (item != null) {
                    if (!o.equals(item)) {
                        next = succ(p);
                        continue;
                    }
                    // 通过CAS删除节点
                    removed = p.casItem(item, null);
                }

                next = succ(p);
                if (pred != null && next != null) // unlink
                    pred.casNext(p, next);
                if (removed)
                    return true;
            }
        }
        return false;
    }

## [](#小结 "#小结")小结

本文主要介绍了两种 CAS 算法实现的安全队列，然而在稳定性要求较高的系统中，为了防止生产者速度过快，导致内存溢出，通常是不建议选择无界队列的。当然楼主水平有限，文章中不免有纰漏，望小伙伴谅解并指出，在技术的道路上一起成长。

## [](#参考链接 "#参考链接")参考链接

- <a href="https://link.juejin.cn?target=https%3A%2F%2Ftech.meituan.com%2Fdisruptor.html" target="_blank" data-ref="nofollow noopener noreferrer" title="https://tech.meituan.com/disruptor.html">高性能队列——Disruptor</a>
- <a href="https://link.juejin.cn?target=http%3A%2F%2Fifeve.com%2Fconcurrentlinkedqueue%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://ifeve.com/concurrentlinkedqueue/">聊聊并发（六）ConcurrentLinkedQueue 的实现原理分析</a>

作 者：haifeiWu\
原文链接：<a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2018%2Fefed%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/article/2018/efed/">www.hchstudio.cn/article/201…</a>\
版权声明：非特殊声明均为本站原创作品，转载时请注明作者和原文链接。
