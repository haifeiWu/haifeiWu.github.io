---
categories: ["后端"]
title: "I-team 博客的 gitlab-runner 持续集成实践"
date: "2018-06-10T23:34:27+08:00"
tags: ["Hexo", "GitLab", "Travis CI", "Node.js", "Linux"]
summary: "作为一个略微看过 nodejs 语法，但又不懂 nodejs 的攻城狮，搭建 Hexo 环境很是麻烦，要考虑到翻墙、版本兼容等问题。于是乎，博主每换一个电脑，为了能继续发博客，都需要在新电脑上花一天时间重新搞一下 Hexo 环境，楼主感觉还是有简洁的方案来实现我一提交代码就可以自动发布博客。"
---

> 📌 本文原发布于掘金社区：[I-team 博客的 gitlab-runner 持续集成实践](https://juejin.cn/post/6844903618852683789)

作为一个略微看过 nodejs 语法，但又不懂 nodejs 的攻城狮，搭建 Hexo 环境很是麻烦，要考虑到翻墙、版本兼容等问题。于是乎，博主每换一个电脑，为了能继续发博客，都需要在新电脑上花一天时间重新搞一下 Hexo 环境，楼主感觉还是有简洁的方案来实现我一提交代码就可以自动发布博客，不需要再手动操作一波，这样岂不美哉。so，也就有了今天的经历，代码可以持续集成，博客也可以。楼主的解决方案是使用 GitLab 与 gitlab-runner 实现博客部署的持续集成，效果真的不要太好。\
<span id="user-content-more"></span>

## [](#持续集成工具-gitlab-runner-介绍 "#持续集成工具-gitlab-runner-介绍")持续集成工具 gitlab-runner 介绍

gitlab-ci 的全称是 GitLab continuous integration，也就是持续集成。中心思想是每当 push 到 GitLab 的时候，都会触发一次脚本执行，然后脚本的内容包括了测试，编译，部署等一系列自定义内容。而 gitlab-runner 是 GitLab 提供的持续集成工具。

简单地说，要让 CI 工作，可总结为以下几点：

- 在仓库根目录创建一个名为.gitlab-ci.yml 的文件。
- 为该项目配置一个 runner 服务，楼主这里是使用 GitLab 提供的代码仓库，在自己的腾讯云服务器上运行 gitlab-runner 服务。
- 完成上面的步骤后，每次 push 代码到 Git 仓库，runner 就会自动开始 pipeline。

gitlab-ci 的具体部署流程如下图所示（图来自网络，侵权删）\
<a href="https://link.juejin.cn?target=http%3A%2F%2Fimg.hchstudio.cn%2Fgitlab-runner.png" target="_blank" data-ref="nofollow noopener noreferrer" title="http://img.hchstudio.cn/gitlab-runner.png"><img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/6/10/163ea55d4644c2b8~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.png" loading="lazy" alt="gitlab-runner" /></a>gitlab-runner

## [](#Hexo-博客环境迁移 "#Hexo-博客环境迁移")Hexo 博客环境迁移

### [](#迁移前版本控制 "#迁移前版本控制")迁移前版本控制

其实每个 nodejs 工程根目录下都有一个 package.json 文件，里面都包含了我们所用的插件信息，只需要我们在安装插件的时候注意加上–save，就会自动把插件信息保存到 package.json 中。

如果目录下没有 package.json 文件也不要紧，在根目录命令行中运行 npm init 即可生成。

### [](#博客环境安装 "#博客环境安装")博客环境安装

前面做好版本控制，那接下来的事情就好做了。

1.  备份你的代码，注意：代码中不需要包含 node_modules 文件夹了
2.  先在新电脑中装上 nodejs 环境
3.  由于国内安装 npm 的一些插件需要翻墙，所以这里直接用淘宝镜像：cnpm，安装方法：npm install -g cnpm –registry=<a href="https://link.juejin.cn?target=https%3A%2F%2Fregistry.npm.taobao.org" target="_blank" data-ref="nofollow noopener noreferrer" title="https://registry.npm.taobao.org">registry.npm.taobao.org</a>
4.  安装 Hexo 客户端：cnpm install hexo-cli -g
5.  新建博客目录：Hexo init
6.  把你备份的代码放到此目录下，如果有重复的文件直接覆盖就行
7.  安装 Hexo 插件：cnpm install\
    就这样，新的博客环境迁移完成了，执行 hexo s 开始你新的博客征程吧！

## [](#gitlab-runner环境搭建 "#gitlab-runner环境搭建")gitlab-runner 环境搭建

### [](#gitlab-runner的安装 "#gitlab-runner的安装")gitlab-runner 的安装

使用 GitLab 官网提供的下载地址太慢，所以找到了一个国内的镜像地址：

1.  新建 gitlab-ci-multi-runner.repo

        touch /etc/yum.repos.d/gitlab-ci-multi-runner.repo

2.  将以下内容写入文件

<!-- -->

    [gitlab-ci-multi-runner]
    name=gitlab-ci-multi-runner
    baseurl=http://mirrors.tuna.tsinghua.edu.cn/gitlab-ci-multi-runner/yum/el7
    repo_gpgcheck=0
    gpgcheck=0
    enabled=1
    gpgkey=https://packages.gitlab.com/gpg.key

1.  执行

<!-- -->

    sudo yum makecache
    sudo yum install gitlab-ci-multi-runner

1.  以上是楼主在 centos 上的安装过程，其他系统版本的安装请移步<a href="https://link.juejin.cn?target=https%3A%2F%2Fdocs.gitlab.com%2Frunner%2Finstall%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="https://docs.gitlab.com/runner/install/">gitlab-runner 其他系统版本的安装</a>

### [](#gitlab-runner注册到gitlab官网 "#gitlab-runner注册到gitlab官网")gitlab-runner 注册到 GitLab 官网

在终端输入**gitlab-runner register** 会出现以下过程：

    [root@localhost ~]# gitlab-runner register
    Running in system-mode.                            

    Please enter the gitlab-ci coordinator URL (e.g. https://gitlab.com/):
    https://gitlab.com/
    Please enter the gitlab-ci token for this runner:
    your gitlab-ci token
    Please enter the gitlab-ci description for this runner:
    [localhost.localdomain]: my-runner
    Please enter the gitlab-ci tags for this runner (comma separated):
    your tag
    Whether to run untagged builds [true/false]:
    [false]: true
    Registering runner... succeeded                     runner=c5552857
    Please enter the executor: parallels, shell, virtualbox, docker+machine, docker-ssh+machine, docker, docker-ssh, ssh, kubernetes:
    shell
    Runner registered successfully. Feel free to start it, but if it's running already the config should be automatically reloaded!

在注册过程中有两个比较重要的参数，一个是 GitLab 的 URL，另一个就是注册的 token，这两个参数可以在 GitLab 上找到，过程是**Settings\>CI/CD\>Runners settings\>Specific Runners**，如下图所示\
<a href="https://link.juejin.cn?target=http%3A%2F%2Fimg.hchstudio.cn%2Fgitlab-runner-settings2.png" target="_blank" data-ref="nofollow noopener noreferrer" title="http://img.hchstudio.cn/gitlab-runner-settings2.png"><img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/6/10/163ea55d461aec7d~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.png" loading="lazy" alt="gitlab-runner-settings" /></a>gitlab-runner-settings

另外还需要打开\
<a href="https://link.juejin.cn?target=http%3A%2F%2Fimg.hchstudio.cn%2Fgitlab-autoDEVOPs.png" target="_blank" data-ref="nofollow noopener noreferrer" title="http://img.hchstudio.cn/gitlab-autoDEVOPs.png"><img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/6/10/163ea55d463f4929~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.png" loading="lazy" alt="gitlab-runner-settings" /></a>gitlab-runner-settings

要让自己注册的 gitlab-runner 生效，还需要禁用**Shared Runners**

以上过程是楼主在 centos 上操作的，其他版本请移步<a href="https://link.juejin.cn?target=https%3A%2F%2Fdocs.gitlab.com%2Frunner%2Fregister%2Findex.html" target="_blank" data-ref="nofollow noopener noreferrer" title="https://docs.gitlab.com/runner/register/index.html">gitlab-runner 注册到 GitLab</a>

### [](#创建-gitlab-ci-yml，并放着工程的根目录下 "#创建-gitlab-ci-yml，并放着工程的根目录下")创建.gitlab-ci.yml，并放着工程的根目录下

**.gitlab-ci.yml**具体配置请移步<a href="https://link.juejin.cn?target=https%3A%2F%2Fdocs.gitlab.com%2Fce%2Fci%2Fyaml%2FREADME.html" target="_blank" data-ref="nofollow noopener noreferrer" title="https://docs.gitlab.com/ce/ci/yaml/README.html">官方文档</a>，下面给出楼主使用的**.gitlab-ci.yml**具体内容

    variables:
      GIT_STRATEGY: none

    stages:
      - build_and_deploy

    job:
      stage: build_and_deploy
      script:
        - cd /opt/I-team-fly
        - git pull --tags origin dev
        - hexo clean
        - hexo g
        - hexo d
      only: 
        - dev

### [](#查看gitlab上的构建结果 "#查看gitlab上的构建结果")查看 GitLab 上的构建结果

<a href="https://link.juejin.cn?target=http%3A%2F%2Fimg.hchstudio.cn%2Fgitlab-ci-result.png" target="_blank" data-ref="nofollow noopener noreferrer" title="http://img.hchstudio.cn/gitlab-ci-result.png"><img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/6/10/163ea55d465cef4e~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.png" loading="lazy" alt="gitlab-runner-settings" /></a>gitlab-runner-settings

## [](#小结 "#小结")小结

当然这个过程中还是要涉及到几次使用 ssh-key 来设置免密登录，楼主就不在这里赘述了，请遇到问题的小伙伴自行 Google。

## [](#参考文章 "#参考文章")参考文章

- <a href="https://link.juejin.cn?target=https%3A%2F%2Fwww.jianshu.com%2Fp%2F705428ca1410" target="_blank" data-ref="nofollow noopener noreferrer" title="https://www.jianshu.com/p/705428ca1410">基于 GitLab CI 搭建持续集成环境</a>
- <a href="https://link.juejin.cn?target=https%3A%2F%2Fwww.jianshu.com%2Fp%2Fdf433633816b" target="_blank" data-ref="nofollow noopener noreferrer" title="https://www.jianshu.com/p/df433633816b">GitLab 之 gitlab-ci 自动部署</a>
- <a href="https://link.juejin.cn?target=https%3A%2F%2Fblog.csdn.net%2Fu010009279%2Farticle%2Fdetails%2F78780016" target="_blank" data-ref="nofollow noopener noreferrer" title="https://blog.csdn.net/u010009279/article/details/78780016">GitLab CI 集成 GitLab Runner</a>
