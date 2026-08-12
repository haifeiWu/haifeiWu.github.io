---
aliases: ["/zh-cn/posts/arrayblockingqueue--zu-se-dui-lie/"]
categories: ["Java"]
title: "ArrayBlockingQueue 阻塞队列"
date: "2019-01-27T00:00:00+08:00"
tags: ["阻塞队列", "Java", "源码", "并发"]
summary: "一直都在写业务代码，对于 jdk 底层的代码难免有些疏忽，所以决定把一些比较重要的源码过一遍……是什么？ArrayBlockingQueue 是一个用数组实现的有界阻塞队列。此队列按照先进先出（FIFO）的原则对元素进行排序。默认情况"
translationKey: "arrayblockingqueue--zu-se-dui-lie"
---

> 📌 本文原发布于代码星冰乐：[ArrayBlockingQueue 阻塞队列](https://changhuin.github.io/article/2019/bf19/)

一直都在写业务代码，对于 `jdk` 底层的代码难免有些疏忽，所以决定把一些比较重要的源码过一遍……\

## 是什么？

`ArrayBlockingQueue` 是一个用数组实现的有界阻塞队列。此队列按照先进先出（FIFO）的原则对元素进行排序。默认情况下不保证访问者公平地访问队列，所谓公平访问队列是指阻塞的所有生产者线程或消费者线程，当队列可用时，可以按照阻塞的先后顺序访问队列，即先阻塞的生产者线程，可以先往队列里插入元素，先阻塞的消费者线程，可以先从队列里获取元素。通常情况下为了保证公平性会降低吞吐量。

## 主要源码实现

`ArrayBlockingQueue` 基于数组，代码相对简单，下面是主要的代码实现。

### 主要常量

    /** 队列元素数组 */
    final Object[] items;

    /** 队列头部元素的索引位置 */
    int takeIndex;

    /** 队列尾部元素的索引位置 */
    int putIndex;

    /** 记录当前队列的元素个数 */
    int count;

    /*
     * 控制队列的锁
     */

    /** Main lock guarding all access */
    final ReentrantLock lock;

    /** Condition for waiting takes */
    private final Condition notEmpty;

    /** Condition for waiting puts */
    private final Condition notFull;

### 主要方法

      /**
       * 入队，当锁阻塞线程时，要释放锁。
       */
      private void enqueue(E x) {
          // assert lock.getHoldCount() == 1;
          // assert items[putIndex] == null;
          final Object[] items = this.items;
          items[putIndex] = x;
          if (++putIndex == items.length)
              putIndex = 0;
          count++;
          notEmpty.signal();
      }

      /**
       * 将当前元素出队，并释放锁
       */
      private E dequeue() {
          // assert lock.getHoldCount() == 1;
          // assert items[takeIndex] != null;
          final Object[] items = this.items;
          @SuppressWarnings("unchecked")
          E x = (E) items[takeIndex];
          items[takeIndex] = null;
          if (++takeIndex == items.length)
              takeIndex = 0;
          count--;
          if (itrs != null)
              itrs.elementDequeued();
          notFull.signal();
          return x;
      }
      
      /**
       * 移除当前索引所指定的元素
       */
      void removeAt(final int removeIndex) {
          // assert lock.getHoldCount() == 1;
          // assert items[removeIndex] != null;
          // assert removeIndex >= 0 && removeIndex < items.length;
          final Object[] items = this.items;
          // 若当前移除的元素是队尾元素则直接移除
          if (removeIndex == takeIndex) {
              // removing front item; just advance
              items[takeIndex] = null;
              if (++takeIndex == items.length)
                  takeIndex = 0;
              count--;
              if (itrs != null)
                  itrs.elementDequeued();
          } else {
              // 否则通过迭代器来移除元素，防止触发 ConcurrentModifyException 的异常
              // an "interior" remove

              // slide over all others up through putIndex.
              final int putIndex = this.putIndex;
              for (int i = removeIndex;;) {
                  int next = i + 1;
                  if (next == items.length)
                      next = 0;
                  if (next != putIndex) {
                      items[i] = items[next];
                      i = next;
                  } else {
                      items[i] = null;
                      this.putIndex = i;
                      break;
                  }
              }
              count--;
              if (itrs != null)
                  itrs.removedAt(removeIndex);
          }
          // 释放锁
          notFull.signal();
      }
      
    /**
    * 加锁的入队方法。
    */
    public void put(E e) throws InterruptedException {
          // 判空
          checkNotNull(e);
          // 获取可重入锁
          final ReentrantLock lock = this.lock;
          // 加锁，但是该锁可被中断
          lock.lockInterruptibly();
          try {
              while (count == items.length)
                  // 若队列满，则等待
                  notFull.await();
              // 入队
              enqueue(e);
          } finally {
              // 释放锁
              lock.unlock();
          }
      }
      
      /**
       * 出队列
      */
      public E take() throws InterruptedException {
          final ReentrantLock lock = this.lock;
          // 加锁，但是该锁可被中断
          lock.lockInterruptibly();
          try {
              while (count == 0)
                  // 当队列为空时，等待
                  notEmpty.await();
              return dequeue();
          } finally {
              // 释放锁
              lock.unlock();
          }
      }

## 基于 `ArrayBlockingQueue` 实现的生产者-消费者模型

生产者消费者模式是通过一个容器来解决生产者和消费者的强耦合问题。生产者和消费者彼此之间不直接通讯，而通过阻塞队列来通讯，所以生产者生产完数据之后不用等待消费者处理，直接扔给阻塞队列，消费者不找生产者要数据，而是直接从阻塞队列里取，阻塞队列就相当于一个缓冲区，平衡了生产者和消费者的处理能力。

    public static void main(String[] args) {
        final ArrayBlockingQueue<String> container = new ArrayBlockingQueue<>(10);

        final int[] producerCount = {0};
        new Thread(() -> {
            while (true) {
                try {
                    System.out.println("我生产了一个 : " + producerCount[0]++);
                    container.put(producerCount[0] + "");
                    Thread.sleep(1000);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
            }
        }).start();

        new Thread(() -> {
            while (true) {
                try {
                    System.out.println("我消费了一个 : " + container.take());
                    Thread.sleep(3000);
                }
                catch (InterruptedException e) {
                    e.printStackTrace();
                }
            }
        }).start();
    }

## 小结

精诚所至，金石为开……

