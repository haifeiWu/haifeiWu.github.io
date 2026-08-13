---
categories: ["Java"]
title: "Pika 性能优化"
date: "2019-01-09T00:00:00+08:00"
tags: ["Redis", "存储", "性能优化"]
summary: "最近在迁移线上 Redis 到 Pika 的过程中，因为业务需要，需要对项目中原有对 pika 读取操作的代码进行优化，最后结果就是读取百万级的数据由原来的 30 降低到 10分钟左右。Pika 是什么 Pika 是 DBA 需求，基础架构组开发"
---

> 📌 本文原发布于代码星冰乐：[Pika 性能优化](https://changhuin.github.io/article/2019/5b7c/)

最近在迁移线上 Redis 到 Pika 的过程中，因为业务需要，需要对项目中原有的对 pika 读取操作的代码进行优化，最后结果就是读取百万级的数据由原来的 30 分钟降低到 10 分钟左右。\

## Pika 是什么

Pika 是应 DBA 需求，由基础架构组开发的大容量、高性能、持久化、支持多数据结构的类 Redis 存储系统，目前已经开源，最新版本为 Pika 2.2。它所使用的 nemo 引擎本质上是对 Rocksdb 的改造和封装，使其支持多数据结构的存储，并在 nemo 引擎之上封装 Redis 接口，使其完全支持 Redis 协议。Pika 兼容 string、hash、list、zset、set 等多数据结构，使用磁盘而非内存存储数据解决了 Redis 由于存储数据量巨大而导致内存不够用的容量瓶颈。这段话摘自官网，感兴趣的小伙伴请移步 <a href="https://github.com/Qihoo360/pika" target="_blank" rel="noopener">pika</a>

## 为什么要进行优化

因为慢啊……，主要原因是单线程的 Redis 是基于内存的，即便是单线程性能也是相当强悍的。Pika 的话是基于磁盘的，相对来说就有点先天不足了，所以多线程访问才能真正发挥它的性能。

## 具体操作伪代码

业务场景：用户信息以 Hash 的形式存放在 Pika 中，需要根据 Hash 的 Key 获取用户信息，并将用户信息写入文件，数据量在百万级。

### 方案一

将数据分批，然后将分好批的数据分配给创建的线程，执行获取用户信息，并写入文件的逻辑。下面只是大概的业务逻辑，\

    public class Test {
        public void businessService() {
                ExecutorService executor = Executors.newFixedThreadPool(10);
                for (int i = 0;i < 100; i++) {
                    executor.submit(new Task());
                }
                executor.shutdown();
                try {
                    // 等待所有线程
                    boolean loop;
                    do {
                        loop = !executor.awaitTermination(2, TimeUnit.SECONDS);
                    } while(loop);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
                System.out.println("mina thread is over");
            }
        
            /**
             * 要执行的业务逻辑
             */
            class Task implements Runnable {
        
                @Override
                public void run() {
                    // getDataFromPika();
                    // writeDataToFile();
                }
            }
    }

### 方案二

将数据读取到阻塞队列中（ArrayBlockingQueue），然后多线程从 ArrayBlockingQueue 中读取数据，写入文件中。线程结束的逻辑就是在队列中读取到特定字符，结束线程。下面是大概的业务逻辑。\

    public class Test {
        private ArrayBlockingQueue<String> queue = new ArrayBlockingQueue<>(1000);
        
        public void businessService() {
            
            // 读取数据，放入到队列中
            while (true) {
                queue.put("data");
            } 
            ExecutorService executor = Executors.newFixedThreadPool(10);
            // 创建线程
            for (int i = 0;i < 100; i++) {
                executor.submit(new Task());
            }
            
            for (int i = 0;i < 100; i++) {
                queue.put("STOP");
            }
            
            executor.shutdown();
        }
        
        /**
         * 要执行的业务逻辑
         */
        class Task implements Runnable {

            @Override
            public void run() {
                while (true) {
                    // getDataFromPika();
                    // writeDataToFile();
                    if (queue.take() == "STOP") {
                        break;
                    }
                }
                
            }
        }
    }

## 小结

在优化代码时踩了不少坑，原因还是在于自己不够细心，程序员敲代码这活还是比较细的，稍不留意，被自己坑半天。

