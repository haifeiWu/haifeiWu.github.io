---
categories: ["后端"]
title: "聊聊ArrayList源码(基于JDK1.8)"
date: "2018-05-04T21:44:37+08:00"
tags: []
summary: "工作快一年了，近期打算研究一下JDK的源码 ArrayList 是一个数组队列，相当于动态数组。与Java中的数组相比，它的容量能动态增长。它继承于AbstractList，实现了List, RandomAccess, Cloneable, java.io.Serializab…"
---

> 📌 本文原发布于掘金社区：[聊聊ArrayList源码(基于JDK1.8)](https://juejin.cn/post/6844903601983193102)

工作快一年了，近期打算研究一下JDK的源码

- ArrayList 是一个数组队列，相当于动态数组。与Java中的数组相比，它的容量能动态增长。它继承于AbstractList，实现了List, RandomAccess, Cloneable, java.io.Serializable这些接口。
- ArrayList 继承了AbstractList，实现了List。它是一个数组队列，提供了相关的添加、删除、修改、遍历等功能。
- ArrayList 实现了RandmoAccess接口，即提供了随机访问功能。RandmoAccess是java中用来被List实现，为List提供快速访问功能的。在ArrayList中，我们即可以通过元素的序号快速获取元素对象；这就是快速随机访问。<span id="user-content-more"></span>
- ArrayList 实现了Cloneable接口，即覆盖了函数clone()，能被克隆。
- ArrayList 实现java.io.Serializable接口，这意味着ArrayList支持序列化，能通过序列化去传输，包括网络传输与本地文件序列化。
- 和Vector不同，ArrayList中的操作不是线程安全的！所以，建议在单线程中才使用ArrayList，而在多线程中建议选择CopyOnWriteArrayList，当然Vector也可以，但不建议使用。

打个广告，楼主自己造的轮子，感兴趣的请点\[github\]: <a href="https://link.juejin.cn?target=https%3A%2F%2Fgithub.com%2FhaifeiWu%2Flightconf" target="_blank" data-ref="nofollow noopener noreferrer" title="https://github.com/haifeiWu/lightconf">github.com/haifeiWu/li…</a>

## [](#ArrayList的UML图 "#ArrayList的UML图")ArrayList的UML图

<a href="https://link.juejin.cn?target=http%3A%2F%2Fof9xsczb1.bkt.clouddn.com%2FArrayList.png" target="_blank" data-ref="nofollow noopener noreferrer" title="http://of9xsczb1.bkt.clouddn.com/ArrayList.png"><img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/5/4/1632b66eaa19ae2f~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.png" title="UML图" loading="lazy" alt="ArrayList的UML图" /></a>ArrayList的UML图

## [](#ArrayList的成员变量及其含义 "#ArrayList的成员变量及其含义")ArrayList的成员变量及其含义

                                                    
    public class ArrayList<E> extends AbstractList<E>
            implements List<E>, RandomAccess, Cloneable, java.io.Serializable
    {
        private static final long serialVersionUID = 8683452581122892189L;

        /**
         * ArrayList默认初始大小为10.
         */
        private static final int DEFAULT_CAPACITY = 10;

        /**
         * 默认的空值数组
         */
        private static final Object[] EMPTY_ELEMENTDATA = {};

        /**
         * 当ArrayList不传参数时，elementData默认初始化成DEFAULTCAPACITY_EMPTY_ELEMENTDATA
         */
        private static final Object[] DEFAULTCAPACITY_EMPTY_ELEMENTDATA = {};

        /**
         * 实现ArrayList的object数组<br><br/>
         * transient关键字扫盲，在实现Serilizable接口后，将不需要序列化的属性前添加关键字transient，序列化对象的时候，这个属性就不会序列化到指定的目的地中
         */
        transient Object[] elementData; // non-private to simplify nested class access

        /**
         * ArrayList的大小
         */
        private int size;
        
        /**
         * 构造一个初始容量的数组
         */
        public ArrayList(int initialCapacity) {
            if (initialCapacity > 0) {
                this.elementData = new Object[initialCapacity];
            } else if (initialCapacity == 0) {
                this.elementData = EMPTY_ELEMENTDATA;
            } else {
                throw new IllegalArgumentException("Illegal Capacity: "+
                                                   initialCapacity);
            }
        }

        /**
         * 初始化一个size为10的空值ArrayList.
         */
        public ArrayList() {
            this.elementData = DEFAULTCAPACITY_EMPTY_ELEMENTDATA;
        }

        /**
         * 按照集合迭代器返回的顺序构造包含指定集合元素的列表。
         */
        public ArrayList(Collection<? extends E> c) {
            elementData = c.toArray();
            if ((size = elementData.length) != 0) {
                // c.toArray might (incorrectly) not return Object[] (see 6260652)
                if (elementData.getClass() != Object[].class)
                    elementData = Arrays.copyOf(elementData, size, Object[].class);
            } else {
                // replace with empty array.
                this.elementData = EMPTY_ELEMENTDATA;
            }
        }
    }


                                                

## [](#聊聊ArrayList的主要方法实现 "#聊聊ArrayList的主要方法实现")聊聊ArrayList的主要方法实现

                                                    

    /**
     * 获取ArrayList对应下标的元素，时间复杂度为O(1).
     */
    public E get(int index) {
        // 检查数组下标越界问题
        rangeCheck(index);

        return elementData(index);
    }

    /**
     * 将对应下标的元素更新成现在的值
     */
    public E set(int index, E element) {
        // 检查数组下标越界问题
        rangeCheck(index);

        E oldValue = elementData(index);
        elementData[index] = element;
        return oldValue;
    }

    /**
     * ArrayList中追加新值.
     */
    public boolean add(E e) {
        ensureCapacityInternal(size + 1);  // Increments modCount!!
        elementData[size++] = e;
        return true;
    }

    /**
     * 在ArrayList的指定下标下添加值，时间复杂度为O(n)
     */
    public void add(int index, E element) {
        rangeCheckForAdd(index);

        ensureCapacityInternal(size + 1);  // Increments modCount!!
        System.arraycopy(elementData, index, elementData, index + 1,
                         size - index);
        elementData[index] = element;
        size++;
    }

    /**
     * 移除指定下标的值，时间复杂度为O(1)。
     */
    public E remove(int index) {
        rangeCheck(index);

        modCount++;
        E oldValue = elementData(index);

        int numMoved = size - index - 1;
        if (numMoved > 0)
            System.arraycopy(elementData, index+1, elementData, index,
                             numMoved);
        elementData[--size] = null; // clear to let GC do its work

        return oldValue;
    }

    /**
     * 移除指定值，时间复杂度为O(n)。
     */
    public boolean remove(Object o) {
        if (o == null) {
            for (int index = 0; index < size; index++)
                if (elementData[index] == null) {
                    fastRemove(index);
                    return true;
                }
        } else {
            for (int index = 0; index < size; index++)
                if (o.equals(elementData[index])) {
                    fastRemove(index);
                    return true;
                }
        }
        return false;
    }

    /**
     * Increases the capacity of this <tt>ArrayList</tt> instance, if
     * necessary, to ensure that it can hold at least the number of elements
     * specified by the minimum capacity argument.
     *
     * @param   minCapacity   the desired minimum capacity
     */
    public void ensureCapacity(int minCapacity) {
        int minExpand = (elementData != DEFAULTCAPACITY_EMPTY_ELEMENTDATA)
            // any size if not default element table
            ? 0
            // larger than default for default empty table. It's already
            // supposed to be at default size.
            : DEFAULT_CAPACITY;

        if (minCapacity > minExpand) {
            ensureExplicitCapacity(minCapacity);
        }
    }

    private void ensureCapacityInternal(int minCapacity) {
        if (elementData == DEFAULTCAPACITY_EMPTY_ELEMENTDATA) {
            minCapacity = Math.max(DEFAULT_CAPACITY, minCapacity);
        }

        ensureExplicitCapacity(minCapacity);
    }

    private void ensureExplicitCapacity(int minCapacity) {
        modCount++;

        // overflow-conscious code
        if (minCapacity - elementData.length > 0)
            grow(minCapacity);
    }

    /**
     * ArrayList的最大长度是2147483639
     * The maximum size of array to allocate.
     * Some VMs reserve some header words in an array.
     * Attempts to allocate larger arrays may result in
     * OutOfMemoryError: Requested array size exceeds VM limit
     */
    private static final int MAX_ARRAY_SIZE = Integer.MAX_VALUE - 8;

    /**
     * 用于ArrayList扩容的方法，扩容的策略是int newCapacity = oldCapacity + (oldCapacity >> 1)，即每次扩容是原来长度的1.5倍
     * Increases the capacity to ensure that it can hold at least the
     * number of elements specified by the minimum capacity argument.
     *
     * @param minCapacity the desired minimum capacity
     */
    private void grow(int minCapacity) {
        // overflow-conscious code
        int oldCapacity = elementData.length;
        int newCapacity = oldCapacity + (oldCapacity >> 1);
        if (newCapacity - minCapacity < 0)
            newCapacity = minCapacity;
        if (newCapacity - MAX_ARRAY_SIZE > 0)
            newCapacity = hugeCapacity(minCapacity);
        // minCapacity is usually close to size, so this is a win:
        elementData = Arrays.copyOf(elementData, newCapacity);
    }


                                                

## [](#动手实现ArrayList "#动手实现ArrayList")动手实现ArrayList

由于代码过长，故不在此处一一贴出来，感兴趣的小伙伴可以到我的github查看\[github\]: <a href="https://link.juejin.cn?target=https%3A%2F%2Fgithub.com%2FhaifeiWu%2Finterview-collect%2Ftree%2Fmaster%2Fsrc%2Fmain%2Fjava%2Fcom%2Fhaifeiwu%2Finterview%2Fstructure%2Flist" target="_blank" data-ref="nofollow noopener noreferrer" title="https://github.com/haifeiWu/interview-collect/tree/master/src/main/java/com/haifeiwu/interview/structure/list">github.com/haifeiWu/in…</a>

## [](#小结 "#小结")小结

关于ArrayList的源码，给出几点比较重要的总结：

1、注意其三个不同的构造方法。无参构造方法构造的ArrayList的容量默认为10，带有Collection参数的构造方法，将Collection转化为数组赋给ArrayList的实现数组elementData。

2、注意扩充容量的方法ensureCapacity。ArrayList在每次增加元素（可能是1个，也可能是一组）时，都要调用该方法来确保足够的容量。当容量不足以容纳当前的元素个数时，就设置新的容量为旧的容量的1.5倍，如果设置后的新容量还不够，则直接新容量设置为传入的参数（也就是所需的容量），而后用Arrays.copyof()方法将元素拷贝到新的数组（见下面的第3点）。从中可以看出，当容量不够时，每次增加元素，都要将原来的元素拷贝到一个新的数组中，非常耗时，所以建议在事先能确定元素数量的情况下，使用ArrayList

3、ArrayList的实现中大量地调用了Arrays.copyof()和System.arraycopy()方法。我们有必扒一下这两个方法的代码实现。

                                                    
    public static <T> T[] copyOf(T[] original, int newLength) {
           return (T[]) copyOf(original, newLength, original.getClass());
       }


                                                

很明显调用了另一个copyof方法，该方法有三个参数，最后一个参数指明要转换的数据的类型，其源码如下：

                                                    

    public static <T,U> T[] copyOf(U[] original, int newLength, Class<? extends T[]> newType) {
        @SuppressWarnings("unchecked")
        T[] copy = ((Object)newType == (Object)Object[].class)
            ? (T[]) new Object[newLength]
            : (T[]) Array.newInstance(newType.getComponentType(), newLength);
        System.arraycopy(original, 0, copy, 0,
                         Math.min(original.length, newLength));
        return copy;
    }


                                                

从代码里面可以看出，copyOf方法实际上是在其内部又创建了一个长度为newlength的数组，然后调用System.arraycopy()方法，将原来数组中的元素复制到了新的数组中。\
下面来看System.arraycopy()方法。该方法被标记了native，调用了系统的C/C++代码，在JDK中是看不到的，在这里就不再做更深入的了解，不过按照JDK的一贯做法，使用系统的C/C++代码来复制数组效率上来说肯定是没问题的。

4、ArrayList基于数组实现，可以通过下标索引直接查找到指定位置的元素，因此查找效率高，但每次插入或删除元素，就要大量地移动元素，插入删除元素的效率低。

5、在查找给定元素索引值等的方法中，源码都将该元素的值分为null和不为null两种情况处理，因此看来，ArrayList中是允许元素为null。
