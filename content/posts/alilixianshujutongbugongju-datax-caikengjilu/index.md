---
categories: ["后端"]
title: "阿里离线数据同步工具 DataX 踩坑记录"
date: "2018-07-04T22:33:38+08:00"
tags: ["后端", "Java", "阿里巴巴", "MySQL", "Oracle"]
summary: "最近在做一些数据迁移相关工作，调研了一些工具，发现DataX是个不错的东西，所以安利给大家。那么DataX是什么呢？ DataX 是阿里巴巴集团内被广泛使用的离线数据同步工具，实现包括 MySQL、SQL Server、Oracle、PostgreSQL 等各种异构数据源的同步"
---

> 📌 本文原发布于掘金社区：[阿里离线数据同步工具 DataX 踩坑记录](https://juejin.cn/post/6844903633545330702)

最近在做一些数据迁移相关工作，调研了一些工具，发现DataX是个不错的东西，所以安利给大家。那么DataX是什么呢？ DataX 是阿里巴巴集团内被广泛使用的离线数据同步工具，实现包括 MySQL、SQL Server、Oracle、PostgreSQL 等各种异构数据源之间高效的数据同步功能。\
<span id="user-content-more"></span>

## [](#主要功能 "#主要功能")主要功能

DataX本身作为数据同步框架，将不同数据源的同步抽象为从源头数据源读取数据的Reader插件，以及向目标端写入数据的Writer插件，理论上DataX框架可以支持任意数据源类型的数据同步工作。同时DataX插件体系作为一套生态系统, 每接入一套新数据源该新加入的数据源即可实现和现有的数据源互通。具体介绍请移步<a href="https://link.juejin.cn?target=https%3A%2F%2Fgithub.com%2Falibaba%2FDataX%2Fblob%2Fmaster%2Fintroduction.md" target="_blank" data-ref="nofollow noopener noreferrer" title="https://github.com/alibaba/DataX/blob/master/introduction.md">DataX介绍</a>

## [](#系统要求 "#系统要求")系统要求

- Linux
- JDK(1.8以上，推荐1.8)
- Python(推荐Python2.6.X)
- Apache Maven 3.x (Compile DataX)
- 设置jvm堆内存，堆内存要求大于1g，否则会出现启动不了的情况

<!-- -->

    export JAVA_OPTS= -Xms1024m -Xmx1024m

## [](#快速开始 "#快速开始")快速开始

### [](#部署DataX "#部署DataX")部署DataX

- 方法一、直接下载DataX工具包：<a href="https://link.juejin.cn?target=http%3A%2F%2Fdatax-opensource.oss-cn-hangzhou.aliyuncs.com%2Fdatax.tar.gz" target="_blank" data-ref="nofollow noopener noreferrer" title="http://datax-opensource.oss-cn-hangzhou.aliyuncs.com/datax.tar.gz">DataX下载地址</a>

下载后解压至本地某个目录，进入bin目录，即可运行同步作业：\

    $ cd  {YOUR_DATAX_HOME}/bin    
    $ python datax.py {YOUR_JOB.json}

- 方法二、下载DataX源码，自己编译：<a href="https://link.juejin.cn?target=https%3A%2F%2Fgithub.com%2Falibaba%2FDataX" target="_blank" data-ref="nofollow noopener noreferrer" title="https://github.com/alibaba/DataX">DataX源码</a>\
  (1)、下载DataX源码：

      $ git clone git@github.com:alibaba/DataX.git

  (2)、通过maven打包：

      $ cd  {DataX_source_code_home}
      $ mvn -U clean package assembly:assembly -Dmaven.test.skip=true

  打包成功，日志显示如下：

      [INFO] BUILD SUCCESS
      [INFO] -----------------------------------------------------------------
      [INFO] Total time: 08:12 min
      [INFO] Finished at: 2018-06-05T16:26:48+08:00
      [INFO] Final Memory: 133M/960M
      [INFO] -----------------------------------------------------------------

打包成功后的DataX包位于 {DataX_source_code_home}/target/datax/datax/ ,

### [](#生成配置文件 "#生成配置文件")生成配置文件

- 第一步、创建配置文件（json格式）

  可以通过命令生成配置模板：

      python datax.py -r oraclereader -w mysqlwriter > oracle2mysql2.json

  在 {DataX_source_code_home} 目录下的 plugin 目录下有DataX支持的所有reader与writer\
  通过命令生成的配置模板如下所示，楼主生成的reader与writer是对应的是从oracle读取数据，向mysql写数据。

      {
      "job": {
          "content": [{
              "reader": {
                  "name": "oraclereader",
                  "parameter": {
                      "column": ["*"],
                      "connection": [{
                          "jdbcUrl": ["*"],
                          "table": ["tb1"]
                      }],
                      "password": "***",
                      "username": "***"
                  }
              },
              "writer": {
                  "name": "mysqlwriter",
                  "parameter": {
                      "column": ["*"],
                      "connection": [{
                          "jdbcUrl": "*",
                          "table": ["tb1"]
                      }],
                      "password": "**",
                      "preSql": [],
                      "session": [],
                      "username": "**",
                      "writeMode": "insert"
                  }
              }
          }],
          "setting": {
              "speed": {
                  "channel": "3"
              }
          }
      }
      }

- 最后：启动DataX

      $ cd {YOUR_DATAX_DIR_BIN}
      $ python datax.py ./oracle2mysql2.json

- 同步结束，显示日志如下：

      ...
      2018-06-05 11:20:25.263 [job-0] INFO  JobContainer - 
      任务启动时刻                    : 2018-06-05 11:20:15
      任务结束时刻                    : 2018-06-05 11:20:25
      任务总计耗时                    :                 10s
      任务平均流量                    :              205B/s
      记录写入速度                    :              5rec/s
      读出记录总数                    :                  50
      读写失败总数                    :                   0

## [](#小结 "#小结")小结

相对来说DataX上手使用起来还是比较容易的，但是令楼主比较犯难就是不能在同一个配置文件里面同时写入不同的数据库的表，要想读取多张表并写入就只能单独配置。但是也解决了楼主一些问题。

作 者：haifeiWu原文链接：<a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2018%2F4928%2Farticle%2F2018%2F4928%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/article/2018/4928/article/2018/4928/">www.hchstudio.cn/article/201…</a>版权声明：非特殊声明均为本站原创作品，转载时请注明作者和原文链接。
