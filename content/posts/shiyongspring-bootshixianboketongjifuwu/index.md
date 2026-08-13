---
categories: ["后端"]
title: "使用 Spring Boot 实现博客统计服务"
date: "2018-06-19T14:53:42+08:00"
tags: ["Spring", "Spring Boot", "Redis", "后端", "Java EE"]
summary: "作为一个后端开发，在微服务，server mesh 等概念满天飞的时代，持续学习能力是不能丢的。此外，楼主博客的阅读统计功能是用的是与 HEXO 相匹配的第三方的数量统计功能，也就诞生了楼主这次更换成自己开发的基础功能的装逼之旅。"
---

> 📌 本文原发布于掘金社区：[使用 Spring Boot 实现博客统计服务](https://juejin.cn/post/6844903622145212429)

作为一个后端开发，在微服务，server mesh 等概念满天飞的时代，持续学习能力是不能丢的，因此楼主最近也研究好多 RPC，Netty，Spring Boot 等技术。此外，楼主博客的阅读统计功能用的是与 HEXO 相匹配的第三方的数量统计功能，也就诞生了楼主这次更换成自己开发的基础功能的装逼之旅。\
<span id="user-content-more"></span>

## [](#通过SPRING-INITIALIZR生成工程 "#通过SPRING-INITIALIZR生成工程")通过 SPRING INITIALIZR 生成工程

<a href="https://link.juejin.cn?target=http%3A%2F%2Fimg.hchstudio.cn%2Fspring-init.png" target="_blank" data-ref="nofollow noopener noreferrer" title="http://img.hchstudio.cn/spring-init.png"><img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/6/19/16416d22744b9873~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.png" loading="lazy" alt="spring init" /></a>Spring init\
如上图，通过 Spring 官方的 <a href="https://link.juejin.cn?target=http%3A%2F%2Fstart.spring.io%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://start.spring.io/">Spring Initial</a> 网站生成项目，项目的目录结构如下：

- 目录结构

<!-- -->

    - src
        -main
            -java
                -package
                    #主函数，启动类，运行它如果运行了 Tomcat、Jetty、Undertow 等容器
                    -SpringbootApplication    
            -resouces
                #存放静态资源 js/css/images 等
                - statics
                #存放 html 模板文件
                - templates
                #主要的配置文件，SpringBoot启动时候会自动加载application.yml/application.properties        
                - application.yml
        #测试文件存放目录        
        -test
     # pom.xml 文件是Maven构建的基础，里面包含了我们所依赖JAR和Plugin的信息
    - pom

- pom 依赖

<!-- -->

    <?xml version="1.0" encoding="UTF-8"?>
    <project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
        <modelVersion>4.0.0</modelVersion>

        <groupId>com.*</groupId>
        <artifactId>*-*</artifactId>
        <version>0.0.1-SNAPSHOT</version>
        <packaging>jar</packaging>

        <name>base-service</name>
        <description>Demo project for Spring Boot</description>

        <parent>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-parent</artifactId>
            <version>2.0.3.RELEASE</version>
            <relativePath/> <!-- lookup parent from repository -->
        </parent>

        <properties>
            <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
            <project.reporting.outputEncoding>UTF-8</project.reporting.outputEncoding>
            <java.version>1.8</java.version>
        </properties>

        <dependencies>
            <!-- https://mvnrepository.com/artifact/org.apache.commons/commons-lang3 -->
            <dependency>
                <groupId>org.apache.commons</groupId>
                <artifactId>commons-lang3</artifactId>
                <version>3.6</version>
            </dependency>

            <dependency>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-starter-data-redis</artifactId>
            </dependency>
            
            <dependency>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-starter-web</artifactId>
            </dependency>

            <dependency>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-starter-test</artifactId>
                <scope>test</scope>
            </dependency>
            <dependency>
                <groupId>com.almende.eve</groupId>
                <artifactId>eve-bundle-full</artifactId>
                <version>3.1.1</version>
            </dependency>
        </dependencies>

        <build>
            <plugins>
                <plugin>
                    <groupId>org.springframework.boot</groupId>
                    <artifactId>spring-boot-maven-plugin</artifactId>
                </plugin>

                <plugin>
                    <groupId>org.springframework.boot</groupId>
                    <artifactId>spring-boot-maven-plugin</artifactId>
                </plugin>
            </plugins>
        </build>
    </project>

## [](#实现redis存储逻辑 "#实现redis存储逻辑")实现 Redis 存储逻辑

选择 Redis 而没选择数据库的原因是 Redis 提供了丰富的数据结构与数据持久化策略，另外 Redis 是基于内存的，相对于数据库来说，快了不止一个数量级。而统计阅读次数的场景对接口处理的速度还是有一定的要求的，因此楼主选择了 Redis 作为阅读次数统计的 db。\
下面就是 Redis 操作的基础代码，比较简单，楼主贴一下代码，不做进一步的阐述

- Redis 的接口类

      public interface RedisService {
          public boolean set(final String key, final String value);
          public String get(final String key);
          public String incr(final String key);
      }

- Redis 的实现类

<!-- -->

    @Service
    public class RedisServiceImpl implements RedisService {

        @Resource
        private RedisTemplate<String, ?> redisTemplate;

        @Override
        public boolean set(final String key, final String value) {
            boolean result = redisTemplate.execute(new RedisCallback<Boolean>() {
                @Override
                public Boolean doInRedis(RedisConnection connection) throws DataAccessException {
                    RedisSerializer<String> serializer = redisTemplate.getStringSerializer();
                    connection.set(serializer.serialize(key), serializer.serialize(value));
                    return true;
                }
            });
            return result;
        }

        @Override
        public String incr(final String key) {
            String incr = redisTemplate.execute(new RedisCallback<String>() {
                @Override
                public String doInRedis(RedisConnection redisConnection) throws DataAccessException {
                    RedisSerializer<String> serializer = redisTemplate.getStringSerializer();
                    Long value = redisConnection.incr(serializer.serialize(key));
                    return String.valueOf(value);
                }
            });
            return incr;
        }

        @Override
        public String get(final String key){
            String result = redisTemplate.execute(new RedisCallback<String>() {
                @Override
                public String doInRedis(RedisConnection connection) throws DataAccessException {
                    RedisSerializer<String> serializer = redisTemplate.getStringSerializer();
                    byte[] value =  connection.get(serializer.serialize(key));
                    return serializer.deserialize(value);
                }
            });
            return result;
        }

    }

## [](#博客阅读次数统计接口实现 "#博客阅读次数统计接口实现")博客阅读次数统计接口实现

博客阅读次数统计的基本业务逻辑就是，每篇博客对应的 blogId 作为 Redis 的 key，而访问次数就是这个 key 所对应的 value，每访问一次该接口就要将对应的 blogId 自增一次，并返回对应的 value。这里楼主选择的 Redis 的数据结构是 Redis 的 String，下面是楼主实现该逻辑的主要代码：

    /**
     * 统计博客阅读次数.
     *
     * @author wuhf
     * @Date 2018/6/15 15:59
     **/
    @RestController
    @RequestMapping("/")
    public class BlogReadCountController {

        private static String ALLOW_REQUEST_URL = "******";
        private static String ILLEGAL_CHARACTERS = "*";
        private static String DEFAULT_READ_COUNT = "1";
        private static Logger logger = LoggerFactory.getLogger(BlogReadCountController.class);

        @Autowired
        private RedisService redisService;

        @ResponseBody
        @RequestMapping("/*_*")
        public ResultCode blogReadCountIncr(HttpServletRequest request,String blogId) {
            ResultCode resultCode = new ResultCode();
            try {
                logger.info(">>>>>> method blogReadCountIncr exec , request params is : {}",blogId);
                String readCount = redisService.get(blogId);
                if (StringUtils.isBlank(readCount)) {
                    
                    if (!blogId.startsWith(ALLOW_REQUEST_URL)||blogId.contains(ILLEGAL_CHARACTERS)) {
                        resultCode.setCode(Messages.API_ERROR_CODE);
                        resultCode.setMsg(Messages.API_ERROR_MSG);
                        return resultCode;
                    }

                    redisService.set(blogId,DEFAULT_READ_COUNT);
                    readCount = DEFAULT_READ_COUNT;
                } else {
                    readCount = redisService.incr(blogId);
                }
                logger.info(">>>>>> readCount is : {}",readCount);
                resultCode.setCode(Messages.SUCCESS_CODE);
                resultCode.setMsg(Messages.SUCCESS_MSG);
                resultCode.setData(readCount);
                return resultCode;
            } catch (Exception e) {
                e.printStackTrace();
                resultCode.setCode(Messages.API_ERROR_CODE);
                resultCode.setMsg(Messages.API_ERROR_MSG);
                return resultCode;
            }
        }
    }

## [](#实现过程中遇到的坑 "#实现过程中遇到的坑")实现过程中遇到的坑

- 设置应用启动的端口号

<!-- -->

    server.port=9401

- 设置应用访问的 path

Spring Boot 应用默认的应用访问的 path 还是 “/“，楼主在这里吃了点苦头，使用http://项目名:port访问服务，愣是访问不通，在配置文件中设置如下所示

    server.servlet.context-path=/项目名

## [](#小结 "#小结")小结

目前很多大佬都写过关于 SpringBoot 的教程了，如有雷同，请略过不看，本文通过自己的亲身实战以及楼主自己踩到的坑完成的，另外本文是基于最新的 spring-boot-starter-parent：2.0.3.RELEASE 编写。

## [](#号外 "#号外")号外

楼主造了一个轮子，LIGHTCONF 是一个基于 Netty 实现的配置管理平台，其核心设计目标是“为业务提供统一的配置管理服务”，可以做到开箱即用。感兴趣的给个 star 支持一下。

- <a href="https://link.juejin.cn?target=https%3A%2F%2Fgithub.com%2FhaifeiWu%2Flightconf" target="_blank" data-ref="nofollow noopener noreferrer" title="https://github.com/haifeiWu/lightconf">基于 Netty 实现的轻量级分布式应用配置中心</a>
