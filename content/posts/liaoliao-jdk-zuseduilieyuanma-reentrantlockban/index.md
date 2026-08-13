---
aliases: ["/posts/liao-liao--jdk--zu-se-dui-lie-yuan-ma--reentrantlock-shi-xian/"]
categories: ["后端"]
title: "聊聊 JDK 阻塞队列源码（ReentrantLock 版）"
date: "2018-08-01T10:14:44+08:00"
tags: ["Java", "Linux"]
summary: "项目中用到了一个叫做 Disruptor 的队列，今天楼主并不是要介绍 Disruptor 而是想巩固一下基础扒一下 JDK 中的阻塞队列，听到队列相信大家对其并不陌生，在我们现实生活中队列随处可见，最经典的就是去银行办理业务等。"
---

> 📌 本文原发布于掘金社区：[聊聊 JDK 阻塞队列源码（ReentrantLock 版）](https://juejin.cn/post/6844903649542406152)

项目中用到了一个叫做 Disruptor 的队列，今天楼主并不是要介绍 Disruptor，而是想巩固一下基础，扒一下 JDK 中的阻塞队列，听到队列相信大家对其并不陌生，在我们现实生活中队列随处可见，最经典的就是去银行办理业务等。\
<span id="user-content-more"></span>\
当然在计算机世界中，队列是一种数据结构，队列采用的是 FIFO(first in first out)，新元素（等待进入队列的元素）总是被插入到尾部，而读取的时候总是从头部开始读取。在计算机中队列一般用来做排队(如线程池的等待排队，锁的等待排队)，用来做解耦（生产者消费者模式），异步等等。

## [](#JDK-中的队列 "#JDK-中的队列")JDK 中的队列

在**JDK**中的队列都实现了 **java.util.Queue** 接口，这些队列又分为两类，一类是线程不安全的，ArrayDeque，LinkedList 等等，还有一类在**java.util.concurrent**包下，属于线程安全，而在我们真实的环境中，我们的机器都是多线程的，当多线程对同一个队列进行操作时，如果使用线程不安全的队列，会出现数据丢失等无法预料的问题，所以我们这个时候只能选择线程安全的队列。下面是我们今天要探讨的两个队列

| 队列名字            | 是否加锁 | 数据结构  | 关键技术点    | 是否有锁 | 是否有界 |
|---------------------|----------|-----------|---------------|----------|----------|
| ArrayBlockingQueue  | 是       | 数组 array | ReentrantLock | 有锁     | 有界     |
| LinkedBlockingQueue | 是       | 链表      | ReentrantLock | 有锁     | 有界     |

## [](#ArrayBlockingQueue-源码分析 "#ArrayBlockingQueue-源码分析")ArrayBlockingQueue 源码分析

ArrayBlockingQueue 的原理就是使用一个可重入锁（ReentrantLock ）和这个锁生成的两个条件对象进行并发控制，ArrayBlockingQueue 是一个有界的阻塞队列，初始化的时候必须要指定队列长度，且指定长度之后不允许修改。\

### [](#成员变量属性 "#成员变量属性")成员变量属性

    /** The queued items item的集合 */
       final Object[] items;

       /** items index for next take, poll, peek or remove 取出数据的索引 */
       int takeIndex;

       /** items index for next put, offer, or add 添加数据的索引 */
       int putIndex;

       /** Number of elements in the queue 队列元素的个数 */
       int count;

       /** Main lock guarding all access 可重入的锁 */
       final ReentrantLock lock;

       /** Condition for waiting takes 队列为空条件等待对象 */
       private final Condition notEmpty;

       /** Condition for waiting puts 队列满条件等待对象 */
       private final Condition notFull;

### [](#主要方法源码实现 "#主要方法源码实现")主要方法源码实现

1.  add：添加元素到队列里，添加成功返回 true，由于容量满了添加失败会抛出`IllegalStateException`异常；\
2.  offer：添加元素到队列里，添加成功返回 true，添加失败返回 false；\
3.  put：添加元素到队列里，如果容量满了会阻塞直到容量不满；\
4.  poll：删除队列头部元素，如果队列为空，返回 null。否则返回元素；\
5.  remove：根据传入的对象找到对应的元素，并删除。删除成功返回 true，否则返回 false；\
6.  take：删除队列头部元素，如果队列为空，会一直阻塞，直到队列有元素时再删除。\

add 方法：\

    public boolean add(E e) {
        if (offer(e))
            return true;
        else
            throw new IllegalStateException("Queue full");
    }

offer 方法：\

    public boolean offer(E e) {
        checkNotNull(e);
        final ReentrantLock lock = this.lock;
        lock.lock();
        try {
            if (count == items.length)
                return false;
            else {
                insert(e);
                return true;
            }
        } finally {
            lock.unlock();
        }
    }

我们可以看到，如果队列满了则返回 false，如果没有满则调用 insert。整个方法通过可重入锁来加锁，并最终释放锁。

接着看一下`insert`方法：\
\

    private void insert(E x) {
        items[putIndex] = x; // 元素添加到数组里
        putIndex = inc(putIndex); // 放数据索引+1，当索引满了变成0
        ++count; // 元素个数+1
        notEmpty.signal(); // 使用条件对象notEmpty通知
    }

这里`insert`被调用时，就会唤醒在`notEmpty`上等待的线程执行`take`操作。\

再看一下`put`方法：\

    public void put(E e) throws InterruptedException {
        checkNotNull(e); // 不允许元素为空
        final ReentrantLock lock = this.lock;
        lock.lockInterruptibly(); // 加锁，保证调用put方法的时候只有1个线程
        try {
            while (count == items.length) // 如果队列满了，阻塞当前线程，while用来防止假唤醒
                notFull.await(); // 线程阻塞并被挂起，同时释放锁
            insert(e); // 调用insert方法
        } finally {
            lock.unlock(); // 释放锁，让其他线程可以调用put方法
        }
    }

通过上面代码我们可以知道，`add`方法和`offer`方法不会阻塞线程，`put`方法如果队列满了会阻塞线程，直到有线程消费了队列里的数据才有可能被唤醒。\

紧接着我们看一下`poll`方法：\

    public E poll() {
        final ReentrantLock lock = this.lock;
        lock.lock(); // 加锁，保证调用poll方法的时候只有1个线程
        try {
            return (count == 0) ? null : extract(); // 如果队列里没元素了，返回null，否则调用extract方法
        } finally {
            lock.unlock(); // 释放锁，让其他线程可以调用poll方法
        }
    }

看看这个`extract`方法，extract 翻译过来就是提取的意思：\

    private E extract() {
        final Object[] items = this.items;
        E x = this.<E>cast(items[takeIndex]); // 得到取索引位置上的元素
        items[takeIndex] = null; // 对应取索引上的数据清空
        takeIndex = inc(takeIndex); // 取数据索引+1，当索引满了变成0
        --count; // 元素个数-1
        notFull.signal(); // 使用条件对象notFull通知，原理同上面的insert中
        return x; // 返回元素
    }

看一下`take`方法：\

    public E take() throws InterruptedException {
        final ReentrantLock lock = this.lock;
        lock.lockInterruptibly(); // 加锁，保证调用take方法的时候只有1个线程
        try {
            while (count == 0) // 如果队列空，阻塞当前线程，并加入到条件对象notEmpty的等待队列里
                notEmpty.await(); // 线程阻塞并被挂起，同时释放锁
            return extract(); // 调用extract方法
        } finally {
            lock.unlock(); // 释放锁，让其他线程可以调用take方法
        }
    }

`remove`方法：\

    public boolean remove(Object o) {
        if (o == null) return false;
        final Object[] items = this.items;
        final ReentrantLock lock = this.lock;
        lock.lock(); // 加锁，保证调用remove方法的时候只有1个线程
        try {
            for (int i = takeIndex, k = count; k > 0; i = inc(i), k--) { // 遍历元素
                if (o.equals(items[i])) { // 两个对象相等的话
                    removeAt(i); // 调用removeAt方法
                    return true; // 删除成功，返回true
                }
            }
            return false; // 删除成功，返回false
        } finally {
            lock.unlock(); // 释放锁，让其他线程可以调用remove方法
        }
    }

再看一下`removeAt`方法：\

    private void removeAt(int i) {
        final Object[] items = this.items;
        if (i == takeIndex) { 
            // 如果要删除数据的索引是取索引位置，直接删除取索引位置上的数据，然后取索引+1即可
            items[takeIndex] = null;
            takeIndex = inc(takeIndex);
        } else { 
            // 如果要删除数据的索引不是取索引位置，移动元素元素，更新取索引和放索引的值
            for (;;) {
                int nexti = inc(i);
                if (nexti != putIndex) {
                    items[i] = items[nexti];
                    i = nexti;
                } else {
                    items[i] = null;
                    putIndex = i;
                    break;
                }
            }
        }
        --count; // 元素个数-1
        notFull.signal(); // 使用条件对象notFull通知
    }

[](#LinkedBlockingQueue-源码分析 "#LinkedBlockingQueue-源码分析")LinkedBlockingQueue 源码分析\
----------------------------------------------------------------------------------------------

`LinkedBlockingQueue`是一个使用链表完成队列操作的阻塞队列。**链表是单向链表，而不是双向链表**。

### [](#成员变量属性-1 "#成员变量属性-1")成员变量属性

    /** The capacity bound, or Integer.MAX_VALUE if none 容量大小 */
    private final int capacity;

       /** Current number of elements 元素个数，因为有2个锁，存在竞态条件，使用AtomicInteger */
       private final AtomicInteger count = new AtomicInteger(0);

       /**
        * Head of linked list.
        * Invariant: head.item == null
        * 头结点
        */
       private transient Node<E> head;

       /**
        * Tail of linked list.
        * Invariant: last.next == null
        * 尾节点
        */
       private transient Node<E> last;

       /** Lock held by take, poll, etc 获取元素的锁 */
       private final ReentrantLock takeLock = new ReentrantLock();

       /** Wait queue for waiting takes 取元素的条件对象 */
       private final Condition notEmpty = takeLock.newCondition();

       /** Lock held by put, offer, etc 放元素的锁 */
       private final ReentrantLock putLock = new ReentrantLock();

       /** Wait queue for waiting puts 添加元素的条件对象 */
       private final Condition notFull = putLock.newCondition();

### [](#主要方法源码实现-1 "#主要方法源码实现-1")主要方法源码实现

由于文章篇幅问题，对于`LinkedBlockingQueue`，我们主要分析以下几个方法：

1.  offer：添加元素到队列里，添加成功返回 true，添加失败返回 false；\
2.  put：添加元素到队列里，如果容量满了会阻塞直到容量不满；\
3.  poll：删除队列头部元素，如果队列为空，返回 null。否则返回元素；\
4.  remove：根据传入的对象找到对应的元素，并删除。删除成功返回 true，否则返回 false；\
5.  take：删除队列头部元素，如果队列为空，会一直阻塞，直到队列有元素时再删除。\

`offer`方法：

    public boolean offer(E e) {
        if (e == null) throw new NullPointerException(); // 不允许空元素
        final AtomicInteger count = this.count;
        if (count.get() == capacity) // 如果容量满了，返回false
            return false;
        int c = -1;
        Node<E> node = new Node(e); // 容量没满，以新元素构造节点
        final ReentrantLock putLock = this.putLock;
        putLock.lock(); // 放锁加锁，保证调用offer方法的时候只有1个线程
        try {
            // 再次判断容量是否已满，因为可能取元素锁在进行消费数据，没满的话继续执行
            if (count.get() < capacity) { 
                enqueue(node); // 节点添加到链表尾部
                c = count.getAndIncrement(); // 元素个数+1
                if (c + 1 < capacity) // 如果容量还没满
                    notFull.signal(); // 在放锁的条件对象notFull上唤醒正在等待的线程，表示可以再次往队列里面加数据
            }
        } finally {
            putLock.unlock(); // 释放放锁，让其他线程可以调用offer方法
        }
        // 由于存在放元素锁和取元素锁，这里可能取元素锁一直在消费数据，count会变化。这里的if条件表示如果队列中还有1条数据
        if (c == 0) 
            // 在拿锁的条件对象notEmpty上唤醒正在等待的1个线程，表示队列里还有1条数据，可以进行消费
            signalNotEmpty(); 
        return c >= 0; // 添加成功返回true，否则返回false
    }

`put`方法：\

    public void put(E e) throws InterruptedException {
        if (e == null) throw new NullPointerException(); // 不允许空元素
        int c = -1;
        Node<E> node = new Node(e); // 以新元素构造节点
        final ReentrantLock putLock = this.putLock;
        final AtomicInteger count = this.count;
        putLock.lockInterruptibly(); // 放锁加锁，保证调用put方法的时候只有1个线程
        try {
            while (count.get() == capacity) { // 如果容量满了
                notFull.await(); // 阻塞并挂起当前线程
            }
            enqueue(node); // 节点添加到链表尾部
            c = count.getAndIncrement(); // 元素个数+1
            if (c + 1 < capacity) // 如果容量还没满
                // 在放锁的条件对象notFull上唤醒正在等待的线程，表示可以再次往队列里面加数据了，队列还没满
                notFull.signal();
        } finally {
            putLock.unlock(); // 释放放锁，让其他线程可以调用put方法
        }
        // 由于存在放锁和拿锁，这里可能拿锁一直在消费数据，count会变化。这里的if条件表示如果队列中还有1条数据
        if (c == 0)
            // 在拿锁的条件对象notEmpty上唤醒正在等待的1个线程，表示队列里还有1条数据，可以进行消费
            signalNotEmpty();
    }

`poll`方法：\

    public E poll() {
        final AtomicInteger count = this.count;
        if (count.get() == 0) // 如果元素个数为0
            return null; // 返回null
        E x = null;
        int c = -1;
        final ReentrantLock takeLock = this.takeLock;
        takeLock.lock(); // 拿锁加锁，保证调用poll方法的时候只有1个线程
        try {
            if (count.get() > 0) { // 判断队列里是否还有数据
                x = dequeue(); // 删除头结点
                c = count.getAndDecrement(); // 元素个数-1
                if (c > 1) // 如果队列里还有元素
                    // 在拿锁的条件对象notEmpty上唤醒正在等待的线程，表示队列里还有数据，可以再次消费
                    notEmpty.signal();
            }
        } finally {
            takeLock.unlock(); // 释放拿锁，让其他线程可以调用poll方法
        }
        // 由于存在放锁和拿锁，这里可能放锁一直在添加数据，count会变化。这里的if条件表示如果队列中还可以再插入数据
        if (c == capacity)
            // 在放锁的条件对象notFull上唤醒正在等待的1个线程，表示队列里还能再次添加数据
            signalNotFull(); 
        return x;
    }

`take`方法：\

    public E take() throws InterruptedException {
        E x;
        int c = -1;
        final AtomicInteger count = this.count;
        final ReentrantLock takeLock = this.takeLock;
        takeLock.lockInterruptibly(); // 拿锁加锁，保证调用take方法的时候只有1个线程
        try {
            while (count.get() == 0) { // 如果队列里已经没有元素了
                notEmpty.await(); // 阻塞并挂起当前线程
            }
            x = dequeue(); // 删除头结点
            c = count.getAndDecrement(); // 元素个数-1
            if (c > 1) // 如果队列里还有元素
                // 在拿锁的条件对象notEmpty上唤醒正在等待的线程，表示队列里还有数据，可以再次消费
                notEmpty.signal(); 
        } finally {
            takeLock.unlock(); // 释放拿锁，让其他线程可以调用take方法
        }
        // 由于存在放锁和拿锁，这里可能放锁一直在添加数据，count会变化。这里的if条件表示如果队列中还可以再插入数据
        if (c == capacity) 
            // 在放锁的条件对象notFull上唤醒正在等待的1个线程，表示队列里还能再次添加数据
            signalNotFull(); 
        return x;
    }

`remove`方法：\

    public boolean remove(Object o) {
        if (o == null) return false;
        fullyLock(); // remove操作要移动的位置不固定，对读锁写锁都进行加锁
        try {
            for (Node<E> trail = head, p = trail.next; // 从链表头结点开始遍历
                p != null;
                trail = p, p = p.next) {
                if (o.equals(p.item)) { // 判断是否找到对象
                    unlink(p, trail); // 修改节点的链接信息，同时调用notFull的signal方法
                    return true;
                }
            }
            return false;
        } finally {
            fullyUnlock(); // 2个锁解锁
        }
    }

紧接着来看一下 `fullyLock`与`fullyUnlock`方法：\

    /**
     * Locks to prevent both puts and takes.
     */
     void fullyLock() {
         putLock.lock();
         takeLock.lock();
     }

     /**
      * Unlocks to allow both puts and takes.
      */
     void fullyUnlock() {
         takeLock.unlock();
         putLock.unlock();
     }

`LinkedBlockingQueue`的 take 方法在没有数据的情况下会阻塞，`poll`方法删除链表头结点，remove 方法删除指定的对象。\

需要注意的是`remove`方法由于要删除的数据的位置不确定，需要 2 个锁同时加锁。\

## [](#小结 "#小结")小结

文章有点长，JDK 中的阻塞队列线程安全的主要有`ArrayBlockingQueue`，`LinkedBlockingQueue`，`LinkedTransferQueue`，`DelayQueue`四种，今天楼主把`ArrayBlockingQueue`，`LinkedBlockingQueue`放在一起介绍，主要原因是这两者都是使用可重入锁 `ReentrantLock`实现线程安全的。\
当然二者也有很大的不同，主要是：

1，`ArrayBlockingQueue`只有 1 个锁，添加数据和删除数据的时候只能有 1 个被执行，不允许并行执行。\
而`LinkedBlockingQueue`有 2 个锁，放元素锁和取元素锁，添加数据和删除数据是可以并行进行的，当然添加数据和删除数据的时候只能有 1 个线程各自执行。\

2，`ArrayBlockingQueue`中放入数据阻塞的时候，需要消费数据才能唤醒。\
而`LinkedBlockingQueue`中放入数据阻塞的时候，因为它内部有 2 个锁，可以并行执行放入数据和消费数据，不仅在消费数据的时候会唤醒因插入而阻塞的线程，同时在插入的时候如果容量还没满，也会唤醒因插入而阻塞的线程。\

## [](#参考链接 "#参考链接")参考链接

- <a href="https://juejin.cn/post/6844903648875528206" target="_blank" title="https://juejin.cn/post/6844903648875528206">还在用阻塞队列？Disruptor 了解一下？</a>

作 者：haifeiWu\
原文链接：<a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2018%2F22ff%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/article/2018/22ff/">www.hchstudio.cn/article/201…</a>\
版权声明：非特殊声明均为本站原创作品，转载时请注明作者和原文链接。
