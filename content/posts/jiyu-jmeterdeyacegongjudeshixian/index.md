---
categories: ["后端"]
title: "基于 JMeter的压测工具的实现"
date: "2017-11-05T19:54:39+08:00"
tags: ["JMeter", "后端", "算法"]
summary: "在界面中选择对应的选项卡：（目前只支持HTTP模板，自定义脚本上传，测试相应结果两个选项卡），HTTP模板是根据页面选择的参数生成jmx文件，自定义脚本是用户直接上传jmx脚本。 下图是执行脚本的页面，在页面中可以选择在本地执行与在远程机执行（远程机执行是指在3台机器上同步执行…"
---

> 📌 本文原发布于掘金社区：[基于 JMeter的压测工具的实现](https://juejin.cn/post/6844903508706082824)

# JMeter Web化

<a href="https://link.juejin.cn?target=https%3A%2F%2Fgithub.com%2FhaifeiWu%2FYOUSONG%2Fblob%2Fmaster%2F%25E4%25BB%25A3%25E7%25A0%2581%25E8%25AF%25B4%25E6%2598%258E%25E6%2596%2587%25E6%25A1%25A3.md" target="_blank" data-ref="nofollow noopener noreferrer" title="https://github.com/haifeiWu/YOUSONG/blob/master/%E4%BB%A3%E7%A0%81%E8%AF%B4%E6%98%8E%E6%96%87%E6%A1%A3.md">代码说明文档</a>\
<a href="https://link.juejin.cn?target=https%3A%2F%2Fgithub.com%2FhaifeiWu%2FYOUSONG%2Fblob%2Fmaster%2FJmeter%2520Web%25E9%25A1%25B9%25E7%259B%25AE%25E4%25BD%25BF%25E7%2594%25A8%25E6%258C%2587%25E5%258D%2597.md" target="_blank" data-ref="nofollow noopener noreferrer" title="https://github.com/haifeiWu/YOUSONG/blob/master/Jmeter%20Web%E9%A1%B9%E7%9B%AE%E4%BD%BF%E7%94%A8%E6%8C%87%E5%8D%97.md">JMeter WEB项目使用说明文档</a>

# JMeter Web项目使用指南

- 项目的内网访问地址：<a href="https://link.juejin.cn?target=http%3A%2F%2F10.2.250.202%3A9099%2FJmeterWEB%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://10.2.250.202:9099/JmeterWEB/">http://10.2.250.202:9099/JmeterWEB/</a>

- 打开链接你会看到，如下界面（请大家尽量使用chrome浏览器）： <img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2017/11/5/483c3e82f49c0d6062af8068b7cfbeec~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp#?w=1312&amp;h=768&amp;s=223735&amp;e=png&amp;b=fbfbfb" loading="lazy" alt="image" />

- 在界面中选择对应的选项卡：（目前只支持HTTP模板，自定义脚本上传，测试相应结果两个选项卡），HTTP模板是根据页面选择的参数生成jmx文件，自定义脚本是用户直接上传jmx脚本。

- 下图是执行脚本的页面，在页面中可以选择在本地执行与在远程机执行（远程机执行是指在3台机器上同步执行脚本，比如你的脚本是10个线程，选择两台远程机与加上本机就相当于执行30个线程）。其他两台远程机器的IP是10.2.250.203:1099，10.2.250.204:1099。 <img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2017/11/5/fea4ead27127bc0fb8cb55812abc9ed0~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp#?w=1299&amp;h=680&amp;s=66982&amp;e=png&amp;b=fefefe" loading="lazy" alt="image" />

- 生成的测试报告如下图所示。 <img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2017/11/5/d4ae901fd6ced49a78b49bd528c70101~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp#?w=1301&amp;h=678&amp;s=100016&amp;e=png&amp;b=f9f9f9" loading="lazy" alt="image" />

- 查看Response，request的数据 <img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2017/11/5/09bd7e1e54fcdde712d20f1fb7fa4681~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp#?w=1305&amp;h=679&amp;s=84571&amp;e=png&amp;b=e6eef5" loading="lazy" alt="image" />

- JMeter3.0提供一个用于生成HTML页面格式图形化报告的扩展模块。该模块支持通过两种方式生成多维度图形化测试报告：在JMeter性能测试结束时，自动生成本次测试的HTML图形化报告使用一个已有的结果文件(如CSV文件)来生成该次结果的HTML图形化报告 其默认提供的度量维度包括：

1.  APDEX(Application Performance Index)指数

2.  聚合报告\
    类似于UI上的Aggregate Report

3.  Errors报告\
    展示不同错误类型的数量以及百分比

4.  响应时间变化曲线 展示平均响应时间随时间变化情况\
    类似于JMeter Plugins在UI上的jp@gc - Response Times Over Time

5.  数据吞吐量时间曲线\
    展示每秒数据吞吐量随时间变化的情况 类似于JMeter Plugins在UI上的jp@gc - Bytes Throughput Over Time

6.  Latency time变化曲线\
    展示Latency time随时间变化的情况\
    类似于JMeter Plugins在UI上的jp@gc - Response Latencies Over Time

7.  每秒点击数曲线\
    类似于JMeter Plugins在UI上的jp@gc - Hits per Second

8.  HTTP状态码时间分布曲线\
    展示响应状态码随时间的分布情况\
    类似于JMeter Plugins在UI上的jp@gc - Response Codes per Second

9.  事务吞吐量时间曲线(TPS)

10. 展示每秒处理的事务数随时间变化情况\
    类似于JMeter Plugins在UI上的jp@gc - Transactions per Second

11. 平均响应时间与每秒请求数的关系图\
    展示平均响应时间与每秒请求数(可以理解为QPS)的关系

12. Latency time与每秒请求数的关系图\
    展示Latency time与每秒请求数的关系

13. 响应时间百分位图\
    响应时间的百分位分布图

14. 活动线程数变化曲线\
    展示测试过程中活动线程数随时间变化情况

15. 平均响应时间与线程数的关系图\
    展示平均响应时间与线程数的关系 类似于JMeter Plugins在UI上的jp@gc - Response Times vs Threads

16. 柱状响应时间分布图\
    展示落在各个平均响应时间区间的请求数情况
