---
categories: ["后端"]
title: "死磕 Java 之聊聊 HashMap 源码(基于 JDK1.8)"
date: "2018-06-04T23:07:24+08:00"
tags: ["Java", "源码", "面试", "服务器", "Linux"]
summary: "HashMap 是 Java 程序员使用频率最高的数据结构之一。另外，JDK1.8 对 HashMap 底层的实现进行了优化，如引入红黑树的数据结构以及扩容的优化等等来提高性能。本文结合 JDK1.8 的源码，探讨 HashMap 的结构实现和功能原理。"
translationKey: "sikejavazhiliaoliaohashmapyuanma-jiyujdk1-8"
---

> 📌 本文原发布于掘金社区：[死磕 Java 之聊聊 HashMap 源码(基于 JDK1.8)](https://juejin.cn/post/6844903616503873550)

HashMap 是 Java 程序员使用频率最高的数据结构之一。另外，JDK1.8 对 HashMap 底层的实现进行了优化，如引入红黑树的数据结构以及扩容的优化等等来提高性能。本文结合 JDK1.8 的源码，探讨 HashMap 的结构实现和功能原理。\
<span id="user-content-more"></span>

## [](#HashMap的UML图 "#HashMap的UML图")HashMap 的 UML 图

<a href="https://link.juejin.cn?target=http%3A%2F%2Fimg.hchstudio.cn%2FHashMap.png" target="_blank" data-ref="nofollow noopener noreferrer" title="http://img.hchstudio.cn/HashMap.png"><img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/6/4/163cb56c386a0d81~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.png" title="UML图" loading="lazy" alt="HashMap的UML图" /></a>HashMap 的 UML 图

## [](#HashMap的成员变量及其含义 "#HashMap的成员变量及其含义")HashMap 的成员变量及其含义

                                                    
    public class HashMap<K,V> extends AbstractMap<K,V>
        implements Map<K,V>, Cloneable, Serializable {

        private static final long serialVersionUID = 362498820763181265L;

        /**
         * HashMap的默认初始化大小为16
         */
        static final int DEFAULT_INITIAL_CAPACITY = 1 << 4; // aka 16

        /**
         * HashMap的最大容量。
         */
        static final int MAXIMUM_CAPACITY = 1 << 30;

        /**
         * 负载因子的大小，一般HashMap的扩容的临界点是当前HashMap的大小 > DEFAULT_LOAD_FACTOR * DEFAULT_INITIAL_CAPACITY 
         */
        static final float DEFAULT_LOAD_FACTOR = 0.75f;

        /**
         * 这是JDK1.8在底层做的一个优化，当一个Entry挂载的节点超过8个，就会将当前Entry的链表结构转化为红黑树的数据结构
         */
        static final int TREEIFY_THRESHOLD = 8;

        /**
         * 
         */
        static final int UNTREEIFY_THRESHOLD = 6;

        /**
         * 红黑树的最大节点数
         */
        static final int MIN_TREEIFY_CAPACITY = 64;

        /**
         * 是hash表中，Entry的节点.
         */
        static class Node<K,V> implements Map.Entry<K,V> {
            final int hash;
            final K key;
            V value;
            Node<K,V> next;

            Node(int hash, K key, V value, Node<K,V> next) {
                this.hash = hash;
                this.key = key;
                this.value = value;
                this.next = next;
            }

            public final K getKey()        { return key; }
            public final V getValue()      { return value; }
            public final String toString() { return key + "=" + value; }

            public final int hashCode() {
                return Objects.hashCode(key) ^ Objects.hashCode(value);
            }

            public final V setValue(V newValue) {
                V oldValue = value;
                value = newValue;
                return oldValue;
            }

            public final boolean equals(Object o) {
                if (o == this)
                    return true;
                if (o instanceof Map.Entry) {
                    Map.Entry<?,?> e = (Map.Entry<?,?>)o;
                    if (Objects.equals(key, e.getKey()) &&
                        Objects.equals(value, e.getValue()))
                        return true;
                }
                return false;
            }
        }
        
         /* ---------------- Static utilities -------------- */
        
            /**
             * 计算key的hash值。
             */
            static final int hash(Object key) {
                int h;
                return (key == null) ? 0 : (h = key.hashCode()) ^ (h >>> 16);
            }
            
            /**
             * 这个方法时HashMap中比较实用的方法，用于计算传入值的2倍，也算是JDK源码部分的最佳实践。
             */
            static final int tableSizeFor(int cap) {
                int n = cap - 1;
                n |= n >>> 1;
                n |= n >>> 2;
                n |= n >>> 4;
                n |= n >>> 8;
                n |= n >>> 16;
                return (n < 0) ? 1 : (n >= MAXIMUM_CAPACITY) ? MAXIMUM_CAPACITY : n + 1;
            }
        
            /* ---------------- Fields -------------- */
        
            /**
             * hash表
             */
            transient Node<K,V>[] table;
        
            /**
             * 保存缓存的entrySet。
             */
            transient Set<Map.Entry<K,V>> entrySet;
        
            /**
             * map中键值对的数量。
             */
            transient int size;
        
            /**
             * 
             * 这个HashMap被结构修改的次数结构修改是那些改变HashMap中的映射数量或者修改其内部结构（例如，重新散列）的修改。 该字段用于在HashMap失败快速的Collection-views上创建迭代器。
             */
            transient int modCount;
        
            /**
             * The next size value at which to resize (capacity * load factor).
             *
             * @serial
             */
            int threshold;
        
            /**
             * The load factor for the hash table.
             *
             * @serial
             */
            final float loadFactor;
    }


                                                

## [](#聊聊HashMap的主要方法实现 "#聊聊HashMap的主要方法实现")聊聊 HashMap 的主要方法实现

### [](#内部实现 "#内部实现")内部实现

搞清楚 HashMap，首先需要知道 HashMap 是什么，即它的存储结构-字段；其次弄明白它能干什么，即它的功能实现-方法。下面我们针对这两个方面详细展开讲解。

### [](#存储结构-字段 "#存储结构-字段")存储结构-字段

从结构实现来讲，HashMap 是数组+链表+红黑树（JDK1.8 增加了红黑树部分）实现的，如下图所示。

<a href="https://link.juejin.cn?target=http%3A%2F%2Fimg.hchstudio.cn%2FhashMap%25E5%2586%2585%25E5%25AD%2598%25E7%25BB%2593%25E6%259E%2584%25E5%259B%25BE.png" target="_blank" data-ref="nofollow noopener noreferrer" title="http://img.hchstudio.cn/hashMap%E5%86%85%E5%AD%98%E7%BB%93%E6%9E%84%E5%9B%BE.png"><img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/6/4/163cb56c385ea680~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.png" title="HashMap的内存结构图" loading="lazy" alt="HashMap的内存结构图" /></a> HashMap 的内存结构图

这里需要讲明白两个问题：数据底层具体存储的是什么？这样的存储方式有什么优点呢？

\(1\) 从源码可知，HashMap 类中有一个非常重要的字段，就是 Node\[\] table，即哈希桶数组，明显它是一个 Node 的数组。我们来看 Node\[JDK1.8\]是何物。

                                                    
    static class Node<K,V> implements Map.Entry<K,V> {
            final int hash;    //用来定位数组索引位置
            final K key;
            V value;
            Node<K,V> next;   //链表的下一个node

            Node(int hash, K key, V value, Node<K,V> next) { ... }
            public final K getKey(){ ... }
            public final V getValue() { ... }
            public final String toString() { ... }
            public final int hashCode() { ... }
            public final V setValue(V newValue) { ... }
            public final boolean equals(Object o) { ... }
    }


                                                

Node 是 HashMap 的一个内部类，实现了 Map.Entry 接口，本质就是一个映射(键值对)。上图中的每个黑色圆点就是一个 Node 对象。

\(2\) HashMap 就是使用哈希表来存储的。哈希表为解决冲突，可以采用开放地址法和链地址法等方式，Java 中 HashMap 采用了链地址法。链地址法，简单来说，就是数组加链表的结合。在每个数组元素上都有一个链表结构，当数据被 Hash 后，得到数组下标，把数据放在对应下标元素的链表上。例如程序执行下面代码：

    map.put("name","makefeixiang");

系统将调用”name”这个 key 的 hashCode()方法得到其 hashCode 值（该方法适用于每个 Java 对象），然后再通过 Hash 算法的后两步运算来定位该键值对的存储位置，有时两个 key 会定位到相同的位置，表示发生了 Hash 碰撞。当然 Hash 算法计算结果越分散均匀，Hash 碰撞的概率就越小，map 的存取效率就会越高。

                                                    
    /**
      * 计算key的hash值。
      */
     static final int hash(Object key) {
         int h;
         return (key == null) ? 0 : (h = key.hashCode()) ^ (h >>> 16);
     }


                                                

当然如果哈希桶数组很大，即便是较差的 hash 算法也会比较分散，有较好的效果，然而，如果哈希桶数组很小，即使好的 Hash 算法也会出现较多 hash 碰撞，因此就需要在空间成本和时间成本之间权衡，其实就是在根据实际情况确定哈希桶数组的大小，并在此基础上设计好的 hash 算法来减少 Hash 碰撞。那么通过什么方式来控制 map 使得 Hash 碰撞的概率又小，哈希桶数组（Node\[\] table）占用空间又少呢？答案就是好的 Hash 算法和扩容机制。\
HashMap 的扩容机制就是通过 threshold = length \* Load factor 来做是否扩容的决策。也就是说，在数组定义好长度之后，负载因子越大，所能容纳的键值对个数越多。当然，负载因子也不是越大越好，JDK 设计者给出了一个相对来说比较均衡的方案，Load factor 为负载因子(默认值是 0.75)，一般我们不对这个参数做修改。

### [](#功能实现-方法 "#功能实现-方法")功能实现-方法

HashMap 的内部功能实现很多，本文主要从根据 key 获取 HashMap 数组索引、put 方法的执行、扩容、获取 HashMap 对应 key 的值等几个具有代表性的点深入展开讲解。

#### [](#1-确定哈希桶数组索引位置 "#1-确定哈希桶数组索引位置")1. 确定哈希桶数组索引位置

不管增加、删除、查找键值对，定位到哈希桶数组的索引都是很关键的第一步。HashMap 的数据结构是数组和链表或者红黑树的结合，所以我们希望这个 HashMap 里面的元素位置尽量分布均匀，使得每个位置上的元素数量只有一个，那么当我们用 hash 算法求得这个位置的时候，就可以马上找到，不用遍历链表，查询的时间复杂度也仅仅是 O(n)。我们来看看源码的实现：

                                                    
    // 方法1，代码段1
    static final int hash(Object key) {
       int h;
       return (key == null) ? 0 : (h = key.hashCode()) ^ (h >>> 16);
    }

    // 当我们使用hash时，代码段2
    if ((p = tab[i = (n - 1) & hash]) == null)
             tab[i] = newNode(hash, key, value, null);


                                                

这里的 Hash 算法本质上就是三步：**取 key 的 hashCode 值、高位运算、取模运算。**

#### [](#2-分析HashMap的put方法 "#2-分析HashMap的put方法")2. 分析 HashMap 的 put 方法

①.判断键值对数组 table\[i\]是否为空或为 null，否则执行 resize()进行扩容；\
②.根据键值 key 计算 hash 值得到插入的数组索引 i，如果 table\[i\]==null，直接新建节点添加，转向⑥，如果 table\[i\]不为空，转向③；\
③.判断 table\[i\]的首个元素是否和 key 一样，如果相同直接覆盖 value，否则转向④，这里的相同指的是 hashCode 以及 equals；\
④.判断 table\[i\] 是否为 treeNode，即 table\[i\] 是否是红黑树，如果是红黑树，则直接在树中插入键值对，否则转向⑤；\
⑤.遍历 table\[i\]，判断链表长度是否大于 8，大于 8 的话把链表转换为红黑树，在红黑树中执行插入操作，否则进行链表的插入操作；遍历过程中若发现 key 已经存在直接覆盖 value 即可；\
⑥.插入成功后，判断实际存在的键值对数量 size 是否超过了最大容量 threshold，如果超过，进行扩容。

                                                    
    final V putVal(int hash, K key, V value, boolean onlyIfAbsent,
                   boolean evict) {
        Node<K,V>[] tab; Node<K,V> p; int n, i;
        // 步骤①：tab为空则创建
        if ((tab = table) == null || (n = tab.length) == 0)
            n = (tab = resize()).length;
        // 步骤②：计算index，并对null做处理 
        if ((p = tab[i = (n - 1) & hash]) == null)
            tab[i] = newNode(hash, key, value, null);
        else {
            Node<K,V> e; K k;
            // 步骤③：节点key存在，直接覆盖value
            if (p.hash == hash &&
                ((k = p.key) == key || (key != null && key.equals(k))))
                e = p;
            // 步骤④：判断该链为红黑树
            else if (p instanceof TreeNode)
                e = ((TreeNode<K,V>)p).putTreeVal(this, tab, hash, key, value);
            // 步骤⑤：该链为链表
            else {
                for (int binCount = 0; ; ++binCount) {
                    if ((e = p.next) == null) {
                        p.next = newNode(hash, key, value, null);
                        //链表长度大于8转换为红黑树进行处理
                        if (binCount >= TREEIFY_THRESHOLD - 1) // -1 for 1st
                            treeifyBin(tab, hash);
                        break;
                    }
                    // key已经存在直接覆盖value
                    if (e.hash == hash &&
                        ((k = e.key) == key || (key != null && key.equals(k))))
                        break;
                    p = e;
                }
            }
            if (e != null) { // existing mapping for key
                V oldValue = e.value;
                if (!onlyIfAbsent || oldValue == null)
                    e.value = value;
                afterNodeAccess(e);
                return oldValue;
            }
        }
        ++modCount; // 用来实现迭代时被修改的快速失败策略
        // 步骤⑥：超过最大容量 就扩容
        if (++size > threshold)
            resize();
        afterNodeInsertion(evict);
        return null;
    }


                                                

#### [](#3-扩容机制的实现 "#3-扩容机制的实现")3. 扩容机制的实现

扩容(resize)就是重新计算容量，向 HashMap 对象里不停地添加元素，**当 HashMap 对象内部的数组长度 大于 DEFAULT_LOAD_FACTOR \* DEFAULT_INITIAL_CAPACITY**，HashMap 就需要扩大数组的长度，以便能装入更多的元素。方法是使用一个新的数组代替已有的容量小的数组。

我们分析下 resize 的源码，鉴于 JDK1.8 融入了红黑树，较复杂，为了便于理解我们仍然使用 JDK1.7 的代码，本质上区别不大，具体区别后文再说。\

                                                    
    final Node<K,V>[] resize() {
        Node<K,V>[] oldTab = table;
        int oldCap = (oldTab == null) ? 0 : oldTab.length;
        int oldThr = threshold;
        int newCap, newThr = 0;
        if (oldCap > 0) {
            // 超过最大值就不再扩充了
            if (oldCap >= MAXIMUM_CAPACITY) {
                threshold = Integer.MAX_VALUE;
                return oldTab;
            }
            // 没超过最大值，就扩充为原来的2倍
            else if ((newCap = oldCap << 1) < MAXIMUM_CAPACITY &&
                     oldCap >= DEFAULT_INITIAL_CAPACITY)
                newThr = oldThr << 1; // double threshold
        }
        else if (oldThr > 0) // initial capacity was placed in threshold
            newCap = oldThr;
        else {               // zero initial threshold signifies using defaults
            newCap = DEFAULT_INITIAL_CAPACITY;
            newThr = (int)(DEFAULT_LOAD_FACTOR * DEFAULT_INITIAL_CAPACITY);
        }
        // 计算新的resize上限
        if (newThr == 0) {
            float ft = (float)newCap * loadFactor;
            newThr = (newCap < MAXIMUM_CAPACITY && ft < (float)MAXIMUM_CAPACITY ?
                      (int)ft : Integer.MAX_VALUE);
        }
        threshold = newThr;
        @SuppressWarnings({"rawtypes","unchecked"})
            Node<K,V>[] newTab = (Node<K,V>[])new Node[newCap];
        table = newTab;
        if (oldTab != null) {
            // 把每个bucket都移动到新的buckets中
            for (int j = 0; j < oldCap; ++j) {
                Node<K,V> e;
                if ((e = oldTab[j]) != null) {
                    oldTab[j] = null;
                    if (e.next == null)
                        newTab[e.hash & (newCap - 1)] = e;
                    // 
                    else if (e instanceof TreeNode)
                        ((TreeNode<K,V>)e).split(this, newTab, j, oldCap);
                    else { // 链表优化重hash的代码块
                        Node<K,V> loHead = null, loTail = null;
                        Node<K,V> hiHead = null, hiTail = null;
                        Node<K,V> next;
                        do {
                            next = e.next;
                            // 原索引
                            if ((e.hash & oldCap) == 0) {
                                if (loTail == null)
                                    loHead = e;
                                else
                                    loTail.next = e;
                                loTail = e;
                            }
                            // 原索引+oldCap
                            else {
                                if (hiTail == null)
                                    hiHead = e;
                                else
                                    hiTail.next = e;
                                hiTail = e;
                            }
                        } while ((e = next) != null);
                        // 原索引放到bucket里
                        if (loTail != null) {
                            loTail.next = null;
                            newTab[j] = loHead;
                        }
                        // 原索引+oldCap放到bucket里
                        if (hiTail != null) {
                            hiTail.next = null;
                            newTab[j + oldCap] = hiHead;
                        }
                    }
                }
            }
        }
        return newTab;
    }


                                                

#### [](#4-HashMap中根据key获取value代码实现 "#4-HashMap中根据key获取value代码实现")4. HashMap 中根据 key 获取 value 代码实现

相比于上面几个，HashMap 中获取 value 相对来说就简单许多，基本逻辑就是根据 key 算出 hash 值定位到哈希桶的索引，当 key 就是当前索引的值则直接返回其对应的 value，反之用 key 去遍历 equal 该索引下的 key，直到找到位置。\

                                                    
    final Node<K,V> getNode(int hash, Object key) {
        Node<K,V>[] tab; Node<K,V> first, e; int n; K k;
        if ((tab = table) != null && (n = tab.length) > 0 &&
            (first = tab[(n - 1) & hash]) != null) {
            if (first.hash == hash && // always check first node
                ((k = first.key) == key || (key != null && key.equals(k))))
                return first;
            if ((e = first.next) != null) {
                if (first instanceof TreeNode)
                    return ((TreeNode<K,V>)first).getTreeNode(hash, key);
                do {
                    if (e.hash == hash &&
                        ((k = e.key) == key || (key != null && key.equals(k))))
                        return e;
                } while ((e = e.next) != null);
            }
        }
        return null;
    }


                                                

## [](#HashMap的线程安全问题 "#HashMap的线程安全问题")HashMap 的线程安全问题

在多线程使用场景中，应该尽量不要使用线程不安全的 HashMap，而应该使用线程安全的 ConcurrentHashMap。那么 HashMap 线程不安全的性质表现在哪里呢？下面来分析一下并发场景下使用 HashMap 可能造成死循环的问题。在 HashMap 的 resize 方法中，我们可以看到

                                                    
    Node<K,V> loHead = null, loTail = null;
       Node<K,V> hiHead = null, hiTail = null;
       Node<K,V> next;
       do {
           next = e.next;
           if ((e.hash & oldCap) == 0) {
               if (loTail == null)
                   loHead = e;
               else
                   loTail.next = e;
               loTail = e;
           }
           else {
               if (hiTail == null)
                   hiHead = e;
               else
                   hiTail.next = e;
               hiTail = e;
           }
       } while ((e = next) != null);


                                                

由于楼主本人才疏学浅，具体过程就不再分析，想要了解的请移步<a href="https://link.juejin.cn?target=https%3A%2F%2Fcoolshell.cn%2Farticles%2F9606.html" target="_blank" data-ref="nofollow noopener noreferrer" title="https://coolshell.cn/articles/9606.html">疫苗：Java HASHMAP 的死循环</a>

## [](#小结 "#小结")小结

\(1\) 扩容是一个特别耗性能的操作，因此初始化 HashMap 的时候给一个数值，避免 map 频繁扩容的情况发生。

\(2\) 负载因子是可以修改的，但是建议一般情况下不要轻易修改。

\(3\) HashMap 是线程不安全的，不要在并发的环境中使用 HashMap，建议使用 ConcurrentHashMap 或者 Collections.synchronizedMap()。

\(4\) JDK1.8 引入红黑树在很大程度上优化了 HashMap 的性能。

## [](#参考文章 "#参考文章")参考文章

- <a href="https://link.juejin.cn?target=https%3A%2F%2Ftech.meituan.com%2Fjava-hashmap.html" target="_blank" data-ref="nofollow noopener noreferrer" title="https://tech.meituan.com/java-hashmap.html">Java 8 系列之重新认识 HashMap</a>
- <a href="https://link.juejin.cn?target=https%3A%2F%2Fcoolshell.cn%2Farticles%2F9606.html" target="_blank" data-ref="nofollow noopener noreferrer" title="https://coolshell.cn/articles/9606.html">疫苗：Java HASHMAP 的死循环</a>
