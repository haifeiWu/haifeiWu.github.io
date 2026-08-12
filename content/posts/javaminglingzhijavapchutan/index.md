---
categories: ["后端"]
title: "Java命令之javap初探"
date: "2018-02-26T13:27:15+08:00"
tags: ["Java", "后端", "JVM", "编译器"]
summary: "下面列举javap命令的常用options及其功能描述，更多功能的使用请自行Google，楼主不做赘述。 javap命令分解一个class文件，它根据options来决定到底输出什么。如果没有使用options,那么javap将会输出该class文件中的包，类里的protect…"
---

> 📌 本文原发布于掘金社区：[Java命令之javap初探](https://juejin.cn/post/6844903566906228750)

<a href="https://link.juejin.cn?target=http%3A%2F%2Fblog.csdn.net%2Fgithub_36379934%2Farticle%2Fdetails%2F79375883" target="_blank" data-ref="nofollow noopener noreferrer" title="http://blog.csdn.net/github_36379934/article/details/79375883">原博客地址</a>

> javap是jdk自带的一个工具在jdk安装目录的/bin下面可以找到，可以对代码反编译，也可以查看java编译器生成的字节码，对代码的执行过程进行分析，了解jvm内部的工作。

下面列举javap命令的常用options及其功能描述，更多功能的使用请自行Google，楼主不做赘述。

### 用法摘要

``` bash
-help 帮助
-l 输出行和变量的表
-public 只输出public方法和域
-protected 只输出public和protected类和成员
-package 只输出包，public和protected类和成员，这是默认的
-p -private 输出所有类和成员
-s 输出内部类型签名
-c 输出分解后的代码，例如，类中每一个方法内，包含java字节码的指令，
-verbose 输出栈大小，方法参数的个数
-constants 输出静态final常量
```

### 实例分析

javap命令分解一个class文件，它根据options来决定到底输出什么。如果没有使用options,那么javap将会输出该class文件中的包，类里的protected和public域以及类里的所有方法。javap将会把它们输出在标准输出上。来看这个例子，先编译(javac)下面这个类。

``` bash
package com.thundersoft.metadata.test.kafka;

import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.clients.consumer.ConsumerRecords;
import org.apache.kafka.clients.consumer.KafkaConsumer;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.Producer;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.junit.Test;

import java.util.Arrays;
import java.util.Properties;

public class KafkaTest {

    @Test
    public void testProducer() {
        Properties props = new Properties();
        props.put("bootstrap.servers", "192.168.204.30:9092");
        props.put("acks", "all");
        props.put("retries", 0);
        props.put("batch.size", 16384);
        props.put("linger.ms", 1);
        props.put("buffer.memory", 33554432);
        props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");

        Producer<String, String> producer = new KafkaProducer<>(props);
        for(int i = 0; i < 100; i++) {
            producer.send(new ProducerRecord<String, String>("my-topic", Integer.toString(i), Integer.toString(i)));
        }

        producer.close();
    }

    @Test
    public void testKafkaConsumer() {
        Properties props = new Properties();
        props.put("bootstrap.servers", "192.168.204.30:9092");
        props.put("group.id", "test");
        props.put("enable.auto.commit", "true");
        props.put("auto.commit.interval.ms", "1000");
        props.put("key.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
        props.put("value.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
        KafkaConsumer<String, String> consumer = new KafkaConsumer<>(props);
        consumer.subscribe(Arrays.asList("my-topic"));

        while (true) {
            ConsumerRecords<String, String> records = consumer.poll(100);
            for (ConsumerRecord<String, String> record : records)
                System.out.printf("offset = %s, key = %s, value = %s%n", record.topic(), record.key(), record.value());
        }
    }

    public static void main(String[] args) {
        int a = 2;
        int b = 3;
        int sum = a*b;
        System.out.println(sum);
    }

}
```

在命令行上键入javap KafkaTest后，输出结果如下

``` bash
public class com.thundersoft.metadata.test.kafka.KafkaTest {
  public com.thundersoft.metadata.test.kafka.KafkaTest();
  public void testProducer();
  public void testKafkaConsumer();
  public static void main(java.lang.String[]);
}
```

#### 结合代码分析编译器执行过程

这里只关注main方法内部的代码逻辑，main方法代码如下

``` bash
 public static void main(String[] args) {
        int a = 2;
        int b = 3;
        int sum = a*b;
        System.out.println(sum);
    }
```

在命令行上键入javap -c KafkaTest后，输出结果如下

``` bash
 public static void main(java.lang.String[]);
    Code:
       0: iconst_2
       1: istore_1
       2: iconst_3
       3: istore_2
       4: iload_1
       5: iload_2
       6: imul
       7: istore_3
       8: getstatic     #47                 // Field java/lang/System.out:Ljava/io/PrintStream;
      11: iload_3
      12: invokevirtual #54                 // Method java/io/PrintStream.println:(I)V
      15: return
```

如上面代码所，iconst_2 与iconst_3分别代表常量2，3 。istore_1 ，istore_2 分别代表定义两个普通变量，iload_1 ， iload_2 分别表示加载istore_1，istore_2 两个变量到数据栈中，imul表示两个变量做乘法运算，结果赋值给变量istore_3，最后将结果输出，程序返回。

在分析这段简单代码的过程中，楼主发现了一个jvm编译命令的网站，分享出来<a href="https://link.juejin.cn?target=https%3A%2F%2Fcs.au.dk%2F~mis%2FdOvs%2Fjvmspec%2Fref-Java.html" target="_blank" data-ref="nofollow noopener noreferrer" title="https://cs.au.dk/~mis/dOvs/jvmspec/ref-Java.html">jvm指令</a>。

### 总结

楼主在上面做了一个简单的代码分析的过程，希望可以帮助到有缘人。javap可以用于反编译和查看编译器编译后的字节码。一般用到的不多，不过平时用javap -c比较多，该命令用于列出每个方法所执行的JVM指令，用来解决比较棘手的逻辑出错的bug是个不错的选择。另外通过字节码和源代码的对比，深入分析java的编译原理及代码执行过程，解决各种Java原理级别的问题。
