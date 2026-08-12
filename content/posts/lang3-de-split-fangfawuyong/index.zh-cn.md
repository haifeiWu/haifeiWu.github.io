---
title: "lang3 的 split 方法误用"
date: "2019-08-07T13:53:17+08:00"
tags: ["Java"]
categories: ["后端"]
summary: "apache 的 lang3 是我们开发常用到的三方工具包，然而对这个包不甚了解的话，会产生莫名其秒的 bug，在这里做下记录。通过分析字符串的拆分结果，发现该方法并不是将分隔符去截取字符串，而是将分隔符的每一个字符都当成分隔符去截取字符串，当我们的分隔符是一个字符的时候一…"
translationKey: "lang3-de-split-fangfawuyong"
---

{{< include-post "content/posts/lang3-de-split-fangfawuyong/index.md" >}}
