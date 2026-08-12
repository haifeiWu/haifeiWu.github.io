---
categories: ["后端"]
title: "线上问题解决及 shell 脚本实现自动保留最近 n 次备份记录"
date: "2017-12-08T20:12:19+08:00"
tags: ["后端", "Shell"]
summary: "某天上午服务器出现卡顿特别严重，页面加载速度奇慢，并且某些页面刷新出现 404 的问题，就连服务器的 tab 命令的自动提示都出现了问题，楼主费了九牛二虎之力，根据服务器排查发现，服务器数据盘出现 100%被占用的问题，导致该问题出现的原因是，Jenkins 每次部署服务器的时候，都会自动…"
translationKey: "xianshangwentijiejuejishelljiaobenshixianzidongbaoliuzuijinn"
---

> 📌 本文原发布于掘金社区：[线上问题解决及 shell 脚本实现自动保留最近 n 次备份记录](https://juejin.cn/post/6844903520324288526)

# 项目中出现的问题

某天上午服务器出现卡顿特别严重，页面加载速度奇慢，并且某些页面刷新出现 404 的问题，就连服务器的 tab 命令的自动提示都出现了问题，楼主费了九牛二虎之力，根据服务器排查发现，服务器数据盘出现 100%被占用的问题，导致该问题出现的原因是，Jenkins 每次部署服务器的时候，都会自动将上一次的 war 备份，由于开发阶段的频繁部署，最终硬盘被占满，便出现上述描述的情况。

# 解决方案的实现过程

## 获取备份文件夹下的所有文件

根据 Google 爸爸的提示，楼主找到了下面的命令，

``` bash
find 对应目录 -mtime +天数 -name "文件名" -exec rm -rf {} \;
```

实例命令：

``` bash
find /opt/soft/log/ -mtime +30 -name "*.log" -exec rm -rf {} \;
```

**说明：**

将/opt/soft/log/目录下所有 30 天前带".log"的文件删除。

**具体参数说明如下：**

find：Linux 的查找命令，用户查找指定条件的文件；/opt/soft/log/：想要进行清理的任意目录；-mtime：标准语句写法；+30：查找 30 天前的文件，这里用数字代表天数；" ×.log"：希望查找的数据类型，"×.jpg"表示查找扩展名为 jpg 的所有文件，"×"表示查找所有文件，这个可以灵活运用，举一反三；-exec：固定写法；rm -rf：强制删除文件，包括目录；{} ;：固定写法，一对大括号+空格++;

**解决问题的思路：**

当然楼主当然不能傻乎乎的将备份目录下的所有文件都删除掉，这样的话，备份不就失去了意义。所以换一下思路便有了下面的命令

``` bash
find ${BAK_HOME} -mtime +1 -name "*:*" | wc -l
```

**说明：**

获取备份目录下所有一天前带"："的所有文件数量。

``` bash
find ${BAK_HOME} -mtime +1 -name "*:*"
```

**说明：**

获取备份目录下所有一天前带”：”的所有文件数量。

到了这里我们的问题差不多就可以解决了。so，请接着往下看：

## 解决方案的思路及 shell 脚本的实现

## 思路

目前解决该问题的方法是在原来部署脚本中添加一段脚本，实现保留最近 10 次部署的备份记录，超过 10 次的备份记录将被删除。

## shell 脚本的实现

逻辑很清晰，思路很明了，我就不在这里接着阐述了，谢谢大家！

``` bash
#!/bin/sh
BAK_HOME="/home/saveHistoryData/iam-share-8083"

keepNum=5
fileNum=$(find ${BAK_HOME} -mtime +1 -name "*:*" | wc -l)

echo "${fileNum}"

for file in $(find ${BAK_HOME} -mtime +1 -name "*:*"); do
    if test $[fileNum] -gt $[keepNum];then
       rm -rf ${file}
       fileNum=${fileNum}-1
       echo "delete backup file"
    else
       echo "do no thing"
    fi
done 
```
