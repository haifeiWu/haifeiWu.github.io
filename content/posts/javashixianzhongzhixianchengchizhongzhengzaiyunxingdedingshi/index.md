---
categories: ["后端"]
title: "Java实现终止线程池中正在运行的定时任务"
date: "2018-01-17T20:35:01+08:00"
tags: ["Java", "面试", "Netty"]
summary: "最近项目中遇到了一个新的需求，就是实现一个可以动态添加定时任务的功能。说到这里，有人可能会说简单啊，使用quartz就好了，简单粗暴。然而quartz框架太重了，小项目根本不好操作啊。当然，也有人会说，jdk提供了timer的接口啊，完全够用啊。但是我们项目的需求完全是多线程的…"
translationKey: "javashixianzhongzhixianchengchizhongzhengzaiyunxingdedingshi"
---

> 📌 本文原发布于掘金社区：[Java实现终止线程池中正在运行的定时任务](https://juejin.cn/post/6844903551890620424)

## 源于开发

最近项目中遇到了一个新的需求，就是实现一个可以动态添加定时任务的功能。说到这里，有人可能会说简单啊，使用quartz就好了，简单粗暴。然而quartz框架太重了，小项目根本不好操作啊。当然，也有人会说，jdk提供了timer的接口啊，完全够用啊。但是我们项目的需求完全是多线程的模型啊，而timer是单线程的，so，楼主最后还是选择了jdk的线程池。

## 线程池是什么

Java通过Executors提供四种线程池，分别为： \*\*newCachedThreadPool ：\*\*创建一个可缓存线程池，如果线程池长度超过处理需要，可灵活回收空闲线程，若无可回收，则新建线程。 **newFixedThreadPool :** 创建一个定长线程池，可控制线程最大并发数，超出的线程会在队列中等待。 **newScheduledThreadPool :** 创建一个定长线程池，支持定时及周期性任务执行。 **newSingleThreadExecutor :** 创建一个单线程化的线程池，它只会用唯一的工作线程来执行任务，保证所有任务按照指定顺序(FIFO, LIFO, 优先级)执行。

楼主项目中用到的是newScheduledThreadPool， 就这些吧，再多的楼主就班门弄斧了，Google一下，一大堆。

## 线程池service的获取

楼主通过单例模式来获取线程池的service，代码如下：

``` bash
/**
 * 线程池创建.
 * @author wuhf
 * @date 2018/01/16
 */
public class ThreadPoolUtils {

    private static ScheduledExecutorService executorService;

    private ThreadPoolUtils() {
        //手动创建线程池.
        executorService = new ScheduledThreadPoolExecutor(10,
                new BasicThreadFactory.Builder().namingPattern("syncdata-schedule-pool-%d").daemon(true).build());
    }

    private static class PluginConfigHolder {
        private final static ThreadPoolUtils INSTANCE = new ThreadPoolUtils();
    }

    public static ThreadPoolUtils getInstance() {
        return PluginConfigHolder.INSTANCE;
    }

    public ScheduledExecutorService getThreadPool(){
        return executorService;
    }

}
```

## 中断某一个正在运行的线程代码实现

废话就不多说了，代码如下：

``` bash
/**
 * 中断线程池的某个任务.
 */
public class InterruptThread implements Runnable {

    private int num;

    public InterruptThread (int num){
        this.num = num;
    }

    public static void main(String[] args) throws InterruptedException {

        Thread interruptThread = new Thread(new InterruptThread(1));
        ScheduledFuture<?> t = ThreadPoolUtils.getInstance().getThreadPool().scheduleAtFixedRate(interruptThread,0,2,
                TimeUnit.SECONDS);

        InterruptThread interruptThread1 = new InterruptThread(2);
        ThreadPoolUtils.getInstance().getThreadPool().scheduleAtFixedRate(interruptThread1,0,2,
                TimeUnit.SECONDS);

        InterruptThread interruptThread2 = new InterruptThread(3);
        ThreadPoolUtils.getInstance().getThreadPool().scheduleAtFixedRate(interruptThread2,0,2,
                TimeUnit.SECONDS);
        Thread.sleep(5000);

        //终止正在运行的线程interruptThread
        t.cancel(true);
        while (true){

        }
    }

    @Override
    public void run() {
        System.out.println("this is a thread" + num);
    }
}
```

## 踩坑记录

楼主在使用如下代码时，突然想到当这个定时任务需要被停止时该如何停止线程运行

``` bash
ThreadPoolUtils.getInstance().getThreadPool().scheduleAtFixedRate(interruptThread,0,2,
                TimeUnit.SECONDS);
```

既然我有这样的需求，那就Google一下吧，找了大半圈，愣是没找到相关资料，都是一些关于Java线程池的深入分析。或者是全局变量啥的，并没有找到令楼主满意的解决方案。

既然没有线程的那就扒一下scheduleAtFixedRate的底层源码看看是什么东西吧，果不其然我在源码中看到了scheduleAtFixedRate方法的具体实现，发现他的返回值是ScheduledFuture。

``` bash
 public ScheduledFuture<?> scheduleAtFixedRate(Runnable command,
                                                  long initialDelay,
                                                  long period,
                                                  TimeUnit unit) {
        if (command == null || unit == null)
            throw new NullPointerException();
        if (period <= 0)
            throw new IllegalArgumentException();
        ScheduledFutureTask<Void> sft =
            new ScheduledFutureTask<Void>(command,
                                          null,
                                          triggerTime(initialDelay, unit),
                                          unit.toNanos(period));
        RunnableScheduledFuture<Void> t = decorateTask(command, sft);
        sft.outerTask = t;
        delayedExecute(t);
        return t;
    }
```

接着往下我们再看看ScheduledFuture里面有什么东西吧，没有让楼主失望，看到了这个

``` bash
public boolean cancel(boolean mayInterruptIfRunning) {
            boolean cancelled = super.cancel(mayInterruptIfRunning);
            if (cancelled && removeOnCancel && heapIndex >= 0)
                remove(this);
            return cancelled;
}
            
//从线程的运行队列中移除当前线程
public boolean remove(Runnable task) {
        boolean removed = workQueue.remove(task);
        tryTerminate(); // In case SHUTDOWN and now empty
        return removed;
}
```

再往上查super.cancel(mayInterruptIfRunning)是什么东西，我们看到了这个，

``` bash
//通过调用线程的interrupt方法终止线程运行
public boolean cancel(boolean mayInterruptIfRunning) {
        if (!(state == NEW &&
              UNSAFE.compareAndSwapInt(this, stateOffset, NEW,
                  mayInterruptIfRunning ? INTERRUPTING : CANCELLED)))
            return false;
        try {    // in case call to interrupt throws exception
            if (mayInterruptIfRunning) {
                try {
                    Thread t = runner;
                    if (t != null)
                        t.interrupt();
                } finally { // final state
                    UNSAFE.putOrderedInt(this, stateOffset, INTERRUPTED);
                }
            }
        } finally {
            finishCompletion();
        }
        return true;
    }
```

到这里所有的问题都迎刃而解。

## 总结一下吧

项目中总是会遇到比较难搞的解决方案，当Google不太好找时，翻一下jdk的源码或许也是一个不错的方法。最后宣传一下楼主的博客，博客已经迁移到腾讯云上，跟几个大学的小伙伴一起经营，内容涵盖java，Android等，感兴趣的小伙伴请移步<a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/">楼主跟他的小伙伴们的博客</a>
