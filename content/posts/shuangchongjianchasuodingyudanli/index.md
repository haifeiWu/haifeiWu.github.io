---
categories: ["后端"]
title: "双重检查锁定与单例"
date: "2019-11-13T14:47:53+08:00"
tags: ["Java", "设计模式"]
summary: "对于单例模式，相信大多数人都可以写出好几种实现方法，懒汉，饿汉等等，然而小小单例真要写好，写的完全正确也并非易事。 下面是我们经常使用的一种单例的实现，也就是双重检查所的实现方案。 让我们来看一下这个代码是如何工作的：首先当一个线程发出请求后，会先检查instance是否为nu…"
---

> 📌 本文原发布于掘金社区：[双重检查锁定与单例](https://juejin.cn/post/6844903993542443022)

<a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2019%2F2b9%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/article/2019/2b9/">双重检查锁定与单例-原文链接</a>\
<a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2019%2F2b9%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/article/2019/2b9/">双重检查锁定与单例-原文链接</a>\
<a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2019%2F2b9%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/article/2019/2b9/">双重检查锁定与单例-原文链接</a>\

对于单例模式，相信大多数人都可以写出好几种实现方法，懒汉，饿汉等等，然而小小单例真要写好，写的完全正确也并非易事。

## 双重检查锁的单例

下面是我们经常使用的一种单例的实现，也就是双重检查所的实现方案。

``` java
public class Singleton {
    private static Singleton instance;

    private Singleton() {
        
    }

    public Singleton getInstance() {
        if (null == instance) {
            synchronized (Singleton.class) {
                if (null == instance) {
                    instance = new Singleton();   // error
                }
            }
        }
        return uniqueSingleton;
    }
}  
```

让我们来看一下这个代码是如何工作的：首先当一个线程发出请求后，会先检查instance是否为null，如果不是则直接返回其内容，这样避免了进入synchronized块所需要花费的资源。其次，如果两个线程同时进入了第一个if判断，那么他们也必须按照顺序执行 synchronized 块中的代码，第一个进入代码块的线程会创建一个新的 Singleton 实例，而后续的线程则因为无法通过if判断，而不会创建多余的实例。

但还有一个问题，在有些情况下，通过这种方式拿到的Singleton对象，可能是错误的 。

回顾我们new对象的3个步骤

- 1，分配内存空间

- 2，初始化对象

- 3，将对象指向刚分配的内存空间

但jvm在指令优化时，会出现步骤2和3对调的情况，比如线程1在经过俩层为 null 判断后，进入 new 的动作，在还没有初始化对象时，就返加了地址值，线程2在第一个为 null 判断时，因为对象已经不为空，那么就直接返回了对象。然而当线程2打算使用Singleton实例，却发现它没有被初始化，于是错误发生了。

## 解决方案

对于上面的问题，有两种解决方案

**1，使用 volatile 关键词主要可以保证代码的执行顺序不受 jvm 重排序影响。**

``` java
public class Singleton {
    private volatile static Singleton instance;

    private Singleton() {
    }

    public Singleton getInstance() {
        if (null == instance) {
            synchronized (Singleton.class) {
                if (null == instance) {
                    instance = new Singleton();   // error
                }
            }
        }
        return instance;
    }
}
```

**2，通过内部类实现多线程环境中的单例模式。**

``` java
public class Singleton {        
    
    private Singleton() {       
    }        
    
    private static class SingletonContainer {        
        private static Singleton instance = new Singleton();        
    }        
    
    public static Singleton getInstance() {        
        return SingletonContainer.instance;        
    }        
} 
```

## 关注我们

<figure>
<img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2019/11/8/16e498848fb64e35~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.png" loading="lazy" alt="关注我们" />
</figure>
