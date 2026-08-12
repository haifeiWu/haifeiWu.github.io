---
categories: ["后端"]
title: "classpath* 和 classpath使用遇到的问题"
date: "2018-05-24T22:00:41+08:00"
tags: ["Java", "Spring", "MyBatis", "Dubbo"]
summary: "在spring配置mybatis的时候需要加载mybatis的多个相关配置文件，其中mybatis的mapper对应的xml通常放在其他的jar包中，mybatis-conf文件通常在当前工程中，so，也就引出了今天遇到的问题，那么classpath* 和 classpath到底"
---

> 📌 本文原发布于掘金社区：[classpath* 和 classpath使用遇到的问题](https://juejin.cn/post/6844903609893650439)

在spring配置mybatis的时候需要加载mybatis的多个相关配置文件，其中mybatis的mapper对应的xml通常放在其他的jar包中，mybatis-conf文件通常在当前工程中，so，也就引出了今天遇到的问题，那么classpath\* 和 classpath到底有啥区别呢？

<span id="user-content-more"></span>

## [](#错误的配置与看到的异常 "#错误的配置与看到的异常")错误的配置与看到的异常

1.  配置文件中的配置，看上去没啥问题

        <bean id="sqlSessionFactory" class="org.mybatis.spring.SqlSessionFactoryBean">
            <property name="dataSource" ref="dataSourceM"/>
            <property name="mapperLocations" value="classpath*:/mappings/*.xml"/>
            <property name="configLocation" value="classpath*:/spring/mybatis-config.xml"></property>
        </bean>

2.  启动服务器之后看到的异常

        Caused by: java.io.FileNotFoundException: Could not open ServletContext resource [/classpath*:/spring/mybatis-config.xml]
            at org.springframework.web.context.support.ServletContextResource.getInputStream(ServletContextResource.java:141)
            at org.mybatis.spring.SqlSessionFactoryBean.buildSqlSessionFactory(SqlSessionFactoryBean.java:358)
            at org.mybatis.spring.SqlSessionFactoryBean.afterPropertiesSet(SqlSessionFactoryBean.java:340)
            at org.springframework.beans.factory.support.AbstractAutowireCapableBeanFactory.invokeInitMethods(AbstractAutowireCapableBeanFactory.java:1687)
            at org.springframework.beans.factory.support.AbstractAutowireCapableBeanFactory.initializeBean(AbstractAutowireCapableBeanFactory.java:1624)
            ... 61 more

3.  分析异常，解决问题

从上面的异常可以看出来，文件很明显是找不到的，但是这是为啥呢？

从异常中可以看出来，spring查找的路径是：

    然而这个路径根本不是我们想要的路径，显然是找错了地方。

    但是我们配置文件给出的路径是：``` classpath*:/spring/mybatis-config.xml

我们将配置文件中下面的配置稍作修改，去掉classpath后面的 \*\

    <property name="configLocation" value="classpath*:/spring/mybatis-config.xml"></property>

改为：

    <property name="configLocation" value="classpath*:/spring/mybatis-config.xml"></property>

之后，启动正常，没有报错，问题解决。到这里可能有的同学会说为啥 `<property name="mapperLocations" value="classpath*:/mappings/*.xml"/>`可以用`classpath*`呢？原因请看下面

## [](#classpath-和-classpath的区别： "#classpath-和-classpath的区别：")classpath\* 和 classpath的区别：

1.  `classpath*` 它会搜索所有的 classpath，找到所有符合条件的文件，包括当前项目依赖的jar文件中的配置文件。而`classpath`不会到当前项目依赖的jar文件中去寻找。

2.  classpath\* 存在可移植性问题，遇到问题时，应该使用classpath.

3.  一般情况下我们根本没有必要去使用classpath\*，直接使用classpath就好了。

## [](#号外 "#号外")号外

楼主造了一个轮子，LIGHTCONF 是一个基于Netty实现的一个配置管理平台，其核心设计目标是“为业务提供统一的配置管理服务”，可以做到开箱即用。

- <a href="https://link.juejin.cn?target=https%3A%2F%2Fgithub.com%2FhaifeiWu%2Flightconf" target="_blank" data-ref="nofollow noopener noreferrer" title="https://github.com/haifeiWu/lightconf">基于Netty实现的轻量级分布式应用配置中心</a>
