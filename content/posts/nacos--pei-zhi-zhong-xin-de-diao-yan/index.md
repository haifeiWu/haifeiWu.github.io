---
categories: ["Java"]
title: "Nacos 配置中心的调研"
date: "2019-03-15T00:00:00+08:00"
tags: ["Nacos", "配置中心", "微服务"]
summary: "进一步减少不必要的重复工作，最近打算在把之前的项目重构成 SpringBoot 项目之后，源于 N 台机器配置的管理甚是麻烦，所以便有了进一步将项目的配置进行统一的管理的需求。  是什么？ Nacos 致力于帮助您发现、配置和管理微服务。N"
translationKey: "nacos--pei-zhi-zhong-xin-de-diao-yan"
---

> 📌 本文原发布于代码星冰乐：[Nacos 配置中心的调研](https://changhuin.github.io/article/2019/b0af/)

进一步减少不必要的重复工作，最近打算在把之前的项目重构成 SpringBoot 项目之后，源于 N 台机器配置的管理甚是麻烦，所以便有了进一步将项目的配置进行统一的管理的需求。\

## 是什么？

<a href="https://nacos.io/zh-cn/docs/what-is-nacos.html" target="_blank" rel="noopener">Nacos</a> 致力于帮助您发现、配置和管理微服务。Nacos 提供了一组简单易用的特性集，帮助您快速实现动态服务发现、服务配置、服务元数据及流量管理。Nacos 帮助您更敏捷和容易地构建、交付和管理微服务平台。

Nacos 是构建以“服务”为中心的现代应用架构 (例如微服务范式、云原生范式) 的服务基础设施。本文调研的主要是 Nacos 的配置中心的功能。

## 如何安装 Nacos

Nacos 通过下载发行包或者编译源码包来获取。

### 从 Github 上下载源码方式

    git clone https://github.com/alibaba/nacos.git
    cd nacos/ 
    mvn -Prelease-nacos clean install -U
    ls -al distribution/target/ 
    // change the $version to your actual path 
    cd distribution/target/nacos-server-$version/nacos/bin
    `

### 下载编译后压缩包方式

您可以从 <a href="https://github.com/alibaba/nacos/releases" target="_blank" rel="noopener">最新稳定版本</a> 下载 nacos-server-\$version.zip 包。

    unzip nacos-server-$version.zip 或者 tar -xvf nacos-server-$version.tar.gz
    cd nacos/bin

### 启动 Nacos

**Linux/Unix/Mac**\
启动命令(standalone代表着单机模式运行，非集群模式):\

    sh startup.sh -m standalone

**Windows**\
启动命令：\

    cmd startup.cmd

或者双击startup.cmd运行文件。

## Springboot 下使用 Nacos 配置中心

新建 springboot 的 web项目，可以通过 <a href="https://start.spring.io/" target="_blank" rel="noopener">SpringBoot start</a> 来新建。并添加 Nacos 的配置中心依赖。

    <dependency>      
        <groupId>com.alibaba.boot</groupId>      
        <artifactId>nacos-config-spring-boot-starter</artifactId>      
        <version>0.2.1</version>
    </dependency>

创建 Controller 并添加 Nacos 的配置注解。

    /**
     * @author wuhf
     * @Date 2019/3/14 19:28
     **/
    @NacosPropertySource(dataId = "goocity-test", groupId = "goocity-test",autoRefreshed = true)
    @RestController
    public class HelloController {
        @NacosValue(value = "${bus.pay.udids:null}", autoRefreshed = true)
        private String busPayUdid;

        @GetMapping("/hello")
        public String test() {
            System.out.println(busPayUdid);
            return busPayUdid;
        }
    }

## 小结

本文总的来说写的比较流水账，主要记录一下使用 Nacos 作为配置中心时的过程，共勉……

