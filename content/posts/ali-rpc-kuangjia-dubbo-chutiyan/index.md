---
aliases: ["/zh-cn/posts/ali-rpc-kuangjia-dubbo-chutiyan/"]
categories: ["后端"]
title: "阿里 RPC 框架 Dubbo 初体验"
date: "2018-06-07T23:11:29+08:00"
tags: ["Java EE", "Dubbo", "Netty", "gRPC", "后端"]
summary: "最近研究了一下阿里开源的分布式 RPC 框架 Dubbo，楼主写了一个 demo，体验了一下 Dubbo 的功能。"
translationKey: "ali-rpc-kuangjia-dubbo-chutiyan"
---

> 📌 本文原发布于掘金社区：[阿里 RPC 框架 Dubbo 初体验](https://juejin.cn/post/6844903618013822983)

最近研究了一下阿里开源的分布式 RPC 框架 Dubbo，楼主写了一个 demo，体验了一下 Dubbo 的功能。

<span id="user-content-more"></span>

## [](#快速开始 "#快速开始")快速开始

实际上，Dubbo 的官方文档已经提供了如何使用这个 RPC 框架的 example 代码，基于 Netty 的长连接。楼主看这个框架主要是为了在微服务，service mesh 大火的今天做一些技术储备以及了解一下分布式 RPC 框架的设计。

当然即便是写一个 Dubbo 的 demo 也不能随便写写就好了，要认真对待说不定哪一天可以派上用场呢，下面是楼主写的代码的目录结构：\
<a href="https://link.juejin.cn?target=http%3A%2F%2Fimg.hchstudio.cn%2FdubboCode.png" target="_blank" data-ref="nofollow noopener noreferrer" title="http://img.hchstudio.cn/dubboCode.png"><img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/6/7/163dacdab5a8130d~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.png" title="dubboCode图" loading="lazy" alt="dubboCode图" /></a> dubboCode 图

下面我来一一说明一下每个 model 的作用，

1.  micro-service-dubbo-common：是通用工具模块，其他的 model 都需要依赖它。
2.  micro-service-dubbo-dal：是整个项目的 dao 模块，有关数据库操作的代码都放在这里。
3.  micro-service-dubbo-interface：是通用接口模块，专门用来声明接口，被 consumer 与 provider 同时依赖，这么做是为了项目的可拆分与分布式部署。
4.  micro-service-dubbo-model：是公用的实体类模块，不限于数据库对应的 model，也可以放 DTO，VO 等。
5.  micro-service-dubbo-provider：项目的服务提供者。
6.  micro-service-dubbo-web：项目的消费者，也是直接跟前端交互的 controller 层。

另外需要在 pom 文件中添加相关依赖

                                                    
    <!--dubbo-->
    <dependency>
        <groupId>com.alibaba</groupId>
        <artifactId>dubbo</artifactId>
        <version>${dubbo.version}</version>
    </dependency>

    <dependency>
        <groupId>com.101tec</groupId>
        <artifactId>zkclient</artifactId>
        <version>${zkclient_version}</version>
    </dependency>

    <dependency>
        <groupId>org.apache.zookeeper</groupId>
        <artifactId>zookeeper</artifactId>
        <version>${zookeeper_version}</version>
    </dependency>

    <dependency>
        <groupId>org.apache.curator</groupId>
        <artifactId>curator-framework</artifactId>
        <version>${curator_version}</version>
    </dependency>


                                                

## [](#接口创建 "#接口创建")接口创建

既然是 RPC 服务，那就需要一个接口，再有一个实现类。这里的接口定义在我们的 micro-service-dubbo-interface 模块中，具体实现是在 provider 这里创建，在楼主的项目中就是在 micro-service-dubbo-provider 中创建 DemoService 的实现。

                                                    
    public interface DemoService {
        String sayHello(String name);

        public List getUsers();
    }


                                                

                                                    
    @Service("demoService")
    public class DemoServiceImpl implements DemoService {

        @Override
        public String sayHello(String name) {
            System.out.println("[" + new SimpleDateFormat("HH:mm:ss").format(new Date()) + "] Hello " + name + ", request from consumer: " + RpcContext
                    .getContext().getRemoteAddress());
            return "Hello " + name + ", response from provider: " + RpcContext.getContext().getLocalAddress();
        }

        @Override
        public List getUsers() {
            List list = new ArrayList();
            User u1 = new User();
            u1.setName("hejingyuan");
            u1.setAge(20);
            u1.setSex("f");

            User u2 = new User();
            u2.setName("xvshu");
            u2.setAge(21);
            u2.setSex("m");


            list.add(u1);
            list.add(u2);

            return list;
        }
    }


                                                

然后在 consumer 的 pom.xml 中添加对这个接口的依赖，这里的 consumer 就是 micro-service-dubbo-web。

                                                    
    <dependency>
      <groupId>com.whforever</groupId>
        <artifactId>micro-service-dubbo-provider</artifactId>
        <version>1.0-SNAPSHOT</version>
    </dependency>
    <dependency>
        <groupId>com.whforever</groupId>
        <artifactId>micro-service-dubbo-interface</artifactId>
        <version>1.0-SNAPSHOT</version>
    </dependency>


                                                

有了接口，就需要配置一下。

## [](#接口配置 "#接口配置")接口配置

首先在提供方这里发布接口。创建一个 XML 文件，名为：dubbo-provider.xml。

文件内容：

                                                    
    <?xml version="1.0" encoding="UTF-8"?>
    <beans xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xmlns:dubbo="http://code.alibabatech.com/schema/dubbo"
           xmlns="http://www.springframework.org/schema/beans"
           xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans-4.3.xsd
           http://code.alibabatech.com/schema/dubbo http://code.alibabatech.com/schema/dubbo/dubbo.xsd">

        <!-- provider's application name, used for tracing dependency relationship -->
        <dubbo:application name="demo-provider"/>

        <!-- use multicast registry center to export service -->
        <dubbo:registry protocol="zookeeper" address="127.0.0.1:2181" />

        <!-- use dubbo protocol to export service on port 20880 -->
        <dubbo:protocol name="dubbo" port="20880"/>

        <!-- service implementation, as same as regular local bean -->
        <bean id="demoProviderService" class="com.whforever.service.impl.DemoServiceImpl"/>

        <!-- declare the service interface to be exported -->
        <dubbo:service interface="com.whforever.service.DemoService" ref="demoProviderService"/>

    </beans>


                                                

很简单，发布了一个接口，类似 Spring 的一个 bean。

同样，在 consumer 即 micro-service-dubbo-web 的 resource 目录下，也创建一个 dubbo-consumer.xml 文件。内容稍有不同。

                                                    
    <?xml version="1.0" encoding="UTF-8"?>
    <beans xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xmlns:dubbo="http://code.alibabatech.com/schema/dubbo"
           xmlns="http://www.springframework.org/schema/beans"
           xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans-4.3.xsd
           http://code.alibabatech.com/schema/dubbo http://code.alibabatech.com/schema/dubbo/dubbo.xsd">

        <!-- consumer's application name, used for tracing dependency relationship (not a matching criterion),
        don't set it same as provider -->
        <dubbo:application name="demo-consumer"/>

        <!-- use multicast registry center to discover service -->
        <!--<dubbo:registry address="multicast://224.5.6.7:1234"/>-->
        <dubbo:registry protocol="zookeeper" address="127.0.0.1:2181" />

        <!-- generate proxy for the remote service, then demoService can be used in the same way as the
        local regular interface -->
        <dubbo:reference id="demoConsumerService" check="false" interface="com.whforever.service.DemoService"/>

    </beans>


                                                

由此可见，这两个文件的注册发现协议是 ZooKeeper，因此在服务启动之前需要启动 ZooKeeper，具体移步<a href="https://link.juejin.cn?target=http%3A%2F%2Fdubbo.apache.org%2Fbooks%2Fdubbo-admin-book%2Finstall%2Fzookeeper.html" target="_blank" data-ref="nofollow noopener noreferrer" title="http://dubbo.apache.org/books/dubbo-admin-book/install/zookeeper.html">ZooKeeper 注册中心安装启动</a>

## [](#准备测试 "#准备测试")准备测试

测试之前还要做点工作。

在启动 provider 时需要一部分引导程序，请看如下代码：\

                                                        
    public class ProviderMain {
        public static void main(String[] args) throws IOException {
            System.setProperty("java.net.preferIPv4Stack", "true");
            ClassPathXmlApplicationContext context = new ClassPathXmlApplicationContext("dubbo-provider.xml");
            context.start();

            System.in.read(); // press any key to exit
        }
    }


                                                    

consumer 代码\

                                                        

    @Controller
    @RequestMapping("/")
    public class IndexController {

        @Autowired
        DemoService demoService;

        @RequestMapping("/echo")
        @ResponseBody
        public String echo() {
            System.out.println(">>>>>>echo");
            return JSON.toJSONString(demoService.getUsers());
        }
    }


                                                    

## [](#运行 "#运行")运行

先运行 provider：\

                                                        
    [06/06/18 11:56:29:029 CST] main  INFO config.AbstractConfig:  [DUBBO] The service ready on spring started. service: com.whforever.service.DemoService, dubbo version: 2.6.1, current host: 192.168.1.120
    [06/06/18 11:56:30:030 CST] main  INFO config.AbstractConfig:  [DUBBO] Export dubbo service com.whforever.service.DemoService to local registry, dubbo version: 2.6.1, current host: 192.168.1.120
    [06/06/18 11:56:30:030 CST] main  INFO config.AbstractConfig:  [DUBBO] Export dubbo service com.whforever.service.DemoService to url dubbo://192.168.1.120:20880/com.whforever.service.DemoService?anyhost=true&application=demo-provider&bind.ip=192.168.1.120&bind.port=20880&dubbo=2.6.1&generic=false&interface=com.whforever.service.DemoService&methods=sayHello,getUsers&pid=13992&side=provider×tamp=1528300589682, dubbo version: 2.6.1, current host: 192.168.1.120
    [06/06/18 11:56:30:030 CST] main  INFO config.AbstractConfig:  [DUBBO] Register dubbo service com.whforever.service.DemoService url dubbo://192.168.1.120:20880/com.whforever.service.DemoService?anyhost=true&application=demo-provider&bind.ip=192.168.1.120&bind.port=20880&dubbo=2.6.1&generic=false&interface=com.whforever.service.DemoService&methods=sayHello,getUsers&pid=13992&side=provider×tamp=1528300589682 to registry registry://127.0.0.1:2181/com.alibaba.dubbo.registry.RegistryService?application=demo-provider&dubbo=2.6.1&pid=13992®istry=zookeeper×tamp=1528300589673, dubbo version: 2.6.1, current host: 192.168.1.120
    [06/06/18 11:56:30:030 CST] main  INFO transport.AbstractServer:  [DUBBO] Start NettyServer bind /0.0.0.0:20880, export /192.168.1.120:20880, dubbo version: 2.6.1, current host: 192.168.1.120


                                                    

再运行 consumer：

<a href="https://link.juejin.cn?target=http%3A%2F%2Fimg.hchstudio.cn%2Fdubbo-consumer.png" target="_blank" data-ref="nofollow noopener noreferrer" title="http://img.hchstudio.cn/dubbo-consumer.png"><img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/6/7/163dacdab5936558~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.png" title="consumer图" loading="lazy" alt="consumer图" /></a>consumer 图

通过查看 Dubbo 监控中心，可以看到如下情况，具体 Dubbo 监控中心如何安装部署请移步<a href="https://link.juejin.cn?target=http%3A%2F%2Fdubbo.apache.org%2Fbooks%2Fdubbo-admin-book%2Finstall%2Fsimple-monitor-center.html" target="_blank" data-ref="nofollow noopener noreferrer" title="http://dubbo.apache.org/books/dubbo-admin-book/install/simple-monitor-center.html">Simple 监控中心安装</a>

<a href="https://link.juejin.cn?target=http%3A%2F%2Fimg.hchstudio.cn%2Fdubbo-admin.png" target="_blank" data-ref="nofollow noopener noreferrer" title="http://img.hchstudio.cn/dubbo-admin.png"><img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/6/7/163dacdacf527b31~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.png" title="dubboAdmin图" loading="lazy" alt="dubboAdmin图" /></a>dubboAdmin 图

## [](#小结 "#小结")小结

Dubbo 听其大名已久，直到最近才动手写了一些 demo，总体来看上手还是比较简单，官方也提供了比较详细的文档，社区也比较活跃。关于本篇博客中的代码，楼主已经放到了 github，感兴趣的小伙伴，请移步<a href="https://link.juejin.cn?target=https%3A%2F%2Fgithub.com%2FhaifeiWu%2Fmicro-service-dubbo" target="_blank" data-ref="nofollow noopener noreferrer" title="https://github.com/haifeiWu/micro-service-dubbo">Dubbo 初体验 Demo 模板代码</a>

## [](#号外 "#号外")号外

楼主造了一个轮子，LIGHTCONF 是一个基于 Netty 实现的配置管理平台，其核心设计目标是“为业务提供统一的配置管理服务”，可以做到开箱即用。

- <a href="https://link.juejin.cn?target=https%3A%2F%2Fgithub.com%2FhaifeiWu%2Flightconf" target="_blank" data-ref="nofollow noopener noreferrer" title="https://github.com/haifeiWu/lightconf">基于 Netty 实现的轻量级分布式应用配置中心</a>
