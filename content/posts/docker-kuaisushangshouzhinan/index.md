---
categories: ["后端"]
title: "Docker 快速上手指南"
date: "2018-12-03T14:09:51+08:00"
tags: ["Docker", "容器", "后端", "Spring Boot"]
summary: "Docker 听其大名已久，但总是疏于操练，今天准备好好搞一下。"
translationKey: "docker-kuaisushangshouzhinan"
---

> 📌 本文原发布于掘金社区：[Docker 快速上手指南](https://juejin.cn/post/6844903729708154893)

当前浏览器不支持播放音乐或语音，请在微信或其他浏览器中播放 <img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/12/3/16772b00735e133e~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.png" loading="lazy" /> <img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/12/3/16772b007c0c5e99~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.png" loading="lazy" /> <span id="user-content-qqmusic_home_449205_0">稻香 周杰伦 - 魔杰座 <img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/12/3/16772b00734c7795~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.png" loading="lazy" /></span> Docker 听其大名已久，但总是疏于操练，今天准备好好搞一下。

<figure>
<img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/12/3/16772b00735d9c0c~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.png" title="docker" data-src="https://mmbiz.qpic.cn/mmbiz_png/0I2EEYqhgI2xPCws8tGYeHhgmQAJibmbzzic8KfsQrwBUuib5FLSmZVrJxklMEzY0nhK3oemCAmx3jkgoTialVZsYA/640?wx_fmt=png" data-type="png" loading="lazy" />
<figcaption>docker</figcaption>
</figure>

## \`Docker\` 是什么？

**Docker 属于 Linux 容器的一种封装，提供简单易用的容器使用接口。** 它是目前最流行的 Linux 容器解决方案。

Docker 将应用程序与该程序的依赖，打包在一个文件里面。运行这个文件，就会生成一个虚拟容器。程序在这个虚拟容器里运行，就好像在真实的物理机上运行一样。有了 Docker，就不用担心环境问题。

总体来说，Docker 的接口相当简单，用户可以方便地创建和使用容器，把自己的应用放入容器。容器还可以进行版本管理、复制、分享、修改，就像管理普通的代码一样。

## \`Docker\` 怎么用？

本文安装 `Docker` 是基于  `CentOS7` ，其他系统的小伙伴请直接转官网的 quick start.

### 卸载旧版本的 \`Docker\`

较旧版本的 `Docker` 被称为  `docker` 或 `docker-engine` 。 如果已安装这些，请卸载它们以及相关的依赖项。

    sudo yum remove docker \                  docker-client \                  docker-client-latest \                  docker-common \                  docker-latest \                  docker-latest-logrotate \                  docker-logrotate \                  docker-selinux \                  docker-engine-selinux \                  docker-engine

### 安装 \`Docker CE\`

您可以根据需要以不同方式安装 `Docker CE` ：

- 大多数用户设置 `Docker` 的存储库并从中进行安装，以便于安装和升级任务。 也是 `Docker` 官方推荐的方法。

- 有些用户下载 `RPM` 软件包并手动安装并完全手动管理升级。 这在诸如在没有访问互联网的气隙系统上安装 `Docker`的情况下非常有用。

- 在测试和开发环境中，一些用户选择使用自动便捷脚本来安装 `Docker`。

本文采用的是第一种方法 ：

在新主机上首次安装 `Docker CE`之前，需要设置  `Docker` 存储库。 之后，您可以 从存储库安装和更新 `Docker` 。

#### 设置 \`REPOSITORY\`

1， 安装所需的包。 `yum-utils` 提供  `yum-config-manager` 实用程序，`devicemapper` 存储驱动程序需要  `device-mapper-persistent-data` 和 `lvm2`。

    sudo yum install -y yum-utils \  device-mapper-persistent-data \  lvm2

2， 使用以下命令设置稳定存储库。

    sudo yum-config-manager \    --add-repo \    https://download.docker.com/linux/centos/docker-ce.repo

#### 安装 \`Docker CE\`

1， 安装最新版本的`Docker CE`，或转到下一步安装特定版本

    sudo yum install docker-ce

2， 要安装特定版本的`Docker CE`，请列出 `repo`中的可用版本，然后选择并安装：a. 列出并对您的仓库中可用的版本进行排序。 此示例按版本号对结果进行排序，从最高到最低，并被截断：

    yum list docker-ce --showduplicates | sort -rdocker-ce.x86_64            18.09.0.ce-1.el7.centos             docker-ce-stable

返回的列表取决于启用的存储库，并且特定于您的`CentOS`版本（在此示例中以 `.el7`后缀表示）。

b\. 通过其完全限定的包名称安装特定版本，包名称（`docker-ce`）加上版本字符串（第2列）直到第一个连字符，用连字符（ - ）分隔，例如，`docker-ce-18.03.0.ce`。

    sudo yum install docker-ce-<VERSION STRING>

`Docker` 已安装但尚未启动。 已创建 `docker` 组，但未向该组添加任何用户。

3， 启动 `Docker`

    sudo systemctl start docker

4， 通过启动 `hello-world` 镜像来验证  `Docker` 安装并启动成功

    sudo docker run hello-world

上面的命令下载测试映像并在容器中运行它。 当容器运行时，它会打印一条信息性消息并退出。

## 卸载 \`Docker CE\`

1， 卸载 docker 的安装包

    sudo yum remove docker-ce

2， 主机上的图像，容器，卷或自定义配置文件不会自动删除。 要删除所有图像，容器和卷：

    sudo rm -rf /var/lib/docker

## Maven 构建 Spring Boot 的 Docker 镜像

### 构建项目，修改配置

通过 https://start.spring.io/ 构建 Spring Boot 工程。

#### 修改 pom 文件

    <build>    <plugins>        <plugin>            <groupId>org.springframework.boot</groupId>            <artifactId>spring-boot-maven-plugin</artifactId>        </plugin>        <!-- tag::plugin[] -->        <plugin>            <groupId>com.spotify</groupId>            <artifactId>dockerfile-maven-plugin</artifactId>            <version>1.3.6</version>            <configuration>                <!--suppress UnresolvedMavenProperty -->                <repository>${docker.image.prefix}/${project.artifactId}</repository>            </configuration>        </plugin>        <!-- end::plugin[] -->        <plugin>            <groupId>com.spotify</groupId>            <artifactId>docker-maven-plugin</artifactId>            <!--<version>0.4.12</version>-->            <configuration>                <!-- 注意imageName一定要是符合正则[a-z0-9-_.]的，否则构建不会成功 -->                <!-- 详见：https://github.com/spotify/docker-maven-plugin    Invalid repository name ... only [a-z0-9-_.] are allowed-->                <dockerHost>http://127.0.0.1:2375</dockerHost>                <imageName>docker-springboot</imageName>                <baseImage>java</baseImage>                <entryPoint>["java", "-jar", "/${project.build.finalName}.jar"]</entryPoint>                <resources>                    <resource>                        <targetPath>/</targetPath>                        <directory>${project.build.directory}</directory>                        <include>${project.build.finalName}.jar</include>                    </resource>                </resources>            </configuration>        </plugin>    </plugins></build>

需要注意的是 `<dockerHost>http://127.0.0.1:2375</dockerHost>`，如果本地有安装  `docker` ，直接只用本地默认即可，若未安装，需要是远程的 `docker` 服务时需要在服务器配置  `docker` ，具体操作请移步 Docker 远程连接。

#### 添加 \`Dockerfile\`

注意 `com.whforever.dockerspringboot.DockerSpringbootApplication` 是指  `Spring Boot` 项目的代码入口。

    FROM openjdk:8-jdk-alpineVOLUME /tmpARG DEPENDENCY=target/dependencyCOPY ${DEPENDENCY}/BOOT-INF/lib /app/libCOPY ${DEPENDENCY}/META-INF /app/META-INFCOPY ${DEPENDENCY}/BOOT-INF/classes /appENTRYPOINT ["java","-cp","app:app/lib/*","com.whforever.dockerspringboot.DockerSpringbootApplication"]

### 构建 构建 \`Spring Boot\` 的 \`Docker\` 镜像

执行 `maven` 命令，执行构建

    mvn clean package docker:build

执行完成之后我们就可以在远程看到刚构建好的 `Spring Boot` 的镜像。

    docker container ls CONTAINER ID        IMAGE                      COMMAND                  CREATED             STATUS              PORTS                    NAMESe5f2c7e4e7c1        docker-springboot:latest   "java -jar /docker-s…"   22 hours ago        Up 22 hours         0.0.0.0:8080->8080/tcp   agitated_kilby

启动 docker 镜像

    docker run -p 8080:8080 docker-springboot

完美……

<figure>
<img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/12/3/16772b009a5943e1~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.png" title="docker-run" data-src="https://mmbiz.qpic.cn/mmbiz_png/0I2EEYqhgI2xPCws8tGYeHhgmQAJibmbzrOwF5E2Fib1MXKNfBg0icyET2ficgLWyfapjoib9hnwTQS4ujOPSZtaXPA/640?wx_fmt=png" data-type="png" loading="lazy" />
<figcaption>docker-run</figcaption>
</figure>

## 小结

本文涉及的代码已经上传到 `github`，感兴趣的小伙伴后台回复关键字 docker 就可获得代码地址。

## 参考链接

- https://spring.io/guides/gs/spring-boot-docker/

- http://www.ruanyifeng.com/blog/2018/02/docker-tutorial.html
