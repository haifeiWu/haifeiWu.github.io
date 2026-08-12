---
aliases: ["/zh-cn/posts/spring-5-webflux--xing-neng-ce-shi---yi/"]
categories: ["Java"]
title: "Spring 5 WebFlux 性能测试[译]"
date: "2018-11-11T00:00:00+08:00"
tags: ["Spring", "WebFlux", "性能优化"]
summary: "Java 世界对反应式编程抱有很高的期望。根据 官方文档 的描述，它使程序员能够构建更具弹性，弹性，响应和消息驱动的应用程序。简而言之，它是一种更好，更快，更现代的模型，可以防止应用程序空闲。Spring 5 通过结合基于 Proje"
translationKey: "spring-5-webflux--xing-neng-ce-shi---yi"
---

> 📌 本文原发布于代码星冰乐：[Spring 5 WebFlux 性能测试[译]](https://changhuin.github.io/article/2018/b971/)

`Java` 世界对反应式编程抱有很高的期望。根据 <a href="https://www.reactivemanifesto.org/" target="_blank" rel="noopener">官方文档</a> 的描述，它使程序员能够构建更具弹性，弹性，响应和消息驱动的应用程序。简而言之，它是一种更好，更快，更现代的模型，可以防止应用程序空闲。

`Spring 5` 通过结合基于 <a href="https://projectreactor.io/" target="_blank" rel="noopener">Project Reactor</a>的 `Spring` 反应计划，引入了一种新的响应式编程模型。但它能完成这项工作吗？

我们研究了`Spring` 提供的新功能，并对它进行了一次性能测试，测试结果请往下看，我想不会让你失望的。

**注意**：我们的结果可能会在几周/几个月内改变。实际上，截至目前，尚未发布真实的 `Spring` 样本，并且文档不完整。`Spring 5` 和 `Spring Boot 2` 仍在开发中（`Spring Framework 5.0.0 RC3`，`Spring Boot 2.0.0.M2`），`Project Reactor` 也在不断发展。此外，社区的反馈仍然很少（`JHipster`，`Spring`，`Reddit`）。

## What’s new in Spring 5?

Spring 框架引入了很多新功能。其中最重要的是反应式编程。

## Spring MVC and Spring WebFlux

可能仍然有一些人可能试图用旧的 `Spring 4` 技术进行反应式编程，如果你这样做，那么你肯定可能会遇到一些麻烦。`Spring 5` 提供了一个易于使用的新模块：`spring-webflux`。它与它的兄弟 `spring-mvc` 做同样的事情，但是它是一种响应式编程模型。让我们看看它是如何工作的吧。

`WebFlux` 主要围绕两个 `Project Reactor` 的类：`Mono` 和 `Flux`。

`Mono` 是 `CompletableFuture` 类型的反应等价物，允许以反应方式处理单个对象。`Flux` 是多个对象的等价物。它们像 `Stream` 一样处理（准备好使用 `lambda` 表达式）。因此，你可能会看到如下所示的代码：

    reactiveService.getResults()
        .mergeWith(Flux.interval(100))
        .map(r -> r * 2)
        .doOnNext(Service1::someObserver)
        .doAfterTerminate(Service2::incrementTerminate);

它们都是 `Reactive Streams` 规范的 `Publisher` 接口的实现，因此它们需要注册到订阅服务器以便数据开始流动。

幸运的是，基于注解的编程模型仍然是最新的，与 `Spring MVC` 的唯一区别是 `REST` 层的方法现在返回 `Mono` 或 `Flux`：

    @PutMapping("/operations")
    public Mono<Operation> updateOperation(@Valid @RequestBody Operation operation)
    throws URISyntaxException {

       log.debug("REST request to update Operation : {}", operation);
       return operationRepository.save(operation);
    }

`Spring` 知道如何处理 `Monos` 或 `Fluxs`。它会自动将封装的对象传递给前端。

关于与数据库的通信，`Spring 5` 支持 `Cassandra`，`CouchBase`，`MongoDB`和 `Redis` 的反应驱动程序，它们可以跟 `Spring Data` 一起使用。

下面是操作 `MongoDB` 代码例子

    @Repository
    public interface BankAccountRepository extends ReactiveMongoRepository<BankAccount,String> {
       Mono<BankAccount> getFirstByBalanceEndingWith(BigDecimal bigDecimal);
       Mono<Long> countByBalanceEquals(BigDecimal bigDecimal);
       Flux<BankAccount> findAllByIdBefore(UUID uuid);
    }

## Our tests

### Why?

反应式编程现在正在流行，当然，`Pivotal` 决定在逻辑上将其集成到 `Spring` 框架中，并承诺提供更好的性能和可扩展性。可悲的是，没有给出任何性能测试数据……

### How?

我们通过在生产模式下对不同的 `JHipster` 生成的应用程序（`MySQL`，`Mongo`，`Model`……）进行压力测试（使用`Gatling`）。

这些应用程序中的每一个都经过多次复制和修改，以确保我们的测试有丰富的测试数据，从而确保测试的正确性。

例如，对于 MySQL 应用程序，我们创建了四个类似的应用程序：

- 使用 `Spring 4`（因为你可以使用 `JHipster` 实际生成）
- 使用 `Spring 5`（仅迁移）
- 使用 `Spring 5` 和反应式编程（在 `REST` 层上）
- 使用 `Spring 5` 和反应式编程（仅在一个实体的 `RestController` 类上）

对于具有异步驱动程序的 Mongo，我们创建了应用程序：

- 使用`Spring 4`（因为你可以使用`JHipster`实际生成）
- 使用`Spring 5`（仅迁移）
- 使用`Spring 5`和反应式编程（在`REST`层上）
- 使用`Spring 5`和反应式编程（仅在一个实体的`RestController`类上）
- 使用`Spring 5`和实体上的反应式编程一直到存储库。

`Spring`允许程序员配置自己的调度程序（处理被动调用的线程池）。因此，当使用反应式编程时，仅在 `REST` 层（而不是实体）上，我们尝试了不同的调度程序：`Schedulers.parallel()`每个 CPU 核心使用一个线程，而`Schedulers.elastic()`动态创建线程。

每个测试包括同时启动 `Gatling 5000/10000/15000` 用户，每个用户执行场景中描述的操作：

    scenario("Test the Operation entity")
            .exec(http("First unauthenticated request")
            .get("/api/account")
            .headers(headers_http)
            .check(status.is(401))).exitHereIfFailed
            .pause(5)
            .exec(http("Authentication")
            .post("/api/authenticate")
            .headers(headers_http_authentication)
            .body(StringBody("""{"username":"admin", "password":"admin"}""")).asJSON
            .check(header.get("Authorization").saveAs("access_token"))).exitHereIfFailed
            .pause(1)
            .repeat(2) {
                exec(http("Authenticated request")
                .get("/api/account")
                .headers(headers_http_authenticated)
                .check(status.is(200)))
                .pause(5)
            }
            .repeat(2) {
                exec(http("Get all operations")
                .get("/api/operations")
                .headers(headers_http_authenticated)
                .check(status.is(200)))
                .pause(5 seconds, 10 seconds)
                .exec(http("Create new operation")
                .post("/api/operations")
                .headers(headers_http_authenticated)
                .body(StringBody("""{"id":null, "date":"2020-01-01T00:00:00.000Z", "description":"SAMPLE_TEXT", "amount":"1"}""")).asJSON
                .check(status.is(201))
                .check(headerRegex("Location", "(.*)").saveAs("new_operation_url"))).exitHereIfFailed
                .pause(5)
                .repeat(8) {
                    exec(http("Get created operation")
                    .get("${new_operation_url}")
                    .headers(headers_http_authenticated))
                    .pause(3)
                }
                .exec(http("Delete created operation")
                .delete("${new_operation_url}")
                .headers(headers_http_authenticated))
                .pause(5)
           }

然后，我们可以通过比较时间或错误/崩溃来分析这些结果。

### Our big configuration:

- 机器 1 用作 `Spring Boot` 服务器和本地数据库：`i7-4790K 4GHz - 16Go - SSD - Ubuntu 16.04 64bits`
- 机器 2 用作加特林客户端：`i7-4790K 4GHz - 16Go - SSD - Ubuntu 16.04 64bits`
- `Cisco SG100-24 24` 端口千兆交换机
> 📷 图注：configuration

## Results

从 `5000` 个用户的模拟生成了以下结果。我们还使用 `10000/15000/20000` 用户进行了测试，但由于错误数量很多，结果并不一致。

### With a MySQL-based JHipster application:

（注意：下面的结果不包括场景中的暂停。）\
> 📷 图注：MySQL-based

当用户在他的 Gatling 场景中出现错误时，他的模拟将停止。因此，如果存在一些错误，则请求服务器的用户较少，因此负载较低且时间更改。

错误可以有几种：超时，达到数据库连接的阈值，使用 Spring 创建/销毁 bean 的并发问题，……

这些图表显示了用户运行 Gatling 场景所需的总时间。\
> 📷 图注：MySQL-based2
> 📷 图注：MySQL-based3

### With a Mongo-based JHipster application:
> 📷 图注：MySQL-based3
> 📷 图注：MySQL-based3
> 📷 图注：MySQL-based3

## Regarding the execution times

我们可以看到，总体而言，`Reactive` 应用程序比“经典” `Spring` 应用程序慢。

对于 MySQL，它是可预测的，因为数据库在使用过程中设置了所有锁，并且没有官方的响应/异步驱动程序。

对于`Mongo`，有一堆完整的反应组件（驱动程序，存储库，……），但即便如此，性能也会更差。

此外，我们注意到`Spring 4` 和 `Spring 5` 之间的速度没有明显改善，即使没有添加反应式编程。

## Regarding scalability

关于可扩展性，`Reactive` 应用程序可以处理比`Spring4` / `Spring5` 应用程序更少的用户。\
实际上，我们通过使用 `Gatling` 模拟`5000,10000,15000`和`20000`用户注意到了这种差异。

从`10000`个用户开始，我们在`Reactive`应用程序上有太多错误，通常超过`40％`的`KO`请求。

## Conclusion

- 我们的反应式应用程序没有观察到速度的提高（`Gatling` 的结果甚至略差）。
- 关于用户友好性，反应式编程不会添加大量新代码，但它肯定是一种更复杂的编码（和调试……）方式。可能需要快速 `Java 8` 复习。
- 目前的主要问题是缺乏文件。这是我们生成测试应用程序的最大障碍，因此我们可能错过了一个关键点。
- 因此，我们建议不要在反应式编程上跳得太快并等待更多反馈。`Spring WebFlux` 尚未证明其优于 `Spring MVC` 的优势。

你可以在此存储库中找到我们的代码：<a href="https://github.com/jhipster/webflux-jhipster" target="_blank" rel="noopener">jhipster / webflux-jhipster</a>。

`Gatling` 结果可以在每个模块根目录的 `gatling-results` 目录中找到。

## 原文链接

- <a href="https://blog.ippon.tech/spring-5-webflux-performance-tests/" target="_blank" rel="noopener">Spring 5 WebFlux: Performance tests</a>

