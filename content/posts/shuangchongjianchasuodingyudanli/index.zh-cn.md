---
title: "双重检查锁定与单例"
date: "2019-11-13T14:47:53+08:00"
tags: ["Java", "设计模式"]
categories: ["后端"]
summary: "对于单例模式，相信大多数人都可以写出好几种实现方法，懒汉，饿汉等等，然而小小单例真要写好，写的完全正确也并非易事。下面是我们经常使用的一种单例的实现，也就是双重检查所的实现方案。让我们来看一下这个代码是如何工作的：首先当一个线程发出请求后，会先检查 instance 是否为 nu…"
translationKey: "shuangchongjianchasuodingyudanli"
---

{{< include-post "content/posts/shuangchongjianchasuodingyudanli/index.md" >}}
