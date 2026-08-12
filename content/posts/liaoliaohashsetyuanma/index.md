---
categories: ["后端"]
title: "聊聊HashSet源码"
date: "2018-05-29T23:18:49+08:00"
tags: ["Java", "源码", "面试", "后端", "服务器"]
summary: "今天聊一下HashSet源码，HashSet内部基本使用HashMap来实现，本博客将通过一下几个方向讲解。"
translationKey: "liaoliaohashsetyuanma"
---

> 📌 本文原发布于掘金社区：[聊聊HashSet源码](https://juejin.cn/post/6844903614285086727)

今天聊一下HashSet源码，HashSet内部基本使用HashMap来实现，本博客将通过一下几个方向讲解。

<span id="user-content-more"></span>

## [](#HashSet的UML图 "#HashSet的UML图")HashSet的UML图

<a href="https://link.juejin.cn?target=http%3A%2F%2Fimg.hchstudio.cn%2FHashSet.png" target="_blank" data-ref="nofollow noopener noreferrer" title="http://img.hchstudio.cn/HashSet.png"><img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/5/29/163ac7b1dd17ad53~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.png" title="UML图" loading="lazy" alt="HashMap的UML图" /></a>HashMap的UML图

## [](#HashSet简介 "#HashSet简介")HashSet简介

### [](#HashSet数据结构 "#HashSet数据结构")HashSet数据结构

HashSet内部使用HashMap来实现，HashMap的key为要存储的元素，value为一个Object，大致数据结构如下：\

    public class HashSet<E> extends AbstractSet<E> implements Set<E>, Cloneable, java.io.Serializable {
        static final long serialVersionUID = -5024744406713321676L;
        private transient HashMap<E,Object> map;  
        private static final Object PRESENT = new Object();  
    }

- serialVersionUID：常量，序列化所用的ID
- map：使用HashMap来保存HashSet中所有元素，并使用transient关键字修饰，防止被序列化，具体序列化过程，后面会有说到
- PRESENT：常量，默认为map的value值

### [](#HashSet构造函数 "#HashSet构造函数")HashSet构造函数

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

这里举例列举了三种构造函数

1.  第一种构造一个包含指定collection中的元素的新set，容器大小为collection大小的4/3倍，和16的最大值
2.  第二种传入初始容量和加载因子，构造一个空的HashSetLinkedHashMap，
3.  第三种传入初始容量、加载因子和标记，构造一个空的LinkedHashMap，此构造函数为包访问权限，不对外公开，实际只是是对LinkedHashSet的支持。

## [](#聊聊HashSet的主要方法实现 "#聊聊HashSet的主要方法实现")聊聊HashSet的主要方法实现

### [](#迭代器 "#迭代器")迭代器

    public Iterator<E> iterator() {  
        return map.keySet().iterator();  
    }

返回对此set中元素进行迭代的迭代器。返回元素的顺序并不是特定的。底层实际调用底层HashMap的keySet来返回所有的key，可见HashSet中的元素，只是存放在了底层HashMap的key上。

### [](#增加元素 "#增加元素")增加元素

    public boolean add(E e) {  
        return map.put(e, PRESENT)==null;  
    }

底层实际将将该元素作为key放入HashMap。由于HashMap的put()方法添加key-value对时，当新放入HashMap的Entry中key，与集合中原有Entry的key相同（hashCode()返回值相等，通过equals比较也返回true）,新添加的Entry的value会将覆盖原来Entry的value，但key不会有任何改变，因此如果向HashSet中添加一个已经存在的元素时，新添加的集合元素将不会被放入HashMap中， 原来的元素也不会有任何改变，这也就满足了Set中元素不重复的特性。

### [](#删除元素 "#删除元素")删除元素

    public boolean remove(Object o) {  
        return map.remove(o)==PRESENT;  
    }

如果指定元素存在于此set中，则将其移除。更确切地讲，如果此set包含一个满足(o==null ? e==null : o.equals(e))的元素e，则将其移除。如果此set已包含该元素，则返回true。底层实际调用HashMap的remove方法删除指定Entry。

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

返回此HashSet实例的浅表副本：并没有复制这些元素本身。底层实际调用HashMap的clone()方法，HashMap的clone()为浅拷贝，故HashSet的clone也是浅拷贝。

## [](#聊聊HashSet与HashMap的关系 "#聊聊HashSet与HashMap的关系")聊聊HashSet与HashMap的关系

从上面的源码可以看出来，HashSet与HashMap的关系不可谓不密切，以至于不敢相信上面的UML是对的。因此，对于HashSet而言，它是基于HashMap实现的，HashSet底层使用HashMap来保存所有元素，因此HashSet源码的实现比较简单，相关HashSet的操作，都是直接调用底层HashMap的相关方法来完成。

## [](#特性小结 "#特性小结")特性小结

1.  从源码来看，HashSet无非是一个阉割版的HashMap，所以要想明白HashSet的实现原理，HashMap源码坑还是要跳的。

2.  对于HashSet中保存的对象，请注意正确重写其equals和hashCode方法，以保证放入的对象的唯一性。

3.  Set是利用底层的Map对于重复的key不放入的特性来保证元素的不重复的。

4.  HashSet没有提供get()方法，原因是同HashMap一样，Set内部是无序的，只能通过迭代的方式获得。

    ## [](#参考文章 "#参考文章")参考文章

- <a href="https://link.juejin.cn?target=https%3A%2F%2Fblog.csdn.net%2Ffighterandknight%2Farticle%2Fdetails%2F66585997" target="_blank" data-ref="nofollow noopener noreferrer" title="https://blog.csdn.net/fighterandknight/article/details/66585997">HashSet源码分析（基于JDK8）</a>
- <a href="https://link.juejin.cn?target=http%3A%2F%2Fzhangshixi.iteye.com%2Fblog%2F673143" target="_blank" data-ref="nofollow noopener noreferrer" title="http://zhangshixi.iteye.com/blog/673143">深入Java集合学习系列：HashSet的实现原理</a>
