---
aliases: ["/zh-cn/posts/mysql-decunchujiegou-ye/"]
categories: ["后端"]
title: "MySQL 的存储结构-页"
date: "2023-12-20T16:05:02+08:00"
tags: ["后端", "MySQL", "面试"]
summary: "先从几个问题开始 innodb 引擎下 varchar 类型的最大长度？什么情况下我们需要水平分表？为什么？"
translationKey: "mysql-decunchujiegou-ye"
---

> 📌 本文原发布于掘金社区：[MySQL 的存储结构-页](https://juejin.cn/post/7314498126088962099)

# 先从几个问题开始

1.  InnoDB 引擎下 varchar 类型的最大长度？
2.  什么情况下我们需要水平分表？为什么？

# MySQL 存储结构简介

MySQL InnoDB 存储引擎逻辑存储结构

<img src="https://p6-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/8a98e0aad1a64b3ba97c61c72efd9375~tplv-k3u1fbpfcp-jj-mark:3024:0:0:0:q75.awebp#?w=612&amp;h=410&amp;s=131224&amp;e=png&amp;b=f6f6f6" loading="lazy" alt="image.png" />

## 1、表空间（table space）

表空间（Tablespace）是一个逻辑容器，表空间存储的对象是段，在一个表空间中可以有一个或多个段，但是一个段只能属于一个表空间。数据库由一个或多个表空间组成，表空间从管理上可以划分为系统表空间、用户表空间、撤销表空间、临时表空间等。

在 InnoDB 中存在两种表空间的类型：共享表空间和独立表空间。如果是共享表空间就意味着多张表共用一个表空间。如果是独立表空间，就意味着每张表有一个独立的表空间，也就是数据和索引信息都会保存在自己的表空间中。独立的表空间可以在不同的数据库之间进行迁移。

InnoDB 把数据保存在表空间内，表空间可以看作是 InnoDB 存储引擎逻辑结构的最高层。本质上是一个由一个或多个磁盘文件组成的虚拟文件系统。InnoDB 用表空间并不只是存储表和索引，还保存了回滚段、双写缓冲区等。

## **2、****段****（segment）**

范围查询，其实是对 B+ 树叶子节点中的记录进行顺序扫描，而如果不区分叶子节点和非叶子节点，统统把节点代表的页面放到申请到的区中的话，进行范围扫描的效果就大打折扣了(**这里解释一下：因为 B+树从上到下查询，如果叶子和非叶子节点混****在****同一个区中，会让****一个****区中存储****的****页目录数据大大减少，造成多个区随机 IO 发生**)。所以对 B+ 树的叶子节点和非叶子节点进行了区别对待，也就是说叶子节点有自己独有的区，非叶子节点也有自己独有的区。存放叶子节点的区的集合就算是一个段（ segment ），存放非叶子节点的区的集合也算是一个段。也就是说一个索引会生成 2 个段，一个叶子节点段，一个非叶子节点段。

默认情况下一个使用 InnoDB 存储引擎的表只有一个聚簇索引，一个索引会生成 2 个段，**而段是以区为单位申请存储空间的**，一个区默认占用 1M 存储空间，所以默认情况下一个只存了几条记录的小表也需要 2M 的存储空间。

## **3、****区****（extent）**

在 InnoDB 存储引擎中，一个区会分配 64 个连续的页。因为 InnoDB 中的页大小默认是 16KB，所以一个区的大小是 64\*16KB=1MB。在任何情况下每个区大小都为 1MB，为了保证页的连续性，InnoDB 存储引擎每次从磁盘一次申请 4-5 个区。默认情况下，InnoDB 存储引擎的页大小为 16KB，即一个区中有 64 个连续的页。

### 为什么要划分多个区呢？

本质上还是为了性能！

如果我们表中数据量很少的话，比如说你的表中只有几十条、几百条数据的话，的确用不到 区 的概念，因为简单的几个页就能把对应的数据存储起来，但是你架不住表里的记录越来越多呀。

从理论上说，不引入区的概念只使用 页 的概念对存储引擎的运行并没啥影响，但是我们来考虑一下下边这个场景：

我们每向表中插入一条记录，本质上就是向该表的聚簇索引以及所有二级索引代表的 B+ 树的节点中插入数据。而 B+ 树的每一层中的页都会形成一个双向链表，如果是以 页 为单位来分配存储空间的话，双向链表相邻的两个页之间的物理位置可能离得非常远。我们介绍 B+ 树索引的适用场景的时候特别提到范围查询只需要定位到最左边的记录和最右边的记录，然后沿着双向链表一直扫描就可以了，而如果链表中相邻的两个页物理位置离得非常远，就是所谓的随机 I/O。再一次强调，磁盘的速度和内存的速度差了好几个数量级，随机 I/O 是非常慢的，所以我们应该**尽量让链表中相邻的页的物理位置也相邻，这样进行范围查询的时候才可以使用所谓的顺序 I/O**。

所以才引入了区（ extent ）的概念，一个区就是在物理位置上连续的 64 个页。在表中数据量大的时候，为某个索引分配空间的时候就不再以页为单位分配了，而是以区为单位分配，甚至在表中的数据非常多的时候，可以一次性分配多个连续的区。虽然可能造成一点点空间的浪费（数据不足填充满整个区），但是从性能角度看，可以消除很多的随机 I/O，功大于过嘛！

## **4、****页****（Page）**

页是 InnoDB 存储引擎磁盘管理（数据读取）的最小单位，每个页默认 16KB；

InnoDB 存储引擎中，常见的页类型有：

1.  数据页（B-tree Node)

2.  undo 页（undo Log Page）

3.  系统页（System Page）

4.  事务数据页（Transaction System Page）

5.  插入缓冲位图页（Insert Buffer Bitmap）

6.  插入缓冲空闲列表页（Insert Buffer Free List）

7.  未压缩的二进制大对象页（Uncompressed BLOB Page）

8.  压缩的二进制大对象页（compressed BLOB Page）

# InnoDB 页定义

真正处理数据的过程是发生在内存中的，所以需要把磁盘中的数据加载到内存中，如果是处理写入或修改请求的话，还需要把内存中的内容刷新到磁盘上。而我们知道读写磁盘的速度非常慢，和内存读写差了几个数量级，所以当我们想从表中获取某些记录时，InnoDB 存储引擎需要一条一条地把记录从磁盘上读出来么？不，那样会慢死，InnoDB 采取的方式是：将数据划分为若干个页，以页作为磁盘和内存之间交互的基本单位，InnoDB 中页的大小一般为 16 KB。也就是在一般情况下，一次最少从磁盘中读取 16KB 的内容到内存中，一次最少把内存中的 16KB 内容刷新到磁盘中。

# 页的结构

<img src="https://p9-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/f7f81322d2e341f4880b8cd199e24f54~tplv-k3u1fbpfcp-jj-mark:3024:0:0:0:q75.awebp#?w=416&amp;h=448&amp;s=70440&amp;e=png&amp;b=fdfbfb" loading="lazy" alt="image.png" />

从图中可以看出，一个 InnoDB 数据页的存储空间大致被划分成了 7 个部分，有的部分占用的字节数是确定的，有的部分占用的字节数是不确定的。

各部分的作用：

# 记录在页中的存储

在页的 7 个组成部分中，我们自己存储的记录会按照我们指定的行格式存储到 User Records 部分。但是在一开始生成页的时候，其实并没有 User Records 这个部分，每当我们插入一条记录，都会从 Free Space 部分，也就是尚未使用的存储空间中申请一个记录大小的空间划分到 User Records 部分，当 Free Space 部分的空间全部被 User Records 部分替代掉之后，也就意味着这个页使用完了，如果还有新的记录插入的话，就需要去申请新的页了，这个过程的图示如下：<img src="https://p1-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/85dbe8f56e5c499fb3ddecd0b95e49fa~tplv-k3u1fbpfcp-jj-mark:3024:0:0:0:q75.awebp#?w=612&amp;h=229&amp;s=45546&amp;e=png&amp;b=eef4e9" loading="lazy" alt="image.png" />

## 行记录格式（Compact 类型）

<img src="https://p6-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/57e04d0dd4ca4e5cab01744b28818d4f~tplv-k3u1fbpfcp-jj-mark:3024:0:0:0:q75.awebp#?w=612&amp;h=195&amp;s=31439&amp;e=png&amp;b=fefdfd" loading="lazy" alt="image.png" />

<img src="https://p9-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/bcf3cdf3b10b4a929ac3c030d72df27a~tplv-k3u1fbpfcp-jj-mark:3024:0:0:0:q75.awebp#?w=612&amp;h=259&amp;s=31545&amp;e=png&amp;b=fefefe" loading="lazy" alt="image.png" />

<img src="https://p9-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/6c6f3a7fa7104a30b6f4a039b4ab39eb~tplv-k3u1fbpfcp-jj-mark:3024:0:0:0:q75.awebp#?w=612&amp;h=261&amp;s=41752&amp;e=png&amp;b=fefefe" loading="lazy" alt="image.png" />

## 行记录在 User_Records 中的存在形式

<img src="https://p9-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/e4d48e98d0624700bea09ed8cd7515e2~tplv-k3u1fbpfcp-jj-mark:3024:0:0:0:q75.awebp#?w=612&amp;h=322&amp;s=52178&amp;e=png&amp;b=fcf6f4" loading="lazy" alt="image.png" />

通过 next_record 属性，可以让页中的多条记录形成一个链表，链表是有序的，按照主键顺序排序。

## 行记录的删除

<img src="https://p1-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/5233e3de2f6c452292c58393fe25680b~tplv-k3u1fbpfcp-jj-mark:3024:0:0:0:q75.awebp#?w=612&amp;h=313&amp;s=52258&amp;e=png&amp;b=fdf8f6" loading="lazy" alt="image.png" />

删除第 2 条记录前后主要发生了这些变化：

第 2 条记录并没有从存储空间中移除，而是把该条记录的 delete_mask 值设置为 1。

第 2 条记录的 next_record 值变为了 0，意味着该记录没有下一条记录了。

第 1 条记录的 next_record 指向了第 3 条记录。

最大记录的 n_owned 值从 5 变成了 4。

所以，不论我们怎么对页中的记录做增删改操作，InnoDB 始终会维护一条记录的单链表，链表中的各个节点是按照主键值由小到大的顺序连接起来的。

另外，当插入的主键和被删除的主键相同时，删除的行记录存储空间是可以被复用的。

# 页目录

页目录就是 page 的目录，就像书的目录，作用是加快查找。

记录在页中按照主键值由小到大顺序串联成一个单链表，那如果我们想根据主键值查找页中的某条记录该咋办呢？比如说这样的查询语句：

```
SELECT * FROM test WHERE id = 100;
```

从 Infimum 记录（最小记录）开始，沿着链表一直往后找就可以了。

但效率低了些...

更好的办法是：页目录

## 页目录的生成

它的生成过程是这样的：

1.  将所有正常的记录（包括最大和最小记录，不包括标记为已删除的记录）划分为几个组。

2.  每个组的最后一条记录（也就是组内最大的那条记录）的头信息中的 n_owned 属性表示该记录拥有多少条记录，也就是该组内共有几条记录。

3.  将每个组的最后一条记录的地址偏移量单独提取出来按顺序存储到靠近页的尾部的地方，这个地方就是所谓的 Page Directory，也就是 页目录。页面目录中的这些地址偏移量被称为 槽（英文名：Slot ），所以这个页面目录就是由 槽组成的。

### 举例

<img src="https://p6-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/49ce12d33e0249ee8259f5129271c87a~tplv-k3u1fbpfcp-jj-mark:3024:0:0:0:q75.awebp#?w=612&amp;h=339&amp;s=47673&amp;e=png&amp;b=fdfcfc" loading="lazy" alt="image.png" />

分组规则：

对于最小记录所在的分组只能有 1 条记录，最大记录所在的分组拥有的记录条数只能在 1~~8 条之间，剩下的分组中记录的条数范围只能是 4~~8 条之间。

每个槽中存储的是：当前分组中最大记录的地址偏移量，偏移量从 page 的 0 字节开始计算

## 查找步骤

1.  通过二分法确定该记录所在的槽，并找到该槽中主键值最小的那条记录。

2.  通过记录的 next_record 属性遍历该槽所在的组中的各个记录。

<img src="https://p9-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/6417e27d6f6e459ab05ccd1873974f88~tplv-k3u1fbpfcp-jj-mark:3024:0:0:0:q75.awebp#?w=612&amp;h=378&amp;s=81365&amp;e=png&amp;b=fcfaf9" loading="lazy" alt="image.png" />

# Page Header（页面头部）

专门针对数据页的。

<img src="https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/7655576883be4ed38ec0bbe787435daa~tplv-k3u1fbpfcp-jj-mark:3024:0:0:0:q75.awebp#?w=612&amp;h=404&amp;s=87524&amp;e=png&amp;b=fdfdfd" loading="lazy" alt="image.png" />

# File Header（文件头）

Page Header 是专门针对 数据页 记录的各种状态信息，比方说页里头有多少个记录了呀，有多少个 槽了呀。我们现在描述的 File Header 针对各种类型的页都通用，也就是说不同类型的页都会以 File Header 作为第一个组成部分，占用固定的 38 个字节

<img src="https://p1-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/72f43fe3571549e38ce43708042bc262~tplv-k3u1fbpfcp-jj-mark:3024:0:0:0:q75.awebp#?w=612&amp;h=259&amp;s=44727&amp;e=png&amp;b=fcfcfc" loading="lazy" alt="image.png" />

FIL_PAGE_SPACE_OR_CHKSUM

这个代表当前页面的校验和（checksum）。啥是个校验和？就是对于一个很长很长的字节串来说，我们会通过某种算法来计算一个比较短的值来代表这个很长的字节串，这个比较短的值就称为 校验和。这样在比较两个很长的字节串之前先比较这两个长字节串的校验和，如果校验和都不一样，两个长字节串肯定是不同的，所以省去了直接比较两个较长的字节串的时间损耗。

FIL_PAGE_OFFSET

每一个 页 都有一个单独的页号，就跟你的身份证号码一样，InnoDB 通过页号可以唯一定位一个 页。

FIL_PAGE_PREV 和 FIL_PAGE_NEXT

InnoDB 可能无法一次性为这么多数据分配一个非常大的存储空间，如果分散到多个不连续的页中存储的话，需要把这些页关联起来，FIL_PAGE_PREV 和 FIL_PAGE_NEXT 就分别代表本页的上一个和下一个页的页号。这样通过建立一个双向链表把许许多多的页就都串联起来了，而无需这些页在物理上真正连着。需要注意的是，并不是所有类型的页都有上一个和下一个页的属性，在数据页（也就是类型为 FIL_PAGE_INDEX 的页）是有这两个属性的，所以所有的数据页其实是一个双链表（很重要）

# InnoDB 的索引结构

MySQL 中的索引有多种，在 InnoDB 中，默认情况下所有主键都会自动创建一个 B+ 树索引，所以我们仅讨论 B+ 树索引。

索引的结构示意图：

<img src="https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/5580ab6ff2204f3089b4d3c47b2a2425~tplv-k3u1fbpfcp-jj-mark:3024:0:0:0:q75.awebp#?w=612&amp;h=339&amp;s=78264&amp;e=png&amp;b=faf8f6" loading="lazy" alt="image.png" />

# 对我们的启发

1.  我们设计系统时也可以参考分层缓存的理念，提升系统的性能。比如：数据记录不多，且频繁读取其中的行，可以一次查出所有（或部分）
2.  将相关数据放置在相邻的物理位置上，以利用空间局部性原则。比如：在选择 Redis 数据结构时，相关数据可以考虑使用 hash 来替代 string
