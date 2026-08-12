---
categories: ["后端"]
title: "golang 重构博客统计服务"
date: "2018-06-25T18:13:12+08:00"
tags: ["Go", "Redis", "Nginx", "Bower", "面试"]
summary: "作为一个后端开发，在 Docker，etcd，k8s 等新技术不断涌现的今天，其背后的功臣 golang 在语言排行榜上持续走高，因此楼主也就开了这次使用 golang 自己开发的基础功能的二次装逼之旅。"
translationKey: "golangzhonggouboketongjifuwu"
---

> 📌 本文原发布于掘金社区：[golang 重构博客统计服务](https://juejin.cn/post/6844903624972173325)

作为一个后端开发，在 Docker，etcd，k8s 等新技术不断涌现的今天，其背后的功臣 golang 在语言排行榜上持续走高，因此楼主也就开了这次使用 golang 自己开发基础功能的二次装逼之旅。\
<span id="user-content-more"></span>

## [](#源于Spring-Boot "#源于Spring-Boot")源于 Spring Boot

感兴趣的小伙伴可以看看楼主的上一篇，基于 Spring Boot 实现的功能，请移步<a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2018%2F6f25%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/article/2018/6f25/">使用 Spring Boot 实现博客统计服务</a>

## [](#实现redis存储逻辑 "#实现redis存储逻辑")实现 Redis 存储逻辑

选择 Redis 而没选择数据库的原因是 Redis 提供了丰富的数据结构与数据持久化策略，另外 Redis 是基于内存的，相对于数据库来说，快了不止一个数量级。而统计阅读次数的场景对接口处理的速度还是有一定的要求的，因此楼主选择了 Redis 作为阅读次数统计的 db。\
下面就是 Redis 操作的基础代码，比较简单，楼主贴一下代码，不做进一步的阐述\
Redis 操作的工具类

    func initRedisPool() {
        // 建立连接池
        RedisClient = &redis.Pool{
            // 从配置文件获取maxidle以及maxactive，取不到则用后面的默认值
            MaxIdle:     1,
            MaxActive:   10,
            IdleTimeout: 180 * time.Second,
            Dial: func() (redis.Conn, error) {
                c, err := redis.Dial("tcp", RedisAddress)
                if err != nil {
                    return nil, err
                }
                // 选择db
                c.Do("SELECT", RedisDb)
                return c, nil
            },
        }
    }

    /**
     * 设置redis的对应key的value
     */
    func redisSet(key string, value string) {
        c, err := RedisClient.Dial()
        if err != nil {
            fmt.Println("Connect to redis error", err)
            return
        }
        _, err = c.Do("SET", key, value)
        if err != nil {
            fmt.Println("redis set failed:", err)
        }
    }

    /**
     * 获取redis的对应key的value
     */
    func redisGet(key string) (value string) {
        c, err := RedisClient.Dial()
        if err != nil {
            fmt.Println("Connect to redis error", err)
            return
        }
        val, err := redis.String(c.Do("GET", key))
        if err != nil {
            fmt.Println("redis get failed:", err)
            return ""
        } else {
            fmt.Printf("Got value is %v \n", val)
            return val
        }
    }

    /**
     * redis使得对应的key的值自增
     */
    func redisIncr(key string) (value string) {
        c, err := RedisClient.Dial()
        _, err = c.Do("INCR", key)
        if err != nil {
            fmt.Println("incr error", err.Error())
        }

        incr, err := redis.String(c.Do("GET", key))
        if err == nil {
            fmt.Println("redis key after incr is : ", incr)
        }
        return incr
    }

## [](#博客阅读次数统计接口实现 "#博客阅读次数统计接口实现")博客阅读次数统计接口实现

博客阅读次数统计的基本业务逻辑就是，将每篇博客对应的 blogId 作为 Redis 的 key，而访问次数就是这个 key 所对应的 value，每访问一次该接口就要将对应的 blogId 自增一次，并返回对应的 value。这里楼主选择的 Redis 的数据结构是 String，下面是楼主实现该逻辑的主要代码：

    package main

    import (
        "encoding/json"
        "fmt"
        "github.com/garyburd/redigo/redis"
        "log"
        "net/http"
        "time"
        "strings"
    )

    const RedisAddress = "127.0.0.1:6379"
    const RedisDb = 0

    const AllowRequestUrlH = "*"
    const  AllowRequestUrlW = "*"
    const  IllegalCharacters = "?"
    const  DefaultReadCount = "1"

    var (
        // 定义常量
        RedisClient *redis.Pool
    )

    func main() {
        // 初始化redis连接池
        initRedisPool()

        // 启动web服务监听
        http.HandleFunc("/*-*/*/", blogReadCountIncr)       //设置访问的路由
        err := http.ListenAndServe(":9401", nil) //设置监听的端口
        if err != nil {
            log.Fatal("ListenAndServe: ", err)
        }
    }

    func blogReadCountIncr(responseWriter http.ResponseWriter, request *http.Request) {

        // 解析参数，默认不解析
        request.ParseForm()

        blogId := request.Form.Get("blogId")

        log.Println(">>>>>> method blogReadCountIncr exec , request params is : ",blogId)

        // 判断请求参数是否为空
        if "" == blogId {
            result := ResultCode{
                Code: 200,
                Msg:  "success",
            }

            ret, _ := json.Marshal(result)
            fmt.Fprintf(responseWriter, string(ret)) //这个写入到w的是输出到客户端的
        }
        
        readCount := redisGet(blogId)
        if "" == readCount {
            // 不符合规则，直接返回
            flag := strings.Index(blogId, AllowRequestUrlH) != 0 ||strings.Index(blogId, AllowRequestUrlW) != 0||strings.Contains(blogId, IllegalCharacters)
            if  !flag {
                result := ResultCode{
                    Code: 200,
                    Msg:  "success",
                }

                ret, _ := json.Marshal(result)
                fmt.Fprintf(responseWriter, string(ret)) //这个写入到w的是输出到客户端的
            }

            redisSet(blogId, DefaultReadCount)
            readCount = DefaultReadCount
        } else {
            readCount = redisIncr(blogId)
        }
        log.Println(">>>>>> readCount is : ",readCount)
        result := ResultCode{
            Code: 200,
            Msg:  "success",
            Data: readCount,
        }
        ret, _ := json.Marshal(result)
        fmt.Fprintf(responseWriter, string(ret)) //这个写入到w的是输出到客户端的
    }
    // 结构体定义返回值
    type ResultCode struct {
        Msg  string `json:"msg"`
        Code int    `json:"code"`
        Data string `json:"data"`
    }

## [](#实现过程中遇到的坑 "#实现过程中遇到的坑")实现过程中遇到的坑

### [](#出现的问题 "#出现的问题")出现的问题

使用 golang 原生的 JSON 工具序列化时，出现序列化失败的问题，如下所示的结构体定义，乍一看是没啥问题的，然而使用

    ret, _ := json.Marshal(result)

序列化时，出现无法序列化成 JSON 串的问题，另外还不报错，这让楼主很是头疼。\

    type ResultCode struct {
        msg  string `json:"msg"`
        code int    `json:"code"`
        data string `json:"data"`
    }

### [](#问题解决 "#问题解决")问题解决

最终楼主通过各种姿势的排查，发现是结构体定义有问题，当定义结构体时首字母必须大写才能序列化成功，这个特点在 golang 里面很是明显，首字母小写的函数在其他文件里面是调不到的。下面给出正确的结构体定义\

    type ResultCode struct {
        Msg  string `json:"msg"`
        Code int    `json:"code"`
        Data string `json:"data"`
    }

## [](#小结 "#小结")小结

目前很多大佬都写过关于 golang web 的教程，如有雷同，请略过不看，本文是通过自己的亲身实战以及楼主自己踩到的坑完成的，另外本文是基于 go 内置的**net/http**库实现的 web 服务。

## [](#号外 "#号外")号外

楼主造了一个轮子，LIGHTCONF 是一个基于 Netty 实现的配置管理平台，其核心设计目标是“为业务提供统一的配置管理服务”，可以做到开箱即用。感兴趣的给个 star 支持一下。

- <a href="https://link.juejin.cn?target=https%3A%2F%2Fgithub.com%2FhaifeiWu%2Flightconf" target="_blank" data-ref="nofollow noopener noreferrer" title="https://github.com/haifeiWu/lightconf">基于 Netty 实现的轻量级分布式应用配置中心</a>

作 者：haifeiWu 原文链接：<a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2018%2F2622%2Farticle%2F2018%2F2622%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/article/2018/2622/article/2018/2622/">www.hchstudio.cn/article/201…</a>版权声明：非特殊声明均为本站原创作品，转载时请注明作者和原文链接。
