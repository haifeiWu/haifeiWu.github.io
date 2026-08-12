---
aliases: ["/zh-cn/posts/golang-xiangmuzhongdequanlianluzhuizong-tracing/"]
categories: ["后端"]
title: "golang 项目中的全链路追踪（tracing）"
date: "2024-03-30T18:01:24+08:00"
tags: ["后端", "微服务", "架构"]
summary: "链路追踪（Tracing）是一种技术，用于监视和记录计算机程序或系统的运行情况。在分布式系统中，追踪可以帮助开发者和运维人员理解多个组件是如何协同工作的，以及在处理请求时它们之间的交互情况。"
translationKey: "golang-xiangmuzhongdequanlianluzhuizong-tracing"
---

> 📌 本文原发布于掘金社区：[golang 项目中的全链路追踪（tracing）](https://juejin.cn/post/7352075662453309478)

## **是什么**

链路追踪（Tracing）是一种技术，用于监视和记录计算机程序或系统的运行情况。在分布式系统中，追踪可以帮助开发者和运维人员理解多个组件是如何协同工作的，以及在处理请求时它们之间的交互情况。

想象一下，你在一个大型购物中心里跟踪一个购物者的行为。这个购物者从进入购物中心开始，先后访问了不同的商店，比如服装店、电子产品店和食品店。在这个过程中，你可能想知道购物者在每个商店花了多长时间，他们是否遇到了任何问题，以及他们最终购买了什么商品。

同样地，在计算机系统中，一个请求可能需要经过多个服务或组件来得到处理。追踪系统就像是一个高级的摄像头，记录下请求在系统中的每一个步骤，包括它访问了哪些服务、每个服务处理请求所花费的时间、以及在处理过程中是否有任何异常或错误发生。

通过分析这些追踪数据，开发者可以发现系统的性能瓶颈，比如某个服务响应慢，或者某个环节出现了错误。这样，他们就可以针对性地优化系统，提高效率和稳定性。

<img src="https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/c275af4b2c5548b0998a6bbb0f6dd138~tplv-k3u1fbpfcp-jj-mark:3024:0:0:0:q75.awebp#?w=3352&amp;h=1229&amp;s=1214136&amp;e=png&amp;b=fffefe" loading="lazy" />

## **为什么**

在分布式系统中使用追踪（tracing）的原因主要包括以下几点：

1.  **复杂性管理**：分布式系统通常由多个组件和服务构成，这些组件可能分布在不同的地理位置和服务器上。系统的复杂性随着组件数量的增加而呈指数级增长。追踪可以帮助理解和管理这种复杂性，通过记录和分析请求在系统中的流动路径，开发者可以清晰地看到每个组件的行为和性能。
2.  **性能优化**：追踪提供了关于系统性能的详细信息，包括请求的处理时间、瓶颈位置和资源使用情况。这些数据对于识别性能瓶颈、优化资源分配和提高系统效率至关重要。
3.  **故障诊断**：当系统出现问题时，追踪可以帮助快速定位问题的根源。通过分析请求的追踪数据，可以发现是哪个环节出现了问题，以及问题发生的原因，从而快速解决问题并恢复服务。
4.  **系统可见性**：追踪增加了系统的可见性，使得开发者和运维人员能够理解系统的内部工作机制。这种可见性对于维护系统的健康状态和预测潜在问题非常重要。

总之，分布式追踪是理解和管理现代复杂分布式系统的关键工具。它不仅帮助开发者和运维团队保持系统的稳定和高效运行，还为业务增长和创新提供了支持。

## **怎么做**

### **OpenTelemetry**

OpenTelemetry 为我们在系统中更轻量化地接入 tracing 提供了标准协议，让我们在系统中接入 tracing 更简单，基本可以实现自动或者半自动的 tracing 埋点。

<img src="https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/f8a1272ed1334b21afd1c68067e1fae5~tplv-k3u1fbpfcp-jj-mark:3024:0:0:0:q75.awebp#?w=3923&amp;h=1317&amp;s=1703598&amp;e=png&amp;b=fefdfd" loading="lazy" />

如上图所示，tracing 实现链路追踪是通过 Trace 的“父子关系”来构造的，而这个关系主要由组成 Trace 的 Span 而来（Trace Span 的概念最早来自于 <a href="https://link.juejin.cn?target=https%3A%2F%2Fresearch.google.com%2Fpubs%2Fpub36356.html" target="_blank" data-ref="nofollow noopener noreferrer" title="https://research.google.com/pubs/pub36356.html">Google 的 Dapper</a> ）。

- Trace 记录了整个请求的生命周期，本身由一组 Span 组成，Span 代表其中的一条调用链

Span 具有“父子关系”，这个父子关系由 SpanID 和 ParentSpanID 组成

- 当调用传播到下一层时，原来的 SpanID 就变成了 ParentSpanID，随后会生成一个新的 SpanID。
- Span 的传播可能会跨进程、跨主机，因此需要有一个传递 TraceID、SpanID 的途径，这个途径叫做 Trace Propagation，Trace Propagation 需要保证上下游的服务都能够支持一样的协议才行，否则传播到下一层时，因为服务无法识别，Trace 会断掉。
- 由于系统中可能具有多个服务，还有队列、数据库、ServiceMesh 等中间件，因此 Trace Propagation 需要遵循某个国际化标准，这个标准需要尽可能的通用。
- 最早出现的国际化标准是 OpenTracing，随后还有 Google 发起的 OpenCensus 项目。
- 而目前 OpenTracing 项目和 OpenCensus 项目已经合并成为 OpenTelemetry，OpenTelemetry 已经成为 Trace 领域的唯一国际化标准。

而 OpenTelemetry 标准带来的好处不仅仅是解决各个系统之间的 Trace 互通问题，还有统一的 SDK、自动化埋点方案、数据采集、Traces/Metrics/Logs 互通等等好处。感兴趣的同学可以移步：<a href="https://link.juejin.cn?target=https%3A%2F%2Fdeveloper.aliyun.com%2Farticle%2F766070" target="_blank" data-ref="nofollow noopener noreferrer" title="https://developer.aliyun.com/article/766070">OpenTelemetry 介绍</a>。

### **SLS**

基于阿里云的 sls 提供的基于标准 OpenTelemetry 协议的 tracing 采集方案。

<img src="https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/7d651a938d6e43d5a3efb651221f90dc~tplv-k3u1fbpfcp-jj-mark:3024:0:0:0:q75.awebp#?w=2857&amp;h=1964&amp;s=2038246&amp;e=png&amp;b=fffefe" loading="lazy" />

如上图所示：sls 支持的采集方式有多种，日志服务支持如下接入方案。

- 使用 OpenTelemetry、Jaeger（目前仅支持 https、grpc 方式）、Zipkin、OpenCensus 等直接将 Trace 数据接入到日志服务。
- 使用 OpenTelemetry Collector 转发 OpenTelemetry、Jaeger（全协议支持）、Zipkin、OpenCensus、AWS X-Ray、SignalFX（Splunk）等平台上的 Trace 数据到日志服务。
- 使用 Logtail 转发 SkyWalking 的 Trace 数据到日志服务。
- 使用自定义协议将 Trace 数据接入到日志服务，并通过日志服务加工功能将 Trace 数据格式转换为 OpenTelemetry 格式。

这次在 push 服务中实现的 tracing 的接入方案主要是基于 OpenTelemetry 统一协议的采集方案，直接使用阿里云提供的 sdk 即可，无需部署其他依赖组件。

### **初始化**

1.  **配置信息：**

``` yaml
[data.tracing]
    traceExporterEndpoint = ""
    metricExporterEndpoint = ""
    slsProject = ""
    slsInstance = ""
    accessKeyId = ""
    accessKeySecret = ""
```

上面的配置信息是测环境的，配置完成后可以本地调试，同时可以在下面的 sls 看板上看到数据

**provider 初始化代码块：**

``` go
var (
    MetricPushInterval        = 20
    Namespace          string = "xxx"
    // MetricName is the name of the compiled software.
    MetricName = "xxx"
    // Name is the name of the compiled software.
    Name = "xxx"
    // Version is the version of the compiled software.
    Version string = "v0.1.0"
)


func initTracerConfig(tracingConfig *conf.Tracing) *provider.Config {
     //  Namespace, Name, Version 必须有值
     slsConfig, err := provider.NewConfig(provider.WithServiceName(Name),
       provider.WithServiceVersion(Version),
       provider.WithServiceNamespace(Namespace),
       provider.WithTraceExporterEndpoint(tracingConfig.TraceExporterEndpoint),
       provider.WithMetricExporterEndpoint(tracingConfig.MetricExporterEndpoint),
       provider.WithSLSConfig(tracingConfig.SlsProject, tracingConfig.SlsInstance, tracingConfig.AccessKeyId, tracingConfig.AccessKeySecret))
    // 如果初始化失败则 panic，可以替换为其他错误处理方式
    if err != nil {
       panic(err)
    }
    return slsConfig
}
```

1.  **main.go 中接入：**

``` go
func main() {
    flag.Parse()
    c := config.New(config.WithPath(confPath))
    if err := c.Load(); err != nil {
       panic(err)
    }
    if err := c.Scan(&conf.Cfg); err != nil {
       panic(err)
    }
    // ...
    // 初始化 tracing
    slsConfig := initTracerConfig(&conf.Cfg.Data.Tracing)
    if err := provider.Start(slsConfig); err != nil {
       panic(err)
    }
    defer provider.Shutdown(slsConfig)
    // ...
}
```

### **gin 接入 tracing**

gin 提供了官方支持的采集方案，侵入性很低，基本上一行代码可以搞定

引入采集 tracing 的组件：

``` go
go get "go.opentelemetry.io/contrib/instrumentation/github.com/gin-gonic/gin/otelgin"
```

在 gin 中使用中间件即可：

``` go
func main() {
    // ...... 省略
    r := gin.Default()
    r.Use(otelgin.Middleware(serviceName))
    // ...... 省略
}
```

### **Redis 接入 tracing**

go-redis 组件提供了官方支持的 OpenTelemetry 协议的采集方案，侵入性很低，一行代码搞定。

引入 redisotel 组件：

``` go
go get "github.com/go-redis/redis/extra/redisotel/v8"
```

在初始化 redis-cli 的地方添加 hook 代码即可

``` go
func NewRedisClient(conf *conf.Data) *redis.Client {
    // ... 省略
    // 添加下面这行采集 tracing 的代码
    client.AddHook(redisotel.NewTracingHook())
    // ... 省略
    return client
}
```

### **MySQL 接入 tracing**

gorm 官方也提供了支持 OpenTelemetry 协议的采集方案，侵入性很低，一行代码搞定。

引入 gromotel 组件：

``` go
go get "gorm.io/plugin/opentelemetry/tracing"
```

在初始化 db-cli 的地方添加如下代码即可：

``` go
 func NewDB(conf *conf.Data, logger log.Logger, zapLogger *zap.Logger) *gorm.DB {
    // ... 省略
    if err = db.Use(tracing.NewPlugin(tracing.WithoutMetrics())); err != nil {
       panic(err)
    }
    return db
}
```

## **已接入系统展示**

**push-service 服务概览** **：**

<img src="https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/7989cb1f36c943ea8f06ad644c920f41~tplv-k3u1fbpfcp-jj-mark:3024:0:0:0:q75.awebp#?w=4087&amp;h=1946&amp;s=1023320&amp;e=png&amp;b=fefefe" loading="lazy" />

**接口概览：**

<img src="https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/f1468336463c487db99a867a00915f42~tplv-k3u1fbpfcp-jj-mark:3024:0:0:0:q75.awebp#?w=4092&amp;h=1820&amp;s=1039824&amp;e=png&amp;b=fefefe" loading="lazy" />

**trace 详情展示：**

<img src="https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/713aa7e832fc45549c7b7acb19b5d6fb~tplv-k3u1fbpfcp-jj-mark:3024:0:0:0:q75.awebp#?w=3642&amp;h=1257&amp;s=417190&amp;e=png&amp;b=fefefe" loading="lazy" />

## **未来规划**

基于 sls 的 trace 能力，将 sls 的 tracing，metric，log 串联起来，同时也可以接入相关报警，实现更细粒度的监控报警方案。

## **相关文档与 lib**

<a href="https://link.juejin.cn?target=https%3A%2F%2Fgithub.com%2Fgo-gorm%2Fopentelemetry" target="_blank" data-ref="nofollow noopener noreferrer" title="https://github.com/go-gorm/opentelemetry">github.com/go-gorm/ope…</a>

<a href="https://link.juejin.cn?target=https%3A%2F%2Fupstash.com%2Fblog%2Fgo-redis-opentelemetry" target="_blank" data-ref="nofollow noopener noreferrer" title="https://upstash.com/blog/go-redis-opentelemetry">upstash.com/blog/go-red…</a>

<a href="https://link.juejin.cn?target=https%3A%2F%2Fgithub.com%2Fredis%2Fgo-redis%2Ftree%2Fmaster%2Fextra%2Fredisotel" target="_blank" data-ref="nofollow noopener noreferrer" title="https://github.com/redis/go-redis/tree/master/extra/redisotel">github.com/redis/go-re…</a>

<a href="https://link.juejin.cn?target=https%3A%2F%2Fhelp.aliyun.com%2Fzh%2Fsls%2Fuser-guide%2Fimport-trace-data-from-golang-applications-to-log-service-by-using-opentelemetry-sdk-for-golang%3Fspm%3Da2c4g.11186623.0.i29" target="_blank" data-ref="nofollow noopener noreferrer" title="https://help.aliyun.com/zh/sls/user-guide/import-trace-data-from-golang-applications-to-log-service-by-using-opentelemetry-sdk-for-golang?spm=a2c4g.11186623.0.i29">help.aliyun.com/zh/sls/user…</a>

<a href="https://link.juejin.cn?target=https%3A%2F%2Fflow.visionhope.cn%2Fposts%2Fopentelemetry-guide%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="https://flow.visionhope.cn/posts/opentelemetry-guide/">flow.visionhope.cn/posts/opent…</a>

## **相关 Tracing 实践**

<a href="https://link.juejin.cn?target=https%3A%2F%2Fxie.infoq.cn%2Farticle%2F8f4b171b1992c6d95e4426230" target="_blank" data-ref="nofollow noopener noreferrer" title="https://xie.infoq.cn/article/8f4b171b1992c6d95e4426230">xie.infoq.cn/article/8f4…</a>

<a href="https://link.juejin.cn?target=https%3A%2F%2Fdeveloper.aliyun.com%2Farticle%2F785854" target="_blank" data-ref="nofollow noopener noreferrer" title="https://developer.aliyun.com/article/785854">developer.aliyun.com/article/785…</a>

<a href="https://link.juejin.cn?target=https%3A%2F%2Fdeveloper.aliyun.com%2Farticle%2F783270%3Fspm%3Da2c6h.12873639.article-detail.10.3e2c5d17TdedkW" target="_blank" data-ref="nofollow noopener noreferrer" title="https://developer.aliyun.com/article/783270?spm=a2c6h.12873639.article-detail.10.3e2c5d17TdedkW">developer.aliyun.com/article/783…</a>
