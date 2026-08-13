---
categories: ["Java"]
title: "LRU 算法"
date: "2019-06-29T00:00:00+08:00"
tags: ["缓存", "算法", "设计模式"]
summary: "What？LRU 是 Least Recently Used 的缩写，即最近最少使用，是一种常用的页面置换算法，选择最近最久未使用的页面予以淘汰。该算法赋予每个页面一个访问字段，用来记录一个页面自上次被访问以来所经历的时间 t，当须淘汰"
---

> 📌 本文原发布于代码星冰乐：[LRU 算法](https://changhuin.github.io/article/2019/9a45/)

## What？

LRU 是 Least Recently Used 的缩写，即最近最少使用，是一种常用的页面置换算法，选择最近最久未使用的页面予以淘汰。该算法赋予每个页面一个访问字段，用来记录一个页面自上次被访问以来所经历的时间 t，当须淘汰一个页面时，选择现有页面中其 t 值最大的，即最近最久未使用的页面予以淘汰。-百科\
上面是对操作系统中 LRU 算法的阐述，本文说的 LRU 主要是指该算法在业务层缓存算法中的应用，总而言之，基本的实现逻辑是一样的。

## How？

算法思想：

- 1，新数据插入到链表头部。
- 2，每当缓存命中（即缓存数据被访问），则将数据移到链表头部。
- 3，当链表满的时候，将链表尾部的数据丢弃。

### 算法实现

    class Node {
        
        public Node(String key,String value) {
            this.key = key;
            this.value = value;
        }
        
        public Node pre;
        public Node next;
        public String key;
        public String value;
    }

    public class LRUCache {
        private Node head;
        private Node end;
        
        // 缓存上限
        private int limit;
        private HashMap map;
        
        public LRUCache(int limit) {
            this.limit = limit;
            map = new HashMap();
        }
        
        public String get(String key) {
            Node node = map.get(key);
            if(node == null) {
                return null;
            }
            // 调整node到尾部
            refreshNode(node);
            return node.value;
        }
        
        public void put(String key, String value) {
            Node node = map.get(key);
            if(node == null) {
                // key不存在直接插入
                while(map.size() >= limit) {
                    // 去除链表内的节点
                    String oldKey = removeNode(head);
                    // 去除map中的缓存
                    map.remove(oldKey);
                }
                node = new Node(key, value);
                // 链表中加入节点
                addNode(node);
                // map中加入节点
                map.put(key, node);
            } else {
                // 更新节点并调整到尾部
                node.value = value;
                refreshNode(node);
            }
        }
        
        private void refreshNode(Node node) {
            // 如果访问的是尾节点，无须移动节点
            if(node == end) {
                return;
            }
            // 把节点移动到尾部，相当于做一次删除插入操作
            removeNode(node);
            addNode(node);
        }
        
        private String removeNode(Node node) {
            // 尾节点
            if(node == end) {
                end = end.pre;
            } else if(node == head) {
            // 头结点
                head = head.next;
            } else {
                // 中间节点
                node.pre.next = node.next;
                node.next.pre = node.pre;
            }
            return node.key;
        }
        
        private void addNode(Node node) {
            if(end != null) {
                end.next = node;
                node.pre = end;
                node.next = null;
            }
            end = node;
            if(head == null) {
                head = node;
            }
        }
    }

### JDK 中的算法实现

通常不需要我们自己专门实现此算法的数据结构，使用 JDK 内置的 LinkedHashMap 稍加改造即可。\

    public class LRUCache<K, V> extends LinkedHashMap<K, V> {
        private final int MAX_CACHE_SIZE;
     
        public LRUCache2(int cacheSize) {
            super((int) Math.ceil(cacheSize / 0.75) + 1, 0.75f, true);
            MAX_CACHE_SIZE = cacheSize;
        }
     
        @Override
        protected boolean removeEldestEntry(Map.Entry eldest) {
            return size() > MAX_CACHE_SIZE;
        }
    }

## mybatis 中的 LRU 算法实现

    /**
     * 最近最少使用缓存
     * 基于 LinkedHashMap 覆盖其 removeEldestEntry 方法实现。
     */
    public class LruCache implements Cache {

        private final Cache delegate;
        //额外用了一个map才做lru，但是委托的Cache里面其实也是一个map，这样等于用2倍的内存实现lru功能
        private Map<Object, Object> keyMap;
        private Object eldestKey;

        public LruCache(Cache delegate) {
            this.delegate = delegate;
            setSize(1024);
        }

        @Override
        public String getId() {
            return delegate.getId();
        }

        @Override
        public int getSize() {
            return delegate.getSize();
        }

        public void setSize(final int size) {
            keyMap = new LinkedHashMap<Object, Object>(size, .75F, true) {
                private static final long serialVersionUID = 4267176411845948333L;

                // 核心就是覆盖 LinkedHashMap.removeEldestEntry方法,
                // 返回true或false告诉 LinkedHashMap要不要删除此最老键值
                // LinkedHashMap内部其实就是每次访问或者插入一个元素都会把元素放到链表末尾，
                // 这样不经常访问的键值肯定就在链表开头啦
                @Override
                protected boolean removeEldestEntry(Map.Entry<Object, Object> eldest) {
                    boolean tooBig = size() > size;
                    if (tooBig) {
                        // 这里没辙了，把eldestKey存入实例变量
                        eldestKey = eldest.getKey();
                    }
                    return tooBig;
                }
            };
        }

        @Override
        public void putObject(Object key, Object value) {
            delegate.putObject(key, value);
            // 增加新纪录后，判断是否要将最老元素移除
            cycleKeyList(key);
        }

        @Override
        public Object getObject(Object key) {
            // get的时候调用一下LinkedHashMap.get，让经常访问的值移动到链表末尾
            keyMap.get(key); //touch
            return delegate.getObject(key);
        }

        @Override
        public Object removeObject(Object key) {
            return delegate.removeObject(key);
        }

        @Override
        public void clear() {
            delegate.clear();
            keyMap.clear();
        }

        @Override
        public ReadWriteLock getReadWriteLock() {
            return null;
        }

        private void cycleKeyList(Object key) {
            keyMap.put(key, key);
            // keyMap是linkedhashmap，最老的记录已经被移除了，然后这里我们还需要移除被委托的那个cache的记录
            if (eldestKey != null) {
                delegate.removeObject(eldestKey);
                eldestKey = null;
            }
        }

    }

