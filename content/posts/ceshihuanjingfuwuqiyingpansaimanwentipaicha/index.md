---
categories: ["后端"]
title: "测试环境服务器硬盘塞满问题排查"
date: "2018-03-12T18:06:57+08:00"
tags: ["服务器", "后端", "Linux", "Nginx"]
summary: "某天下午测试环境服务器出现 tab 无法补全命令，给出的提示大概意思就是说，无可用空间无法创建临时文件，不过这次跟上次出现的问题比较像，上次服务器出现的问题，因此楼主判断可能是服务器数据盘被占满，果不其然，使用 df -h 命令看到服务器数据盘出现 100%被占用的情况。楼主首先想到的…"
---

> 📌 本文原发布于掘金社区：[测试环境服务器硬盘塞满问题排查](https://juejin.cn/post/6844903574837657608)

## 项目中出现的问题

<a href="https://link.juejin.cn?target=http%3A%2F%2Fblog.csdn.net%2Fgithub_36379934%2Farticle%2Fdetails%2F79530397" target="_blank" data-ref="nofollow noopener noreferrer" title="http://blog.csdn.net/github_36379934/article/details/79530397">文章出处</a>

某天下午测试环境服务器出现 tab 无法补全命令，给出的提示大概意思就是说，**无可用空间无法创建临时文件**，不过这次跟上次出现的问题比较像，<a href="https://link.juejin.cn?target=http%3A%2F%2Fblog.csdn.net%2Fgithub_36379934%2Farticle%2Fdetails%2F78754980" target="_blank" data-ref="nofollow noopener noreferrer" title="http://blog.csdn.net/github_36379934/article/details/78754980">上次服务器出现的问题</a>，因此楼主判断可能是服务器数据盘被占满，果不其然，使用`df -h`命令看到服务器数据盘出现 100%被占用的情况。

## 问题排查过程

楼主首先想到的是查看 Linux 系统中占用数据盘最大的文件，通常情况下，最有可能找出占用磁盘空间的文件或文件夹的地方，主要是 `/tmp or /var or /home or /`。目前没有单个命令来完成查找的工作，通常可以使用一些命令的组合来帮助您找出磁盘上比较占用空间的文件或者文件夹。主要用到下面的三个命令：

- du : 计算出单个文件或者文件夹的磁盘空间占用。
- sort : 对文件行或者标准输出行记录排序后输出。
- head : 输出文件内容的前面部分。

用下面的命令组合就可以完成上述查找工作：

``` bash
du -h / | sort -n -r | head -n 10
```

上述命令的含义就是查找`/`目录下按照大小排序占用磁盘空间最大的 10 个文件。

如果需要输出可读性更高的内容，请使用如下命令：

``` bash
du -hsx * | sort -rh | head -10
```

ok，到此为止问题华丽丽地解决了，很开心哦。

## 分享一个命令的使用

### lsof -i

在使用 Linux 系统的过程中，有时候会遇到端口被占用而导致服务无法启动的情况。比如 HTTP 使用 80 端口，但当启动 Nginx 时，却发现此端口正在使用。

这种情况大多数是由于软件冲突、或者默认端口设置不正确导致的，此时需要查看究竟哪个进程占用了端口，来决定进一步的处理方法。

一般情况下查看某一端口的占用情况的用法是：`lsof -i:端口号` 例如查看 80 端口的使用情况

``` bash
lsof -i:80
COMMAND  PID   USER   FD   TYPE  DEVICE SIZE/OFF NODE NAME
java    7464   root  272u  IPv6 7111192      0t0  TCP 192.168.201.8:45616->192.168.201.8:http (CLOSE_WAIT)
nginx   7555   root    7u  IPv4 7110265      0t0  TCP *:http (LISTEN)
nginx   7556 nobody    7u  IPv4 7110265      0t0  TCP *:http (LISTEN)
java    7573   root  210u  IPv6 7110330      0t0  TCP 192.168.201.8:45422->192.168.201.8:http (CLOSE_WAIT)
java    7602   root  140u  IPv6 7111090      0t0  TCP 192.168.201.8:45412->192.168.201.8:http (CLOSE_WAIT)
```

结束该端口的占用可以使用`kill pid`的方法。
