---
categories: ["后端"]
title: "自建脚手架之配置中心--LightConf 的实现"
date: "2018-04-22T18:39:29+08:00"
tags: ["GitHub", "后端", "服务器", "Nginx"]
summary: "在经历了一个多月的开发后，项目的第一个稳定版本终于完成，开源地址https://github.com/haifeiWu/lightconf，欢迎各路大神star，拍砖。 LIGHTCONF 使用了 Netty 实现底层通讯，保证配置的实时生效。接入 LIGHTCONF 事只需要添加 mav…"
translationKey: "zijianjiaoshoujiazhipeizhizhongxin-lightconfdeshixian"
---

> 📌 本文原发布于掘金社区：[自建脚手架之配置中心--LightConf 的实现](https://juejin.cn/post/6844903596937445383)

> 常规项目开发过程中，通常会将配置信息放在项目 resource 目录下的 properties 文件中，配置信息通常包括：JDBC 地址配置、Redis 地址配置、活动开关等等。因此每次上线或者服务迁移的时候都要手动修改配置，并一台一台地重启服务器，甚是麻烦，且费时费力。\
> 于是便萌生出了使用配置中心的想法，在考察了 github 上的 apoll，xxl-conf 等开源项目后，感觉都不适合我司的应用模型，于是决定自研一套符合自己需求的配置中心，因此 LightConf 便应运而生，当然 LightConf 也借鉴了 apoll，xxl-conf 的部分代码实现。

## 项目开源地址

- 在经历了一个多月的开发后，项目的第一个稳定版本终于完成，开源地址<a href="https://link.juejin.cn?target=https%3A%2F%2Fgithub.com%2FhaifeiWu%2Flightconf" target="_blank" data-ref="nofollow noopener noreferrer" title="https://github.com/haifeiWu/lightconf">github.com/haifeiWu/li…</a>，欢迎各路大神 star，拍砖。
- LIGHTCONF 使用了 Netty 实现底层通讯，保证配置的实时生效。接入 LIGHTCONF 时只需要添加 Maven 依赖，简单配置即可马上上手，学习零成本。

## 一、简介

### 1.1 概述

LIGHTCONF 是一个基于 Netty 实现的配置管理平台，其核心设计目标是“为业务提供统一的配置管理服务”，可以做到开箱即用。

### 1.2 特性

- 1、简单易用：上手非常简单，只需要引入 Maven 依赖和一行配置即可；
- 2、在线管理：提供配置管理中心，支持在线管理配置信息；
- 3、实时推送：配置信息更新后，实时推送配置信息，项目中配置数据会实时更新并生效，不需要重启线上机器；
- 4、配置备份：配置数据会在 MySQL 中对配置信息做备份，保证配置数据的安全性；

### 1.3 背景

> why not properties

常规项目开发过程中，通常会将配置信息放在项目 resource 目录下的 properties 文件中，配置信息通常包括：JDBC 地址配置、Redis 地址配置、活动开关、阈值配置、黑白名单等等。使用 properties 维护配置信息将会导致以下几个问题：

- 1、需要手动修改 properties 文件；
- 2、需要重新编译打包；
- 3、需要重启线上服务器 (项目集群时，更加令人崩溃) ;
- 4、配置生效不及时：因为流程复杂，新的配置生效需要经历比较长的时间；
- 5、不同环境上线包不一致：例如 JDBC 连接，不同环境需要差异化配置；

> why LIGHTCONF

- 1、不需要 (手动修改 properties 文件) : 在配置管理中心提供的 Web 界面中，定位到指定配置项，输入配置的新值，点击更新按钮即可；
- 2、不需要 (重新编译打包) : 配置更新后，实时推送新配置信息至项目中，不需要编译打包；
- 3、不需要 (重启线上服务器) : 配置更新后，实时推送新配置信息至项目中，实时生效，不需要重启线上机器；
- 4、配置生效 "非常及时" : 点击更新按钮，新的配置信息将会即刻推送到项目中，瞬间生效，非常及时。比如一些开关类型的配置，配置变更后，将会立刻推送至项目中并生效，相对常规配置修改的繁琐流程，及时性可谓天壤之别；

#### 项目在线预览地址

| 配置中心预览 | 接入 LIGHTCONF 的 Demo 项目预览 |
|----|----|
| http://www.whforever.cn/lightconf-admin-web/ | http://www.whforever.cn/lightconf-sample/ |

#### 源码仓库地址

| 源码仓库地址 | Release Download |
|----|----|
| <a href="https://link.juejin.cn?target=https%3A%2F%2Fgithub.com%2FhaifeiWu%2Flightconf" target="_blank" data-ref="nofollow noopener noreferrer" title="https://github.com/haifeiWu/lightconf">github.com/haifeiWu/li…</a> | <a href="https://link.juejin.cn?target=https%3A%2F%2Fgithub.com%2FhaifeiWu%2Flightconf%2Freleases" target="_blank" data-ref="nofollow noopener noreferrer" title="https://github.com/haifeiWu/lightconf/releases">Download</a> |

### 1.5 环境

- Maven3+
- Jdk1.7+
- Tomcat7+
- Mysql5.5+

## 二、快速入门

### 2.1 初始化“数据库”

请下载项目源码并解压，获取 "调度数据库初始化 SQL 脚本" 并执行即可。脚本位置如下：

    lightconf/doc/db/light-conf-0.1.1V.sql

### 2.2 编译源码

解压源码，按照 Maven 格式将源码导入 IDE, 使用 Maven 编译即可

- lightconf-admin：配置管理中心
- lightconf-core：公共依赖
- lightconf-common：公共依赖
- lightconf-sample: 接入 LIGHTCONF 的 Demo 项目

### 2.3 “配置管理中心” 项目配置

    项目：lightconf-admin
    作用：管理线上配置信息

配置文件位置：

    lightconf/lightconf-admin/lightconf-admin-web/src/main/resources/light-conf.properties

配置项说明：

    # 配置登录lightconf的用户名，密码
    light.conf.login.username=admin
    light.conf.login.password=123456

    # mysql database setting
    jdbc.type=mysql
    jdbc.driver=com.mysql.jdbc.Driver

    jdbc.url=jdbc:mysql://localhost:3306/light-conf?useUnicode=true&characterEncoding=utf-8
    jdbc.username=root
    jdbc.password=root_pwd

    # pool settings
    jdbc.pool.init=2
    jdbc.pool.minIdle=3
    jdbc.pool.maxActive=20

    # jdbc.testSql=SELECT 'x'
    jdbc.testSql=SELECT 'x' FROM DUAL

    # 服务端启动监听端口
    netty.server.port=9998

### 2.4 “接入 LIGHTCONF 的示例项目” 项目配置

    项目：lightconf-sample
    作用：接入LIGHTCONF的示例项目，供用户参考学习

#### A、引入 Maven 依赖

    <!-- lightconf-client -->
    <dependency>
        <groupId>com.lightconf</groupId>
        <artifactId>lightconf-core</artifactId>
        <version>${project.parent.version}</version>
    </dependency>

#### B、添加 LIGHTCONF 配置文件

    可参考配置文件：
    lightconf/lightconf-sample/src/main/resources/light-conf.properties

    配置项说明:

    # 连接light-conf-admin的IP地址
    light.conf.host=127.0.0.1
    # 连接light-conf-admin的端口号
    light.conf.port=9998

    ## 接入应用的uuid
    application.uuid=8705d6c8-bbe0-420c-9853-f780de4cb5ea

#### C、LIGHTCONF 配置初始化\[必须\]

    可参考配置文件：

    lightconf/lightconf-sample/src/main/resources/spring/applicationcontext-light-conf.xml

    配置项说明：

    <!-- ********************************* 核心配置[必须]：LIGHTCONF 配置 ********************************* -->
    <bean id="xxlConf" class="com.lightconf.core.spring.LightConfFactory" init-method="init" destroy-method="destroy" />

    <!-- ********************************* 核心配置[必须]：LIGHTCONF netty client监听 ********************************* -->
    <bean id="lightConfListener" class="com.lightconf.core.listener.LightConfClientListener"></bean>

## 三、配置管理中心操作指南

### 3.1、应用管理

系统以 “应用” 为维度进行配置隔离。可进入 "配置管理界面" 操作和维护应用，应用属性说明如下：

- UUID:每个应用拥有唯一的 UUID,作为应用标识。
- 应用名称：该应用的名称；

<figure>
<img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/5/22/1638587b1ba44686~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp" loading="lazy" alt="light-conf-app" />
<figcaption aria-hidden="true">light-conf-app</figcaption>
</figure>

### 3.2 配置管理

进入"配置管理" 界面，选择应用，然后可查看和操作该应用下配置数据，同时也可以通过应用管理页面的"应用配置信息"的 button 来进入该应用的配置信息页面，如下图所示。

<figure>
<img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/5/22/1638587b1b5630fe~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp" loading="lazy" alt="light-conf-conf" />
<figcaption aria-hidden="true">light-conf-conf</figcaption>
</figure>

新增配置：点击 "新增配置" 按钮可添加配置数据，配置属性说明如下：

- KEY:配置的 KEY,创建时将会自动添加所属项目的 APPName 作为前缀，生成最终的 Key。可通过客户端使用最终的 Key 获取配置；
- 描述：该配置的描述信息；
- VALUE：配置的值；
