---
categories: ["Java"]
title: "线上 Elasticsearch 集群健康值 red 状态问题排查与解决"
date: "2018-08-07T00:00:00+08:00"
tags: ["Elasticsearch", "运维", "问题排查"]
summary: "之前一直运行正常的数据分析平台，最近一段时间没有注意发现日志索引数据一直未生成，大概持续了n多天，当前状态: 单台机器, Elasticsearch（下面称ES）单节点 空集群 ,1000+shrads, 约200G大小。  问题排查 服务"
translationKey: "xian-shang--elasticsearch--ji-qun-jian-kang-zhi--red--zhuang-tai-wen-ti-pai-cha-"
---

> 📌 本文原发布于代码星冰乐：[线上 Elasticsearch 集群健康值 red 状态问题排查与解决](https://changhuin.github.io/article/2018/f023/)

之前一直运行正常的数据分析平台，最近一段时间没有注意发现日志索引数据一直未生成，大概持续了n多天，当前状态: 单台机器, Elasticsearch（下面称ES）单节点(空集群),1000+shrads, 约200G大小。\

## 问题排查

### 服务器内存，CPU状态检查

使用 `top` 查看服务器 `cpu`，内存等占用情况，如下图示（当时楼主的服务器ES应用的CPU占用在90%以上，肯定有问题）\
> 📷 图注：top

内存占用也极高（当时楼主的8G内存的服务器仅剩下150M左右的空闲，肯定是ES的问题）\
> 📷 图注：free

### ES集群状态

查看ES集群健康值，发现 `status` 为 `red`，这种状态表示部分主分片不可用，楼主当前的状态是历史数据可查，但是无法生成新的 `index` 数据。\

    curl https://localhost:9200/_cluster/health?pretty

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

查看每个索引的状态，发现大部分索引状态是 `red` ，处于不可用状态，因为打开的索引数据过多，导致ES占用大量的CPU，内存，使得 `logstash` 不可用，也就无法创建新的索引数据，从而导致数据丢失。\

    curl -XGET   "https://localhost:9200/_cat/indices?v"

    health status index          pri rep docs.count docs.deleted store.size pri.store.size
    red    open   jr-2016.12.20    3   0
    red    open   jr-2016.12.21    3   0
    red    open   jr-2016.12.22    3   0
    red    open   jr-2016.12.23    3   0
    red    open   jr-2016.12.24    3   0
    red    open   jr-2016.12.25    3   0
    red    open   jr-2016.12.26    3   0
    red    open   jr-2016.12.27    3   0

### ES集群分片不可用，导致的查询失败

查询ES时抛出的异常：\

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

## 问题解决

通过以上排查大概知道是历史索引数据处于 open 状态过多，从而导致ES的CPU，内存占用过高导致的不可用。

    #关闭不需要的索引，减少内存占用
    curl -XPOST "https://localhost:9200/index_name/_close"

### 小插曲

关闭非热点索引数据后，楼主的ES集群的健康值依然是 red 状态，楼主最后联想到索引的 red 状态可能会影响ES的状态，果不其然如下所示

    curl GET https://10.252.148.85:9200/_cluster/health?level=indices

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

解决方法，删除这条索引数据（这条数据是楼主排查问题期间产生的脏数据，索引直接删除）\

    curl -XDELETE 'https://10.252.148.85:9200/jr-2018.08.06'

## 小结

当ES处于单点时，应注意ES的索引状态以及服务器的监控，及时清理或者关闭不必要的索引数据，避免这种情况发生。技术成长的道路上，与你同行。

