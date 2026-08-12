---
categories: ["后端"]
title: "聊聊 volatile 关键字"
date: "2018-10-22T10:07:21+08:00"
tags: ["后端", "安全", "Java", "算法"]
summary: "我们知道 volatile 关键字的作用是保证变量在多线程之间的可见性，它是 java.util.concurrent 包的核心，没有 volatile 就没有这么多的并发类给我们使用。本文将简单介绍一下 volatile 这个东东。 CAS(compare-and-swap)…"
---

> 📌 本文原发布于掘金社区：[聊聊 volatile 关键字](https://juejin.cn/post/6844903696468279303)

> 原文地址： <a href="https://link.juejin.cn?target=https%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2018%2F3da%2F%3F_ref%3Djuejin" target="_blank" data-ref="nofollow noopener noreferrer" title="https://www.hchstudio.cn/article/2018/3da/?_ref=juejin">haifeiWu和他朋友们的博客</a>\
> 博客地址：<a href="https://link.juejin.cn?target=https%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2018%2F3da%2F%3F_ref%3Djuejin" target="_blank" data-ref="nofollow noopener noreferrer" title="https://www.hchstudio.cn/article/2018/3da/?_ref=juejin">www.hchstudio.cn</a>\
> 欢迎转载，转载请注明作者及出处，谢谢！

我们知道 volatile 关键字的作用是保证变量在多线程之间的可见性，它是 java.util.concurrent 包的核心，没有 volatile 就没有这么多的并发类给我们使用。本文将简单介绍一下 volatile 这个东东。

## 算法概念及其执行流程

- CAS(compare-and-swap) 是一种硬件对并发的支持，针对多处理器操作而设计的处理器中的一种特殊指令，用于管理对共享数据的并发访问。

- CAS 是一种无锁非阻塞算法的实现。

- CAS 包含了 3 个操作数：\
  需要读写的内存值 V 进行比较的值 A\
  拟写入的新值 B

- 当且仅当 V 的值等于 A 时，CAS 通过原子方式用新值更新 V 的值，否则不会执行任何操作。

## CAS 操作过程如下所示

<figure>
<img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/10/22/166997da67baa664~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.png" loading="lazy" alt="CAS操作过程" />
</figure>

## CAS 算法模拟

``` java
/**
 * 模拟 CAS 算法
 *
 * Created by wuhf on 2017-1-22.
 */
public class TestCompareAndSwap {
    public static void main(String[] args){
        final CompareAndSwap cas = new CompareAndSwap();

        for (int i = 0; i < 10; i++ ){
            new Thread(new Runnable() {
                        @Override
                        public void run() {
                            int expectValue = cas.getValue();
                            boolean b = cas.compareAndSet(expectValue, (int)(Math.random() * 101));
                            System.out.println(b);
                        }
                    }
            ).start();
        }
    }
}

class CompareAndSwap{
    private int value;

    // 获取内存值
    public synchronized int getValue(){
        return this.value;
    }
    // 比较
    public synchronized int compareAndSwap(int expectValue,int newValue){
        int oldValue = this.value;
        if(oldValue == expectValue){//如果期望值等于旧值
            this.value = newValue;
        }
        return oldValue;
    }

    public synchronized boolean compareAndSet(int expectValue,int newValue){
        return expectValue == compareAndSwap(expectValue, newValue);
    }

}
```

## 原子变量

- 类的小工具包，支持在单个变量上解除锁的线程安全编程。事实上，此包中的类可将 volatile 值、字段和数组元素的概念扩展到那些也提供原子条件更新操作的类。

- 类 AtomicBoolean、 AtomicInteger、 AtomicLong 和 AtomicReference 的实例各自提供对相应类型单个变量的访问和更新。每个类也为该类型提供适当的实用工具方法。

- AtomicIntegerArray、 AtomicLongArray 和 AtomicReferenceArray 类进一步扩展了原子操作，对这些类型的数组提供了支持。这些类在为其数组元素提供 volatile 访问语义方面也引人注目，这对于普通数组来说是不受支持的。

- 核心方法： boolean compareAndSet(expectedValue, updateValue)

- java.util.concurrent.atomic 包下提供了一些原子操作的常用类:

1.  AtomicBoolean 、 AtomicInteger 、 AtomicLong 、AtomicReference
2.  AtomicIntegerArray 、 AtomicLongArray
3.  AtomicMarkableReference
4.  AtomicReferenceArray
5.  AtomicStampedReference

## 原子变量简单 Demo

``` java
/**
 * 一、i++ 的原子性问题：i++ 的操作实际上分为三个步骤“读-改-写”
 *        int i = 10;
 *        i = i++; //10
 *
 *        int temp = i;
 *        i = i + 1;
 *        i = temp;
 * 二、原子变量：在 java.util.concurrent.atomic 包下提供了一些原子变量。
 *      1. volatile 保证内存可见性
 *      2. CAS（Compare-And-Swap） 算法保证数据变量的原子性
 *          CAS 算法是硬件对于并发操作的支持
 *          CAS 包含了三个操作数：
 *          1,内存值  V
 *          2,预估值  A
 *          3,更新值  B
 *          当且仅当 V == A 时， V = B; 否则，不会执行任何操作。
 */
public class AtomicDemo {
    public static void main(String[] args) {
        AtomicData ad = new AtomicData();
        for (int i = 0; i < 10; i++) {
            new Thread(ad).start();
        }
    }
}

class AtomicData implements Runnable{
    // 初始化原子变量
    private AtomicInteger atomicData = new AtomicInteger(0);
    
    @Override
    public void run() {
        try {
            Thread.sleep(200);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        
        System.out.println(getAtomicData());
    }
    
    // 相当于atomicData++
    public int getAtomicData(){
        return atomicData.getAndIncrement();
    }
    
}
```

## 小结

在我们的实现可能会被并发操作的共享资源时，加锁可能会是最简单粗暴的方法，但是使用不慎必然会产生死锁等问题，而造成线程假死，产生重大线上问题。因此 volatile 不失为不错的选择。

<figure>
<img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/10/25/166a8fd5986ff3a7~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.png" loading="lazy" alt="关注我们" />
</figure>
