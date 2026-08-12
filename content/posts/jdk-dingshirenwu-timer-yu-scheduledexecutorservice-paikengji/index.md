---
aliases: ["/zh-cn/posts/jdk-dingshirenwu-timer-yu-scheduledexecutorservice-paikengji/"]
categories: ["后端"]
title: "JDK 定时任务 Timer 与 ScheduledExecutorService 排坑记录"
date: "2018-07-18T19:12:40+08:00"
tags: ["Java", "Linux"]
summary: "正在认真敲代码的楼主，突然收到数据维护系统发过来的报警邮件说楼主凌晨跑的定时任务没有成功，于是便开始了楼主今天的找坑填坑的过程。"
translationKey: "jdk-dingshirenwu-timer-yu-scheduledexecutorservice-paikengji"
---

> 📌 本文原发布于掘金社区：[JDK 定时任务 Timer 与 ScheduledExecutorService 排坑记录](https://juejin.cn/post/6844903640365285389)

正在认真敲代码的楼主，突然收到数据维护系统发过来的报警邮件说楼主凌晨跑的定时任务没有成功，于是便开始了楼主今天的找坑填坑的过程。\
<span id="user-content-more"></span>

## [](#定时任务，关于-Timer-与-ScheduledExecutorService-的抉择 "#定时任务，关于-Timer-与-ScheduledExecutorService-的抉择")定时任务，关于 Timer 与 ScheduledExecutorService 的抉择

这事肯定会有小伙伴说了为啥不用 Quartz 啊，因为楼主的庙小啊，就几个定时任务而已 Quartz 太重了。

### [](#Timer-存在的问题 "#Timer-存在的问题")Timer 存在的问题

Timer 的主要问题在于，如果 TimerTask 抛出未检查的异常，Timer 将会产生无法预料的行为。Timer 线程并不捕获异常，所以 TimerTask 抛出的未检查的异常会终止 timer 线程，这种情况下，Timer 也不会再恢复线程的执行了；它错误地认为整个 Timer 都被取消了。此时，已经被安排但尚未执行的 TimerTask 永远不会再执行了，新的任务也不能被调度了。

### [](#使用-ScheduledExecutorService "#使用-ScheduledExecutorService")使用 ScheduledExecutorService

ScheduledExecutorService 是 JDK 1.5 之后 concurrent 包下提供的 API。ScheduledExecutorService 妥善地处理了抛出异常的任务，所以说在 JDK1.5 或更高的 JDK 中，楼主不建议使用 Timer。关于 ScheduledExecutorService 楼主的另一篇文章也有提到，感兴趣的小伙伴请移步<a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2018%2Fcc2a%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/article/2018/cc2a/">Java 实现终止线程池中正在运行的定时任务</a>

## [](#产生的问题 "#产生的问题")产生的问题

上面说了一堆 Timer 与 ScheduledExecutorService 的区别，有点不着重点，现在重点来了，楼主凌晨的定时任务没有跑成功就是使用了 ScheduledExecutorService 而不是 Timer，当然倘若使用了 Timer 而导致的问题楼主也没必要说了。下面开始我们的找坑过程

### [](#查日志 "#查日志")查日志

通过 JDK 提供的 jstack 工具获取服务的 jstack 日志，如下所示：

                                                    

    2018-07-18 15:39:09
    Full thread dump Java HotSpot(TM) 64-Bit Server VM (24.79-b02 mixed mode):

    "Attach Listener" daemon prio=10 tid=0x00007f5bd0007800 nid=0x4e78 waiting on condition [0x0000000000000000]
       java.lang.Thread.State: RUNNABLE

    "DestroyJavaVM" prio=10 tid=0x00007f5bec008800 nid=0x1dd5 waiting on condition [0x0000000000000000]
       java.lang.Thread.State: RUNNABLE

    "Thread-4" prio=10 tid=0x00007f5bec4be000 nid=0x1df8 runnable [0x00007f5be88b2000]
       java.lang.Thread.State: RUNNABLE
        at java.net.PlainDatagramSocketImpl.receive0(Native Method)
        - locked <0x00000000e7e450b8> (a java.net.PlainDatagramSocketImpl)
        at java.net.AbstractPlainDatagramSocketImpl.receive(AbstractPlainDatagramSocketImpl.java:146)
        - locked <0x00000000e7e450b8> (a java.net.PlainDatagramSocketImpl)
        at java.net.DatagramSocket.receive(DatagramSocket.java:816)
        - locked <0x00000000e7e450e8> (a java.net.DatagramPacket)
        - locked <0x00000000e7e45110> (a java.net.DatagramSocket)
        at com.yg84.chelaile.middleware.common.remotedata.protocol.udp.UDPReceiver$1.run(UDPReceiver.java:55)
        at java.lang.Thread.run(Thread.java:745)

    "pool-5-thread-1" prio=10 tid=0x00007f5bec4ba800 nid=0x1df6 waiting on condition [0x00007f5be89b3000]
       java.lang.Thread.State: TIMED_WAITING (parking)
        at sun.misc.Unsafe.park(Native Method)
        - parking to wait for  <0x00000000e7f1e510> (a java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject)
        at java.util.concurrent.locks.LockSupport.parkNanos(LockSupport.java:226)
        at java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject.awaitNanos(AbstractQueuedSynchronizer.java:2082)
        at java.util.concurrent.ScheduledThreadPoolExecutor$DelayedWorkQueue.take(ScheduledThreadPoolExecutor.java:1090)
        at java.util.concurrent.ScheduledThreadPoolExecutor$DelayedWorkQueue.take(ScheduledThreadPoolExecutor.java:807)
        at java.util.concurrent.ThreadPoolExecutor.getTask(ThreadPoolExecutor.java:1068)
        at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1130)
        at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:615)
        at java.lang.Thread.run(Thread.java:745)

    "kafka-producer-network-thread | producer-1" daemon prio=10 tid=0x00007f5bec497000 nid=0x1df2 runnable [0x00007f5be8ffe000]
       java.lang.Thread.State: RUNNABLE
        at sun.nio.ch.EPollArrayWrapper.epollWait(Native Method)
        at sun.nio.ch.EPollArrayWrapper.poll(EPollArrayWrapper.java:269)
        at sun.nio.ch.EPollSelectorImpl.doSelect(EPollSelectorImpl.java:79)
        at sun.nio.ch.SelectorImpl.lockAndDoSelect(SelectorImpl.java:87)
        - locked <0x00000000e7e45778> (a sun.nio.ch.Util$2)
        - locked <0x00000000e7e45788> (a java.util.Collections$UnmodifiableSet)
        - locked <0x00000000e7e45730> (a sun.nio.ch.EPollSelectorImpl)
        at sun.nio.ch.SelectorImpl.select(SelectorImpl.java:98)
        at org.apache.kafka.common.network.Selector.select(Selector.java:454)
        at org.apache.kafka.common.network.Selector.poll(Selector.java:277)
        at org.apache.kafka.clients.NetworkClient.poll(NetworkClient.java:260)
        at org.apache.kafka.clients.producer.internals.Sender.run(Sender.java:229)
        at org.apache.kafka.clients.producer.internals.Sender.run(Sender.java:134)
        at java.lang.Thread.run(Thread.java:745)

    "AsyncLoggerConfig-1" daemon prio=10 tid=0x00007f5bec32a800 nid=0x1dee waiting on condition [0x00007f5bf04c2000]
       java.lang.Thread.State: WAITING (parking)
        at sun.misc.Unsafe.park(Native Method)
        - parking to wait for  <0x00000000e7638090> (a java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject)
        at java.util.concurrent.locks.LockSupport.park(LockSupport.java:186)
        at java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject.await(AbstractQueuedSynchronizer.java:2043)
        at com.lmax.disruptor.BlockingWaitStrategy.waitFor(BlockingWaitStrategy.java:45)
        at com.lmax.disruptor.ProcessingSequenceBarrier.waitFor(ProcessingSequenceBarrier.java:55)
        at com.lmax.disruptor.BatchEventProcessor.run(BatchEventProcessor.java:123)
        at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1145)
        at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:615)
        at java.lang.Thread.run(Thread.java:745)

    "Service Thread" daemon prio=10 tid=0x00007f5bec0b3800 nid=0x1ddc runnable [0x0000000000000000]
       java.lang.Thread.State: RUNNABLE

    "C2 CompilerThread1" daemon prio=10 tid=0x00007f5bec0b1000 nid=0x1ddb waiting on condition [0x0000000000000000]
       java.lang.Thread.State: RUNNABLE

    "C2 CompilerThread0" daemon prio=10 tid=0x00007f5bec0ae800 nid=0x1dda waiting on condition [0x0000000000000000]
       java.lang.Thread.State: RUNNABLE

    "Signal Dispatcher" daemon prio=10 tid=0x00007f5bec0ac800 nid=0x1dd9 runnable [0x0000000000000000]
       java.lang.Thread.State: RUNNABLE

    "Finalizer" daemon prio=10 tid=0x00007f5bec08c000 nid=0x1dd8 in Object.wait() [0x00007f5bf163a000]
       java.lang.Thread.State: WAITING (on object monitor)
        at java.lang.Object.wait(Native Method)
        - waiting on <0x00000000e74a07a0> (a java.lang.ref.ReferenceQueue$Lock)
        at java.lang.ref.ReferenceQueue.remove(ReferenceQueue.java:135)
        - locked <0x00000000e74a07a0> (a java.lang.ref.ReferenceQueue$Lock)
        at java.lang.ref.ReferenceQueue.remove(ReferenceQueue.java:151)
        at java.lang.ref.Finalizer$FinalizerThread.run(Finalizer.java:209)

    "Reference Handler" daemon prio=10 tid=0x00007f5bec08a000 nid=0x1dd7 in Object.wait() [0x00007f5bf173b000]
       java.lang.Thread.State: WAITING (on object monitor)
        at java.lang.Object.wait(Native Method)
        - waiting on <0x00000000e74a0848> (a java.lang.ref.Reference$Lock)
        at java.lang.Object.wait(Object.java:503)
        at java.lang.ref.Reference$ReferenceHandler.run(Reference.java:133)
        - locked <0x00000000e74a0848> (a java.lang.ref.Reference$Lock)

    "VM Thread" prio=10 tid=0x00007f5bec085800 nid=0x1dd6 runnable 

    "VM Periodic Task Thread" prio=10 tid=0x00007f5bec0b7000 nid=0x1ddd waiting on condition 

    JNI global references: 165

     

通过 jstack 日志并没有发现线程死锁，并且看到楼主开启的 ScheduledThreadPoolExecutor 也在正常运行，并没有发现问题。

                                                    
    "pool-5-thread-1" prio=10 tid=0x00007f5bec4ba800 nid=0x1df6 waiting on condition [0x00007f5be89b3000]
       java.lang.Thread.State: TIMED_WAITING (parking)
        at sun.misc.Unsafe.park(Native Method)
        - parking to wait for  <0x00000000e7f1e510> (a java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject)
        at java.util.concurrent.locks.LockSupport.parkNanos(LockSupport.java:226)
        at java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject.awaitNanos(AbstractQueuedSynchronizer.java:2082)
        at java.util.concurrent.ScheduledThreadPoolExecutor$DelayedWorkQueue.take(ScheduledThreadPoolExecutor.java:1090)
        at java.util.concurrent.ScheduledThreadPoolExecutor$DelayedWorkQueue.take(ScheduledThreadPoolExecutor.java:807)
        at java.util.concurrent.ThreadPoolExecutor.getTask(ThreadPoolExecutor.java:1068)
        at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1130)
        at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:615)
        at java.lang.Thread.run(Thread.java:745)

     

### [](#扒源码 "#扒源码")扒源码

因为出问题的是定时任务没有执行，所以楼主打算看一下 ScheduledExecutorService 中 scheduleAtFixedRate 的代码

                                                    

    /**
         * Creates and executes a periodic action that becomes enabled first
         * after the given initial delay, and subsequently with the given
         * period; that is executions will commence after
         * {@code initialDelay} then {@code initialDelay+period}, then
         * {@code initialDelay + 2 * period}, and so on.
         * If any execution of the task
         * encounters an exception, subsequent executions are suppressed.
         * Otherwise, the task will only terminate via cancellation or
         * termination of the executor.  If any execution of this task
         * takes longer than its period, then subsequent executions
         * may start late, but will not concurrently execute.
         *
         * @param command the task to execute
         * @param initialDelay the time to delay first execution
         * @param period the period between successive executions
         * @param unit the time unit of the initialDelay and period parameters
         * @return a ScheduledFuture representing pending completion of
         *         the task, and whose {@code get()} method will throw an
         *         exception upon cancellation
         * @throws RejectedExecutionException if the task cannot be
         *         scheduled for execution
         * @throws NullPointerException if command is null
         * @throws IllegalArgumentException if period less than or equal to zero
         */
        public ScheduledFuture<?> scheduleAtFixedRate(Runnable command,
                                                      long initialDelay,
                                                      long period,
                                                      TimeUnit unit);

     

果不其然，通过这个方法的 doc 中下面的这段话，大概可以知道任务遇到异常的时候，这个任务就不再执行。当然其他任务是不受影响的。

                                                    
    If any execution of the task encounters an exception, subsequent executions are suppressed. Otherwise, the task will only terminate via cancellation or termination of the executor.  If any execution of this task takes longer than its period, then subsequent executions may start late, but will not concurrently execute.

     

## [](#复盘 "#复盘")复盘

根据楼主上面的分析过程，可以知道出问题的原因就是代码中抛出了非受检异常，下面是楼主的测试代码，代码很简单，就是使用 ScheduledExecutorService 启动两个定时任务，其中一个抛出空指针异常，线程不捕获。

                                                    

    public class TestCase {

        public static void main (String[] args) {
            ScheduledExecutorService service = Executors
                    .newSingleThreadScheduledExecutor();
            service.scheduleAtFixedRate(new TestJob(), 0, 1000, TimeUnit.MILLISECONDS);
            service.scheduleAtFixedRate(new TestJob2(), 0, 1000, TimeUnit.MILLISECONDS);
        }

        static class TestJob implements Runnable {

            int count = 0;

            public TestJob() {

            }

            @Override
            public void run() {
    //          try {
                    count++;
                    System.out.println("TestJob count : " + count);
                    if (count == 5) {
                        throw new NullPointerException();
                    }
    //          } catch (Exception e) {
    //              e.printStackTrace();
    //          }
            }
        }

        static class TestJob2 implements Runnable {

            int count = 0;

            public TestJob2() {

            }

            @Override
            public void run() {
                count++;
                System.out.println("TestJob2 count : " + count);
            }
        }

    }

     

代码运行结果：在 TestJob 抛出异常后不再执行，TestJob2 不受影响可以继续执行。

<a href="https://link.juejin.cn?target=http%3A%2F%2Fimg.whforever.cn%2FscheduleAtFixedRate-result.png" target="_blank" data-ref="nofollow noopener noreferrer" title="http://img.whforever.cn/scheduleAtFixedRate-result.png"><img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/7/18/164ad17ae7e768ff~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.png" loading="lazy" alt="运行结果" /></a>运行结果

## [](#问题解决 "#问题解决")问题解决

问题产生的根源找到了，解决起来就比较简单了，具体代码如下所示

                                                    

    static class TestJob implements Runnable {

            int count = 0;

            public TestJob() {

            }

            @Override
            public void run() {
                try {
                    count++;
                    System.out.println("TestJob count : " + count);
                    if (count == 5) {
                        throw new NullPointerException();
                    }
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
        }

     

## [](#小结 "#小结")小结

总的来看这个问题也比较简单，相对来说比较隐蔽一些。当然，这跟自己平时的编码规范有很大关系。

作 者：haifeiWu\
原文链接：<a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2018%2Fb903%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/article/2018/b903/">www.hchstudio.cn/article/201…</a>\
版权声明：非特殊声明均为本站原创作品，转载时请注明作者和原文链接。
