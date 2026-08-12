---
categories: ["ThreadPoolExecutor"]
title: "ThreadPoolExecutor 的简单梳理"
date: "2020-01-19T00:00:00+08:00"
tags: ["Android", "Docker", "Go", "Java", "Kafka", "Kotlin", "MySQL", "Nginx", "Python", "Raft", "Redis", "Shell", "Spring-Boot", "WebFlux", "go", "golang", "netty", "web", "学习笔记", "工具", "性能优化", "性能测试", "总结", "散列表", "旅游日记", "源码", "源码解析", "算法", "设计模式", "译文", "配置中心", "问题排查"]
summary: "还是楼主惯用的论述三连问，先问是什么，再问为什么，最后祭除终极大杀器 just do it …… what ? 那么什么是线程池呢？总的来说，线程池是一种线程使用模式。线程的频繁创建于调度会带来调度开销，进而影响缓存局部性和整体性能。而线程"
translationKey: "threadpoolexecutor--de-jian-dan-shu-li"
---

> 📌 本文原发布于代码星冰乐：[ThreadPoolExecutor 的简单梳理](https://changhuin.github.io/article/2020/c5a/)

还是楼主惯用的论述三连问，先问是什么，再问为什么，最后祭除终极大杀器 `just do it` ……

## what ?

那么什么是线程池呢？总的来说，线程池是一种线程使用模式。线程的频繁创建于调度会带来调度开销，进而影响缓存局部性和整体性能。而线程池维护着多个线程，等待着监督管理者分配可并发执行的任务。这避免了在处理短时间任务时创建与销毁线程的代价。线程池不仅能够保证内核的充分利用，还能防止过分调度。可用线程数量应该取决于可用的并发处理器、处理器内核、内存、网络sockets等的数量。

## why ?

上面说的是整个线程池的总体概念，当然 `Java` 中的线程池也是基于相同的理念设计的。在 `Java` 线程池可以提高线程复用，又可以固定最大线程使用量，防止无限制地创建线程。当程序提交一个任务需要一个线程时，会去线程池中查找是否有空闲的线程，若有，则直接使用线程池中的线程工作，若没有，会去判断当前已创建的线程数量是否超过最大线程数量，如未超过，则创建新线程，如已超过，则进行排队等待或者直接抛出异常。如下图所示\

总的来说，线程池就是把资源池化，预先准备好，以避免不必要额外开销。

## how ?

`Java` 提供了一套 `Executor` 框架，根据常用的场景对 `ThreadPoolExecutor` 类做了简单的封装，当然这样做的话难免有些束手束脚，所以大部分情况下都是根据自己的业务需求直接调用 `ThreadPoolExecutor` 实现自己的线程池。\

这个框架中包括了 `ScheduledThreadPoolExecutor` 和 `ThreadPoolExecutor` 两个核心线程池。前者是用来定时执行任务，后者是用来执行被提交的任务。因为这两个线程池的原理是一样的，都是调用底层的 `ThreadPoolExecutor`，下面我们就重点看看 ThreadPoolExecutor 类是如何实现线程池的。\

    public ThreadPoolExecutor(int corePoolSize,//线程池的核心线程数量
                              int maximumPoolSize,//线程池的最大线程数
                              long keepAliveTime,//当线程数大于核心线程数时，多余的空闲线程存活的最长时间
                              TimeUnit unit,//时间单位
                              BlockingQueue<Runnable> workQueue,//任务队列，用来储存等待执行任务的队列
                              ThreadFactory threadFactory,//线程工厂，用来创建线程，一般默认即可
                              RejectedExecutionHandler handler) //拒绝策略，当提交的任务过多而不能及时处理时，我们可以定制策略来处理任务

通过上面代码，我们发现线程池有两个线程数的设置，一个为核心线程数，一个为最大线程数。在创建完线程池之后，默认情况下，线程池中并没有任何线程，等到有任务来才创建线程去执行任务。

当创建的线程数等于 `corePoolSize` 时，提交的任务会被加入到设置的阻塞队列中。当队列满了，会创建线程执行任务，直到线程池中的数量等于 `maximumPoolSize`。当线程数量已经等于 `maximumPoolSize` 时， 新提交的任务无法加入到等待队列，也无法创建非核心线程直接执行，当我们又没有为线程池设置具体的拒绝策略时，线程池就会抛出 `RejectedExecutionException` 异常，即线程池拒绝接受当前提交的任务。

当线程池中创建的线程数量超过设置的 `corePoolSize`，在某些线程处理完任务后，如果等待 `keepAliveTime` 时间后仍然没有新的任务分配给它，那么这个线程将会被回收。线程池回收线程时，会对所谓的“核心线程”和“非核心线程”一视同仁，直到线程池中线程的数量等于设置的 `corePoolSize` 参数，回收过程才会停止。从下面代码中可以看出\

    public void setCorePoolSize(int corePoolSize) {
        if (corePoolSize < 0 || maximumPoolSize < corePoolSize)
            throw new IllegalArgumentException();
        int delta = corePoolSize - this.corePoolSize;
        this.corePoolSize = corePoolSize;
        if (workerCountOf(ctl.get()) > corePoolSize)
            interruptIdleWorkers();
        else if (delta > 0) {
            int k = Math.min(delta, workQueue.size());
            while (k-- > 0 && addWorker(null, true)) {
                if (workQueue.isEmpty())
                    break;
            }
        }
    }

## 小结

到目前为止，楼主只是围绕 `ThreadPoolExecutor` 的构造方法，简单阐述了下 Java 中的线程池实现的基本逻辑，想要更深入了理解，也可以尝试在阅读完 `JDK` 的线程池实现源码之后造个轮子。

