---
categories: ["后端"]
title: "散列表"
date: "2018-11-23T14:54:25+08:00"
tags: ["Java", "数据结构", "编程语言"]
summary: "是根据键 (Key) 而直接访问在内存存储位置的数据结构。也就是说，它通过计算一个关于键值的函数，将所需查询的数据映射到表中一个位置来访问记录，这加快了查找速度。"
translationKey: "sanliebiao"
---

> 📌 本文原发布于掘金社区：[散列表](https://juejin.cn/post/6844903720157708296)

> 原文地址：<a href="https://link.juejin.cn?target=https%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2018%2F799a%2F%3F_ref%3Djuejin" target="_blank" data-ref="nofollow noopener noreferrer" title="https://www.hchstudio.cn/article/2018/799a/?_ref=juejin">haifeiWu 和他朋友们的博客</a>\
> 博客地址：<a href="https://link.juejin.cn?target=https%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2018%2F799a%2F%3F_ref%3Djuejin" target="_blank" data-ref="nofollow noopener noreferrer" title="https://www.hchstudio.cn/article/2018/799a/?_ref=juejin">www.hchstudio.cn</a>\
> 欢迎转载，转载请注明作者及出处，谢谢！

做个预警，这篇文章有点硬……

## 什么是散列表

是根据键 (Key) 而直接访问在内存存储位置的数据结构。也就是说，它通过计算一个关于键值的函数，将所需查询的数据映射到表中一个位置来访问记录，这加快了查找速度。这个映射函数称做散列函数，存放记录的数组称做散列表。

## 通俗的解释

一个通俗的例子是，为了查找电话簿中某人的号码，可以创建一个按照人名首字母顺序排列的表（即建立人名<span class="math math-inline"><span class="katex"><span class="katex-mathml">$`{\displaystyle x}`$</span></span></span> 到首字母 <span class="math math-inline"><span class="katex"><span class="katex-mathml">$`{\displaystyle F(x)}`$</span></span></span> 的一个函数关系），在首字母为 W 的表中查找 `王` 姓的电话号码，显然比直接查找就要快得多。这里使用人名作为关键字，`取首字母` 是这个例子中散列函数的函数法则 <span class="math math-inline"><span class="katex"><span class="katex-mathml">$`{\displaystyle F(x)}`$</span></span></span>，存放首字母的表对应散列表。关键字和函数法则理论上可以任意确定。

## 基本思想

若关键字为 <span class="math math-inline"><span class="katex"><span class="katex-mathml">$`{\displaystyle k}`$</span></span></span>，则其值存放在 <span class="math math-inline"><span class="katex"><span class="katex-mathml">$`{\displaystyle f(k)}`$</span></span></span> 的存储位置上。由此，不需比较便可直接取得所查记录。称这个对应关系 <span class="math math-inline"><span class="katex"><span class="katex-mathml">$`{\displaystyle f}`$</span></span></span> 为散列函数

## 散列表几个重要概念：

散列函数、装载因子、散列冲突

### 装载因子：

<span class="math math-inline"><span class="katex"><span class="katex-mathml">$`{\displaystyle \alpha }`$</span></span></span> = 填入表中的元素个数 / 散列表的长度

<span class="math math-inline"><span class="katex"><span class="katex-mathml">$`{\displaystyle \alpha }`$</span></span></span> 是散列表装满程度的标志因子。由于表长是定值，<span class="math math-inline"><span class="katex"><span class="katex-mathml">$`{\displaystyle \alpha }`$</span></span></span> 与“填入表中的元素个数”成正比，所以，<span class="math math-inline"><span class="katex"><span class="katex-mathml">$`{\displaystyle \alpha }`$</span></span></span> 越大，表明填入表中的元素越多，产生冲突的可能性就越大；反之，<span class="math math-inline"><span class="katex"><span class="katex-mathml">$`{\displaystyle \alpha }`$</span></span></span> 越小，表明填入表中的元素越少，产生冲突的可能性就越小。实际上，散列表的平均查找长度是载荷因子 <span class="math math-inline"><span class="katex"><span class="katex-mathml">$`{\displaystyle \alpha }`$</span></span></span> 的函数，只是不同处理冲突的方法有不同的函数。

对于开放定址法，装载因子是特别重要因素，应严格限制在 `0.7-0.8` 以下。超过 `0.8`，查表时的 CPU 缓存不命中（`cache missing`）按照指数曲线上升。因此，一些采用开放定址法的 `hash` 库，如 `Java` 的系统库限制了装载因子为 `0.75`，超过此值将 `resize` 散列表。

### 散列冲突：

就是指多个元素通过散列函数计算得到的散列地址是相同的。

### 散列函数：

**散列函数选取原则**：

`好的散列函数 = 计算简单 + 分布均匀`

#### 数据结构中的散列函数：

1，直接定址法：取关键字或关键字的某个线性函数值为散列地址。即<span class="math math-inline"><span class="katex"><span class="katex-mathml">$`{\displaystyle hash(k)=k}`$</span></span></span>或<span class="math math-inline"><span class="katex"><span class="katex-mathml">$`{\displaystyle hash(k)=a\cdot k+b}`$</span></span></span>，其中 <span class="math math-inline"><span class="katex"><span class="katex-mathml">$`{\displaystyle a\,b}`$</span></span></span> 为常数。

2，数字分析法：数字分析法通常适用于散列表中可能出现的关键字都是事先知道的情况，例如我们现在要存储某家公司员工登记表，如果用手机号作为关键字，那么我们发现抽取后面的四位数字作为散列地址是不错的选择，同理存储身份证号码时，也可以采用这样的逻辑。

3，平方取中法：平方取中法是将关键字平方之后取中间若干位数字作为散列地址。这种方法适用于不知道关键字的分布，且数值的位数又不是很大的情况。

4，随机数法：选择一个随机数，取关键字的随机函数值为它的散列地址，<span class="math math-inline"><span class="katex"><span class="katex-mathml">$`f(key) = random(key)`$</span></span></span>

5，除留取余法：取关键字被某个不大于散列表表长 `m` 的数 `p` 除后所得的余数为散列地址。即 <span class="math math-inline"><span class="katex"><span class="katex-mathml">$`{\displaystyle hash(k)=k\,{\bmod {\,}}p}, {\displaystyle p\leq m}`$</span></span></span> `p`为小于 m 的最大质数，所谓素数就是指只能被 `1` 与它本身整除的数。

### 主要的散列冲突的解决办法

#### 开放寻址法：

所谓的开放定址法就是一旦发生了冲突，就去寻找下一个空的散列地址，只要散列表足够大，空的散列地址总能找到，并将记录存入其中。

主要是有**线性探查** <span class="math math-inline"><span class="katex"><span class="katex-mathml">$`fi(key) = (f(key)+di) MOD m (di=1,2,…,m-1)`$</span></span></span> **平方探查** <span class="math math-inline"><span class="katex"><span class="katex-mathml">$`fi(key) = (f(key)+di) MOD m (di=1²,-1²,2²,-2²…,q²,-q²,q<=m/1)`$</span></span></span>

**拉链法（链地址法）** 将散列到同一个存储位置的所有元素保存在一个链表中。<img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/11/23/1673f5308d3db46f~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp#?w=421&amp;h=339&amp;s=9722&amp;e=png&amp;b=ffffff" title="链地址表" loading="lazy" alt="链地址表" />

#### 再散列法：

即在上次散列计算发生冲突时，利用该次冲突的散列函数地址产生新的散列函数地址，直到冲突不再发生。

## Example

### 开放定址法

#### 散列表查找的伪代码

``` scss

// 使用除留余数法
int Hash(int key)
{
    return key % HASHSIZE;        //除数一般小于等于表长的最大素数
}

// 插入关键字到散列表
void InsertHash(HashTable *H, int key)
{
    int addr;

    addr = Hash(key);     //只是得到一个偏移地址

    while( H->elem[addr] != NULLKEY )   // 如果不为空，则冲突出现
    {
        addr = (addr + 1) % HASHSIZE;   // 开放定址法的线性探测
    }

    H->elem[addr] = key;
}

// 散列表查找关键字
int SearchHash(HashTable H, int key, int *addr)
{
    *addr = Hash(key);

    while( H.elem[*addr] != key )
    {
        *addr = (*addr + 1) % HASHSIZE;
        if( H.elem[*addr] == NULLKEY || *addr == Hash(key) )   //后面那个条件说明循环回到原点
        {
            return -1;
        }
    }

    return 0;
}
```

#### `Java` 中的散列

`Java` 中的散列冲突解决方法就是上文中提到的开放定址法。散列函数如下。

``` java
    static final int hash(Object key) { 
        int h;
        return (key == null) ? 0 : (h = key.hashCode()) ^ (h >>> 16);
    }
```

散列查找方法

``` java
    public V get(Object key) {
        Node<K,V> e;
        return (e = getNode(hash(key), key)) == null ? null : e.value;
    }
    
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
```

散列表的插入

``` java
    public V put(K key, V value) {
        return putVal(hash(key), key, value, false, true);
    }
    
    final V putVal(int hash, K key, V value, boolean onlyIfAbsent,
                   boolean evict) {
        Node<K,V>[] tab; Node<K,V> p; int n, i;
        if ((tab = table) == null || (n = tab.length) == 0)
            n = (tab = resize()).length;
        if ((p = tab[i = (n - 1) & hash]) == null)
            tab[i] = newNode(hash, key, value, null);
        else {
            Node<K,V> e; K k;
            if (p.hash == hash &&
                ((k = p.key) == key || (key != null && key.equals(k))))
                e = p;
            else if (p instanceof TreeNode)
                e = ((TreeNode<K,V>)p).putTreeVal(this, tab, hash, key, value);
            else {
                for (int binCount = 0; ; ++binCount) {
                    if ((e = p.next) == null) {
                        p.next = newNode(hash, key, value, null);
                        if (binCount >= TREEIFY_THRESHOLD - 1) // -1 for 1st
                            treeifyBin(tab, hash);
                        break;
                    }
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
        ++modCount;
        if (++size > threshold)
            resize();
        afterNodeInsertion(evict);
        return null;
    }
```

## 小结

最近在学习数据结构的时候，复习了一下散列表的基本概念，因为散列表在我们敲代码的时候用得比较多，所以打好基础还是有必要的。

## 参考链接

- <a href="https://link.juejin.cn?target=https%3A%2F%2Fzh.wikipedia.org%2Fzh-hans%2F%25E5%2593%2588%25E5%25B8%258C%25E8%25A1%25A8" target="_blank" data-ref="nofollow noopener noreferrer" title="https://zh.wikipedia.org/zh-hans/%E5%93%88%E5%B8%8C%E8%A1%A8">维基百科</a>
