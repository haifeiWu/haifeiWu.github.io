---
categories: ["后端"]
title: "聊聊 HashSet 源码"
date: "2018-05-29T23:18:49+08:00"
tags: ["Java", "源码", "面试", "后端", "服务器"]
summary: "今天聊一下 HashSet 源码，HashSet 内部基本使用 HashMap 来实现，本博客将通过一下几个方向讲解。"
---

> 📌 本文原发布于掘金社区：[聊聊 HashSet 源码](https://juejin.cn/post/6844903614285086727)

今天聊一下 HashSet 源码，HashSet 内部基本使用 HashMap 来实现，本博客将通过以下几个方向讲解。

<span id="user-content-more"></span>

## [](#HashSet的UML图 "#HashSet的UML图")HashSet 的 UML 图

<a href="https://link.juejin.cn?target=http%3A%2F%2Fimg.hchstudio.cn%2FHashSet.png" target="_blank" data-ref="nofollow noopener noreferrer" title="http://img.hchstudio.cn/HashSet.png"><img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/5/29/163ac7b1dd17ad53~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.png" title="UML图" loading="lazy" alt="HashMap的UML图" /></a>HashMap 的 UML 图

## [](#HashSet简介 "#HashSet简介")HashSet 简介

### [](#HashSet数据结构 "#HashSet数据结构")HashSet 数据结构

HashSet 内部使用 HashMap 来实现，HashMap 的 key 为要存储的元素，value 为一个 Object，大致数据结构如下：\

    public class HashSet<E> extends AbstractSet<E> implements Set<E>, Cloneable, java.io.Serializable {
        static final long serialVersionUID = -5024744406713321676L;
        private transient HashMap<E,Object> map;  
        private static final Object PRESENT = new Object();  
    }

- serialVersionUID：常量，序列化所用的 ID
- map：使用 HashMap 来保存 HashSet 中所有元素，并使用 transient 关键字修饰，防止被序列化，具体序列化过程，后面会有说到
- PRESENT：常量，默认为 map 的 value 值

### [](#HashSet构造函数 "#HashSet构造函数")HashSet 构造函数

    public HashSet(Collection<? extends E> c) {  
        map = new HashMap<E,Object>(Math.max((int) (c.size()/.75f) + 1, 16));  
        addAll(c);  
    }  

    public HashSet(int initialCapacity, float loadFactor) {  
        map = new HashMap<E,Object>(initialCapacity, loadFactor);  
    }  

    HashSet(int initialCapacity, float loadFactor, boolean dummy) {  
        map = new LinkedHashMap<E,Object>(initialCapacity, loadFactor);  
    }

这里列举了三种构造函数

1.  第一种构造一个包含指定 collection 中的元素的新 set，容器大小为 collection 大小的 4/3 倍与 16 中的最大值
2.  第二种传入初始容量和加载因子，构造一个空的 HashMap，
3.  第三种传入初始容量、加载因子和标记，构造一个空的 LinkedHashMap，此构造函数为包访问权限，不对外公开，实际只是对 LinkedHashSet 的支持。

## [](#聊聊HashSet的主要方法实现 "#聊聊HashSet的主要方法实现")聊聊 HashSet 的主要方法实现

### [](#迭代器 "#迭代器")迭代器

    public Iterator<E> iterator() {  
        return map.keySet().iterator();  
    }

返回对此 set 中元素进行迭代的迭代器。返回元素的顺序并不是特定的。底层实际调用 HashMap 的 keySet 来返回所有的 key，可见 HashSet 中的元素，只是存放在了底层 HashMap 的 key 上。

### [](#增加元素 "#增加元素")增加元素

    public boolean add(E e) {  
        return map.put(e, PRESENT)==null;  
    }

底层实际将该元素作为 key 放入 HashMap。由于 HashMap 的 put()方法在添加 key-value 对时，如果新放入的 Entry 的 key 与集合中原有 Entry 的 key 相同（hashCode()返回值相等，通过 equals 比较也返回 true）,新添加的 Entry 的 value 会覆盖原来 Entry 的 value，但 key 不会有任何改变，因此如果向 HashSet 中添加一个已经存在的元素时，新添加的集合元素将不会被放入 HashMap 中，原来的元素也不会有任何改变，这也就满足了 Set 中元素不重复的特性。

### [](#删除元素 "#删除元素")删除元素

    public boolean remove(Object o) {  
        return map.remove(o)==PRESENT;  
    }

如果指定元素存在于此 set 中，则将其移除。更确切地讲，如果此 set 包含一个满足(o==null ? e==null : o.equals(e))的元素 e，则将其移除。如果此 set 已包含该元素，则返回 true。底层实际调用 HashMap 的 remove 方法删除指定 Entry。

### [](#对象拷贝 "#对象拷贝")对象拷贝

    public Object clone() {  
        try {  
            HashSet<E> newSet = (HashSet<E>) super.clone();  
            newSet.map = (HashMap<E, Object>) map.clone();  
            return newSet;  
        } catch (CloneNotSupportedException e) {  
            throw new InternalError();  
        }  
    }

返回此 HashSet 实例的浅表副本：并没有复制这些元素本身。底层实际调用 HashMap 的 clone()方法，HashMap 的 clone()为浅拷贝，故 HashSet 的 clone 也是浅拷贝。

## [](#聊聊HashSet与HashMap的关系 "#聊聊HashSet与HashMap的关系")聊聊 HashSet 与 HashMap 的关系

从上面的源码可以看出来，HashSet 与 HashMap 的关系不可谓不密切，以至于不敢相信上面的 UML 是对的。因此，对于 HashSet 而言，它是基于 HashMap 实现的，HashSet 底层使用 HashMap 来保存所有元素，因此 HashSet 源码的实现比较简单，HashSet 的相关操作，都是直接调用底层 HashMap 的相关方法完成的。

## [](#特性小结 "#特性小结")特性小结

1.  从源码来看，HashSet 无非是一个阉割版的 HashMap，所以要想明白 HashSet 的实现原理，HashMap 源码坑还是要跳的。

2.  对于 HashSet 中保存的对象，请注意正确重写其 equals 和 hashCode 方法，以保证放入的对象的唯一性。

3.  Set 是利用底层 Map 不放入重复 key 的特性来保证元素不重复的。

4.  HashSet 没有提供 get()方法，原因是同 HashMap 一样，Set 内部是无序的，只能通过迭代的方式获得。

    ## [](#参考文章 "#参考文章")参考文章

- <a href="https://link.juejin.cn?target=https%3A%2F%2Fblog.csdn.net%2Ffighterandknight%2Farticle%2Fdetails%2F66585997" target="_blank" data-ref="nofollow noopener noreferrer" title="https://blog.csdn.net/fighterandknight/article/details/66585997">HashSet 源码分析（基于 JDK8）</a>
- <a href="https://link.juejin.cn?target=http%3A%2F%2Fzhangshixi.iteye.com%2Fblog%2F673143" target="_blank" data-ref="nofollow noopener noreferrer" title="http://zhangshixi.iteye.com/blog/673143">深入 Java 集合学习系列：HashSet 的实现原理</a>
