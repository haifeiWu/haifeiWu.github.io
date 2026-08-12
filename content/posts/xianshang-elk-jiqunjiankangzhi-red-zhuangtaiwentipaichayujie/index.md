---
categories: ["后端"]
title: "线上 ELK 集群健康值 red 状态问题排查与解决"
date: "2018-08-07T12:31:09+08:00"
tags: ["后端", "Elasticsearch", "服务器", "数据分析"]
summary: "之前一直运行正常的数据分析平台，最近一段时间没有注意发现日志索引数据一直未生成，大概持续了 n 多天，当前状态：单台机器，Elasticsearch（下面称 ES）单节点(空集群),1000+shrads, 约 200G 大小。查看 ES 集群健康值，发现 status 为 red，这…"
translationKey: "xianshang-elk-jiqunjiankangzhi-red-zhuangtaiwentipaichayujie"
---

> 📌 本文原发布于掘金社区：[线上 ELK 集群健康值 red 状态问题排查与解决](https://juejin.cn/post/6844903652595875853)

> 原文地址：<a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2F%3F_ref%3Djuejin" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/?_ref=juejin">haifeiWu 的博客</a>\
> 博客地址：<a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2018%2Ff023%2F%3F_ref%3Djuejin" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/article/2018/f023/?_ref=juejin">www.hchstudio.cn</a>\
> 欢迎转载，转载请注明作者及出处，谢谢！

之前一直运行正常的数据分析平台，最近一段时间没有注意到日志索引数据一直未生成，大概持续了 n 多天，当前状态：单台机器，Elasticsearch（下面称 ES）单节点(空集群),1000+ shards, 约 200G 大小。

## 问题排查

### 服务器内存，CPU 状态检查

使用 `top` 查看服务器 `cpu`，内存等占用情况，如下图所示（当时楼主的服务器 ES 应用的 CPU 占用在 90%以上，肯定有问题）

<figure>
<img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/8/7/16512a56d09216c9~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.png" loading="lazy" alt="top" />
<figcaption aria-hidden="true">top</figcaption>
</figure>

内存占用也极高（当时楼主的 8G 内存的服务器仅剩下 150M 左右的空闲，肯定是 ES 的问题）

<figure>
<img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/8/7/16512a56d0810172~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.png" loading="lazy" alt="free" />
<figcaption aria-hidden="true">free</figcaption>
</figure>

### ES 集群状态

查看 ES 集群健康值，发现 `status` 为 `red`，这种状态表示部分主分片不可用，楼主当前的状态是历史数据可查，但是无法生成新的 `index` 数据。

``` bash
curl http://localhost:9200/_cluster/health?pretty

{
  "cluster_name" : "elasticsearch",
  "status" : "red",
  "timed_out" : false,
  "number_of_nodes" : 1,
  "number_of_data_nodes" : 1,
  "active_primary_shards" : 663,
  "active_shards" : 663,
  "relocating_shards" : 0,
  "initializing_shards" : 0,
  "unassigned_shards" : 6,
  "delayed_unassigned_shards" : 0,
  "number_of_pending_tasks" : 0,
  "number_of_in_flight_fetch" : 0,
  "task_max_waiting_in_queue_millis" : 0,
  "active_shards_percent_as_number" : 99.10313901345292
}
```

查看每个索引的状态，发现大部分索引状态是 `red`，处于不可用状态，因为打开的索引数据过多，导致 ES 占用大量的 CPU，内存，使得 `logstash` 不可用，也就无法创建新的索引数据，从而导致数据丢失。

``` bash
curl -XGET   "http://localhost:9200/_cat/indices?v"

health status index          pri rep docs.count docs.deleted store.size pri.store.size
red    open   jr-2016.12.20    3   0
red    open   jr-2016.12.21    3   0
red    open   jr-2016.12.22    3   0
red    open   jr-2016.12.23    3   0
red    open   jr-2016.12.24    3   0
red    open   jr-2016.12.25    3   0
red    open   jr-2016.12.26    3   0
red    open   jr-2016.12.27    3   0
```

### ES 集群分片不可用，导致的查询失败

查询 ES 时抛出的异常：

``` java
[2018-08-06 18:27:24,553][DEBUG][action.search            ] [Godfrey Calthrop] All shards failed for phase: [query]
[jr-2018.08.06][[jr-2018.08.06][2]] NoShardAvailableActionException[null]
    at org.elasticsearch.action.search.AbstractSearchAsyncAction.start(AbstractSearchAsyncAction.java:129)
    at org.elasticsearch.action.search.TransportSearchAction.doExecute(TransportSearchAction.java:115)
    at org.elasticsearch.action.search.TransportSearchAction.doExecute(TransportSearchAction.java:47)
    at org.elasticsearch.action.support.TransportAction.doExecute(TransportAction.java:149)
    at org.elasticsearch.action.support.TransportAction.execute(TransportAction.java:137)
    at org.elasticsearch.action.support.TransportAction.execute(TransportAction.java:85)
    at org.elasticsearch.client.node.NodeClient.doExecute(NodeClient.java:58)
    at org.elasticsearch.client.support.AbstractClient.execute(AbstractClient.java:359)
    at org.elasticsearch.client.FilterClient.doExecute(FilterClient.java:52)
    at org.elasticsearch.rest.BaseRestHandler$HeadersAndContextCopyClient.doExecute(BaseRestHandler.java:83)
    at org.elasticsearch.client.support.AbstractClient.execute(AbstractClient.java:359)
    at org.elasticsearch.client.support.AbstractClient.search(AbstractClient.java:582)
    at org.elasticsearch.rest.action.search.RestSearchAction.handleRequest(RestSearchAction.java:85)
    at org.elasticsearch.rest.BaseRestHandler.handleRequest(BaseRestHandler.java:54)
    at org.elasticsearch.rest.RestController.executeHandler(RestController.java:205)
    at org.elasticsearch.rest.RestController.dispatchRequest(RestController.java:166)
    at org.elasticsearch.http.HttpServer.internalDispatchRequest(HttpServer.java:128)
    at org.elasticsearch.http.HttpServer$Dispatcher.dispatchRequest(HttpServer.java:86)
    at org.elasticsearch.http.netty.NettyHttpServerTransport.dispatchRequest(NettyHttpServerTransport.java:449)
    at org.elasticsearch.http.netty.HttpRequestHandler.messageReceived(HttpRequestHandler.java:61)
```

## 问题解决

通过以上排查大概知道是历史索引数据处于 open 状态过多，从而导致 ES 的 CPU，内存占用过高而不可用。

``` bash
#关闭不需要的索引，减少内存占用
curl -XPOST "http://localhost:9200/index_name/_close"
```

### 小插曲

关闭非热点索引数据后，楼主的 ES 集群的健康值依然是 red 状态，楼主最后联想到索引的 red 状态可能会影响 ES 的状态，果不其然，如下所示

``` bash
curl GET http://10.252.148.85:9200/_cluster/health?level=indices

{
    "cluster_name": "elasticsearch",
    "status": "red",
    "timed_out": false,
    "number_of_nodes": 1,
    "number_of_data_nodes": 1,
    "active_primary_shards": 660,
    "active_shards": 660,
    "relocating_shards": 0,
    "initializing_shards": 0,
    "unassigned_shards": 9,
    "delayed_unassigned_shards": 0,
    "number_of_pending_tasks": 0,
    "number_of_in_flight_fetch": 0,
    "task_max_waiting_in_queue_millis": 0,
    "active_shards_percent_as_number": 98.65470852017937,
    "indices": {
        "jr-2018.08.06": {
            "status": "red",
            "number_of_shards": 3,
            "number_of_replicas": 0,
            "active_primary_shards": 0,
            "active_shards": 0,
            "relocating_shards": 0,
            "initializing_shards": 0,
            "unassigned_shards": 3
        }
    }
}
```

解决方法：删除这条索引数据（这条数据是楼主排查问题期间产生的脏数据，直接删除即可）

``` bash
curl -XDELETE 'http://10.252.148.85:9200/jr-2018.08.06'
```

## 小结

当 ES 处于单点时，应注意 ES 的索引状态以及服务器的监控，及时清理或者关闭不必要的索引数据，避免这种情况发生。技术成长的道路上，与你同行。
