---
aliases: ["/zh-cn/posts/duoyingyongpeizhiguanlipingtailightconf/"]
categories: ["后端"]
title: "多应用配置管理平台 LIGHTCONF"
date: "2018-05-07T20:42:14+08:00"
tags: []
summary: "LIGHTCONF 是一个配置管理平台，其核心设计目标是“为业务提供统一的配置管理服务”。"
translationKey: "duoyingyongpeizhiguanlipingtailightconf"
---

> 📌 本文原发布于掘金社区：[多应用配置管理平台 LIGHTCONF](https://juejin.cn/post/6844903602985680909)

## <a href="#多应用配置管理平台lightconf" id="user-content-user-content-多应用配置管理平台lightconf" title="#多应用配置管理平台lightconf"></a>《多应用配置管理平台 LIGHTCONF》

<a href="https://link.juejin.cn?target=https%3A%2F%2Ftravis-ci.org%2FhaifeiWu%2Flightconf" target="_blank" data-ref="nofollow noopener noreferrer" title="https://travis-ci.org/haifeiWu/lightconf"><img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/5/7/1633a9fc93127cca~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp" data-canonical-src="https://travis-ci.org/haifeiWu/lightconf.svg?branch=master" loading="lazy" alt="Build Status" /></a> <a href="https://link.juejin.cn?target=https%3A%2F%2Fgithub.com%2FhaifeiWu%2Flightconf%2Freleases" target="_blank" data-ref="nofollow noopener noreferrer" title="https://github.com/haifeiWu/lightconf/releases"><img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/5/7/1633a9fc92fb984f~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp" data-canonical-src="https://img.shields.io/github/release/haifeiWu/lightconf.svg" loading="lazy" alt="GitHub release" /></a> <a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.gnu.org%2Flicenses%2Fgpl-3.0.html" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.gnu.org/licenses/gpl-3.0.html"><img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/5/7/1633a9fc930e94a7~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp" data-canonical-src="https://img.shields.io/badge/license-GPLv3-blue.svg" loading="lazy" alt="License" /></a>

## <a href="#一简介" id="user-content-user-content-一简介" title="#一简介"></a>一、简介

### <a href="#11-概述" id="user-content-user-content-11-概述" title="#11-概述"></a>1.1 概述

LIGHTCONF 是一个配置管理平台，其核心设计目标是“为业务提供统一的配置管理服务”。

### <a href="#12-特性" id="user-content-user-content-12-特性" title="#12-特性"></a>1.2 特性

- 1、简单易用：上手非常简单，只需要引入 Maven 依赖和一行配置即可；
- 2、在线管理：提供配置管理中心，支持在线管理配置信息；
- 3、实时推送：配置信息更新后，实时推送配置信息，项目中配置数据会实时更新并生效，不需要重启线上机器；
- 4、配置备份：配置数据会在 MySQL 中对配置信息做备份，保证配置数据的安全性；

### <a href="#13-背景" id="user-content-user-content-13-背景" title="#13-背景"></a>1.3 背景

> why not properties

常规项目开发过程中，通常会将配置信息放在项目 resource 目录下的 properties 文件中，配置信息通常包括：JDBC 地址配置、Redis 地址配置、活动开关、阈值配置、黑白名单……等等。使用 properties 维护配置信息将会导致以下几个问题：

- 1、需要手动修改 properties 文件；
- 2、需要重新编译打包；
- 3、需要重启线上服务器 (项目集群时，更加令人崩溃) ;
- 4、配置生效不及时：因为流程复杂，新的配置生效需要经历比较长的时间才可以生效；
- 5、不同环境上线包不一致：例如 JDBC 连接，不同环境需要差异化配置；

> why LIGHTCONF

- 1、不需要 (手动修改 properties 文件) : 在配置管理中心提供的 Web 界面中，定位到指定配置项，输入新的配置值，点击更新按钮即可；
- 2、不需要 (重新编译打包) : 配置更新后，实时推送新配置信息至项目中，不需要编译打包；
- 3、不需要 (重启线上服务器) : 配置更新后，实时推送新配置信息至项目中，实时生效，不需要重启线上机器；
- 4、配置生效 "非常及时" : 点击更新按钮，新的配置信息即可推送到项目中，瞬间生效，非常及时。比如一些开关类型的配置，配置变更后，将会立刻推送至项目中并生效，相对常规配置修改繁琐的流程，及时性可谓天壤之别；

#### <a href="#项目在线预览地址" id="user-content-user-content-项目在线预览地址" title="#项目在线预览地址"></a>项目在线预览地址

| 配置中心预览 | 接入 LIGHTCONF 的 Demo 项目预览 |
|----|----|
| <a href="https://link.juejin.cn?target=http%3A%2F%2F58.87.84.211%2Flightconf-admin-web%2FtoLogin" target="_blank" data-ref="nofollow noopener noreferrer" title="http://58.87.84.211/lightconf-admin-web/toLogin">http://58.87.84.211/lightconf-admin-web/toLogin</a> | <a href="https://link.juejin.cn?target=http%3A%2F%2F58.87.84.211%2Flightconf-sample%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://58.87.84.211/lightconf-sample/">http://58.87.84.211/lightconf-sample/</a> |

#### <a href="#源码仓库地址" id="user-content-user-content-源码仓库地址" title="#源码仓库地址"></a>源码仓库地址

| 源码仓库地址 | Release Download |
|----|----|
| <a href="https://link.juejin.cn?target=https%3A%2F%2Fgithub.com%2FhaifeiWu%2Flightconf" target="_blank" data-ref="nofollow noopener noreferrer" title="https://github.com/haifeiWu/lightconf">github.com/haifeiWu/li…</a> | <a href="https://link.juejin.cn?target=https%3A%2F%2Fgithub.com%2FhaifeiWu%2Flightconf%2Freleases" target="_blank" data-ref="nofollow noopener noreferrer" title="https://github.com/haifeiWu/lightconf/releases">Download</a> |

### <a href="#15-环境" id="user-content-user-content-15-环境" title="#15-环境"></a>1.5 环境

- Maven3+
- Jdk1.7+
- Tomcat7+
- Mysql5.5+

## <a href="#二快速入门" id="user-content-user-content-二快速入门" title="#二快速入门"></a>二、快速入门

### <a href="#21-初始化数据库" id="user-content-user-content-21-初始化数据库" title="#21-初始化数据库"></a>2.1 初始化“数据库”

请下载项目源码并解压，获取 "调度数据库初始化 SQL 脚本" 并执行即可。脚本位置如下：

    lightconf/doc/db/light-conf-0.1.1V.sql

### <a href="#22-编译源码" id="user-content-user-content-22-编译源码" title="#22-编译源码"></a>2.2 编译源码

解压源码，按照 Maven 格式将源码导入 IDE, 使用 Maven 进行编译即可

- lightconf-admin：配置管理中心
- lightconf-core：公共依赖
- lightconf-common：公共依赖
- lightconf-sample: 接入 LIGHTCONF 的 Demo 项目

### <a href="#23-配置管理中心-项目配置" id="user-content-user-content-23-配置管理中心-项目配置" title="#23-配置管理中心-项目配置"></a>2.3 “配置管理中心” 项目配置

    项目：lightconf-admin
    作用：管理线上配置信息

配置文件位置：

    lightconf/lightconf-admin/lightconf-admin-web/src/main/resources/light-conf.properties

配置项目说明：

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

### <a href="#24-接入lightconf的示例项目-项目配置" id="user-content-user-content-24-接入lightconf的示例项目-项目配置" title="#24-接入lightconf的示例项目-项目配置"></a>2.4 “接入 LIGHTCONF 的示例项目” 项目配置

    项目：lightconf-sample
    作用：接入LIGHTCONF的示例项目，供用户参考学习

#### <a href="#a引入maven依赖" id="user-content-user-content-a引入maven依赖" title="#a引入maven依赖"></a>A、引入 Maven 依赖

    <!-- lightconf-client -->
    <dependency>
        <groupId>com.lightconf</groupId>
        <artifactId>lightconf-core</artifactId>
        <version>${project.parent.version}</version>
    </dependency>

#### <a href="#b添加-lightconf-配置文件" id="user-content-user-content-b添加-lightconf-配置文件" title="#b添加-lightconf-配置文件"></a>B、添加 LIGHTCONF 配置文件

    可参考配置文件：
    lightconf/lightconf-sample/src/main/resources/light-conf.properties

    配置项说明:

    # 连接light-conf-admin的IP地址
    light.conf.host=127.0.0.1
    # 连接light-conf-admin的端口号
    light.conf.port=9998

    ## 接入应用的uuid
    application.uuid=8705d6c8-bbe0-420c-9853-f780de4cb5ea

#### <a href="#clightconf-配置初始化必须" id="user-content-user-content-clightconf-配置初始化必须" title="#clightconf-配置初始化必须"></a>C、LIGHTCONF 配置初始化\[必须\]

    可参考配置文件：

    lightconf/lightconf-sample/src/main/resources/spring/applicationcontext-light-conf.xml

    配置项说明：

    <!-- ********************************* 核心配置[必须]：LIGHTCONF 配置 ********************************* -->
    <bean id="xxlConf" class="com.lightconf.core.spring.LightConfFactory" init-method="init" destroy-method="destroy" />

    <!-- ********************************* 核心配置[必须]：LIGHTCONF netty client监听 ********************************* -->
    <bean id="lightConfListener" class="com.lightconf.core.listener.LightConfClientListener"></bean>
