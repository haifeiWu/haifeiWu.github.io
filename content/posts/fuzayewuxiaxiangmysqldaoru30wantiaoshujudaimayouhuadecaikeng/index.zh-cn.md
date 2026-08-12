---
title: "复杂业务下向Mysql导入30万条数据代码优化的踩坑记录"
date: "2018-04-23T21:37:17+08:00"
tags: ["MySQL", "SQL", "后端", "数据库"]
categories: ["后端"]
summary: "另外，在information_schema下面有三张表:INNODB_TRX、INNODB_LOCKS、INNODB_LOCK_WAITS（解决问题方法），通过这三张表，可以更简单地监控当前的事务并分析可能存在的问题。 kill 进程ID，发生上面错误的根本原因在业务逻辑代码…"
translationKey: "fuzayewuxiaxiangmysqldaoru30wantiaoshujudaimayouhuadecaikeng"
---

{{< include-post "content/posts/fuzayewuxiaxiangmysqldaoru30wantiaoshujudaimayouhuadecaikeng/index.md" >}}
