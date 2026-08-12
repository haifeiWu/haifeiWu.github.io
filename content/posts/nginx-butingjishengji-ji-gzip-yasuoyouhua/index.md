---
aliases: ["/zh-cn/posts/nginx-butingjishengji-ji-gzip-yasuoyouhua/"]
categories: ["后端"]
title: "Nginx 不停机升级 及 gzip 压缩优化"
date: "2018-11-14T10:04:53+08:00"
tags: ["Nginx", "后端", "百度"]
summary: "好久不写博客手都生了，不过这个习惯不能丢，仅以一篇水文记录一下 Nginx 不停机版本升级及配置 gzip 压缩优化网站访问体验过程。何为水文，楼主对水文的定义就是百度一搜一大把，但是始终比较杂乱，需要自己仔细甄别才能真正解决问题，这也是楼主写这篇文章的原因，记录一下这个过程…"
translationKey: "nginx-butingjishengji-ji-gzip-yasuoyouhua"
---

> 📌 本文原发布于掘金社区：[Nginx 不停机升级 及 gzip 压缩优化](https://juejin.cn/post/6844903713270824967)

> 原文地址：<a href="https://link.juejin.cn?target=https%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2018%2Fca%2F%3F_ref%3Djuejin" target="_blank" data-ref="nofollow noopener noreferrer" title="https://www.hchstudio.cn/article/2018/ca/?_ref=juejin">haifeiWu 和他朋友们的博客</a>\
> 博客地址：<a href="https://link.juejin.cn?target=https%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2018%2Fca%2F%3F_ref%3Djuejin" target="_blank" data-ref="nofollow noopener noreferrer" title="https://www.hchstudio.cn/article/2018/ca/?_ref=juejin">www.hchstudio.cn</a>\
> 欢迎转载，转载请注明作者及出处，谢谢！

好久不写博客手都生了，不过这个习惯不能丢，仅以一篇水文记录一下 Nginx 不停机版本升级及配置 gzip 压缩优化网站访问体验的过程。

## 缘起

何为水文，楼主对水文的定义就是百度一搜一大把，但是始终比较杂乱，需要自己仔细甄别才能真正解决问题，这也是楼主写这篇文章的原因，记录一下这个过程，也留给以后自己查阅，也分享给有需要的小伙伴。

## 开篇

### Nginx 不停机升级

**1. 下载稳定版本的 Nginx**

``` bash
wget http://nginx.org/download/nginx-1.14.1.tar.gz
```

**2. 编译 Nginx**

注意编译的时候不要执行 `make install`。

``` bash
# 解压
tar -zxvf nginx-1.14.1.tar.gz
# 编译Nginx
cd nginx-1.14.1
# 配置编译要加载的模块
./configure --with-http_ssl_module
# 执行编译，切记不要make install
make
```

**3. 备份原来的 `nginx` 脚本，替换成编译新生成的**

备份完原来的数据之后，执行下面的脚本，覆盖 `ngxin` 可执行程序。

``` bash
cp -rfp objs/nginx /usr/local/nginx/sbin/
```

**4. 执行升级**

下面的命令应该在最开始的 `make` 的目录下执行。

``` bash
make upgrade
```

### 配置 Nginx 的 gzip 压缩

这个配置比较简单，修改 `nginx.conf` 文件添加如下内容即可。

``` bash
gzip on;                     # 开启Gzip
gzip_min_length  1k;         # 不压缩临界值，大于1K的才压缩
gzip_buffers     4 16k;      
gzip_comp_level 8;           # 压缩级别

# 进行压缩的文件类型
gzip_types       text/plain application/x-javascript text/css application/xml text/javascript application/x-httpd-php image/jpeg image/gif image/png;
gzip_vary on;
```

然后重启一下 `Nginx` 就可以了

``` bash
./nginx -s reload
```

## 终章

当然除了 `gzip` 可以实现压缩之外还有一种 `Google` 爸爸加持的更强悍的压缩算法，名字叫 `brotli`，有时间可以再搞一下。

<figure>
<img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/mirror-assets/-temp/15415875969165118d~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp" loading="lazy" alt="关注我们" />
</figure>
