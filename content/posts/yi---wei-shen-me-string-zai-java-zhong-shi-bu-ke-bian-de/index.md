---
categories: ["Java"]
title: "[译] 为什么 String 在 Java 中是不可变的"
date: "2019-07-08T00:00:00+08:00"
tags: ["Java", "JVM", "源码"]
summary: "String 在 Java 中是不可变的。不可变类只是一个无法修改其实例的类。创建实例时，将初始化实例中的所有信息，并且无法修改信息。不可变类有许多优点。本文总结了为什么 String 设计为不可变的。这篇文章从内存，同步和数据结"
translationKey: "yi---wei-shen-me-string-zai-java-zhong-shi-bu-ke-bian-de"
---

> 📌 本文原发布于代码星冰乐：[[译] 为什么 String 在 Java 中是不可变的](https://changhuin.github.io/article/2019/496a/)

String 在 Java 中是不可变的。不可变类只是一个无法修改其实例的类。创建实例时，将初始化实例中的所有信息，并且无法修改信息。不可变类有许多优点。本文总结了<a href="https://www.programcreek.com/2009/02/diagram-to-show-java-strings-immutability/" target="_blank" rel="noopener">为什么 String 设计为不可变的</a>。这篇文章从内存，同步和数据结构的角度说明了不变性概念。

## 1. 字符串池

字符串池（String intern pool）是方法区中的特殊存储区域。当创建字符串并且池中已存在该字符串时，将返回现有字符串的引用，而不是创建新对象。

以下代码将在堆中仅创建一个字符串对象。

    String string1 = "abcd";
    String string2 = "abcd";

如下图所示：
> 📷 图注：字符串池

如果字符串是可变的，则使用一个引用更改字符串将导致其他引用出错。

## 2. 缓存的哈希码

字符串的哈希码经常在 Java 中使用。例如，在 HashMap 或 HashSet 中。不可变性保证哈希码总是相同的，这样它就可以被缓存起来而不用担心变化。这意味着，每次使用时都不需要计算哈希码。这更有效率。

在 String 类中，它具有如下代码：

    private int hash;//this is used to cache hash code.

## 3. 其他对象中的字符串

具体来说，请参考以下程序：

    HashSet<String> set = new HashSet<String>();
    set.add(new String("a"));
    set.add(new String("b"));
    set.add(new String("c"));
     
    for(String a: set)
        a.value = "a";

在此示例中，如果 String 是可变的，则可以更改其值，这将违反 set 的设计（set 包含非重复元素）。当然，上面的示例仅用于演示目的，并且实际字符串类中没有值字段。

## 4. 安全

String 被广泛用作许多 Java 类的参数，例如 网络连接，打开文件等。如果字符串不是不可变的，连接或文件将被更改，这可能会导致严重的安全威胁。该方法认为它连接到一台机器，但事实并非如此。可变字符串也可能在 Reflection 中引起安全问题，因为参数是字符串。

如下例子：

    boolean connect(string s){
        if (!isSecure(s)) { 
    throw new SecurityException(); 
    }
        //here will cause problem, if s is changed before this by using other references.    
        causeProblem(s);
    }

## 5. 不可变保证了线程安全

由于无法更改不可变对象，因此可以在多个线程之间自由共享它们。这消除了同步的要求。

综上所述，出于效率和安全原因，String 被设计为不可变的，这也是在一般情况下优选不可变类的原因。

