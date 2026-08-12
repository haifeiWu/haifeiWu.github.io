---
categories: ["Java"]
title: "Mysql 的七种 join"
date: "2017-02-06T00:00:00+08:00"
tags: ["Android", "Docker", "Go", "Java", "Kafka", "Kotlin", "MySQL", "Nginx", "Python", "Raft", "Redis", "Shell", "Spring-Boot", "WebFlux", "go", "golang", "netty", "web", "学习笔记", "工具", "性能优化", "性能测试", "总结", "散列表", "旅游日记", "源码", "源码解析", "算法", "设计模式", "译文", "配置中心", "问题排查"]
summary: "对于SQL的Join，在学习起来可能是比较乱的。我们知道，SQL的Join语法有很多inner的，有outer的，有left的，有时候，对于Select出来的结果集是什么样子有点不是很清楚。Coding Horror上有一篇文章（实在不清楚"
translationKey: "mysql--de-qi-zhong--join"
---

> 📌 本文原发布于代码星冰乐：[Mysql 的七种 join](https://changhuin.github.io/article/2017/56cd/)

对于SQL的Join，在学习起来可能是比较乱的。我们知道，SQL的Join语法有很多inner的，有outer的，有left的，有时候，对于Select出来的结果集是什么样子有点不是很清楚。Coding Horror上有一篇文章（实在不清楚为什么Coding Horror也被墙）通过 文氏图 Venn diagrams解释了SQL的Join。\

## 建表

在这里呢我们先来建立两张有外键关联的张表。

    CREATE DATABASE db0206;
    USE db0206;

    CREATE TABLE `db0206`.`tbl_dept`(  
      `id` INT(11) NOT NULL AUTO_INCREMENT,
      `deptName` VARCHAR(30),
      `locAdd` VARCHAR(40),
      PRIMARY KEY (`id`)
    ) ENGINE=INNODB CHARSET=utf8;

    CREATE TABLE `db0206`.`tbl_emp`(  
      `id` INT(11) NOT NULL AUTO_INCREMENT,
      `name` VARCHAR(20),
      `deptId` INT(11),
      PRIMARY KEY (`id`),
      FOREIGN KEY (`deptId`) REFERENCES `db0206`.`tb_dept`(`id`)
    ) ENGINE=INNODB CHARSET=utf8;
    /*插入数据*/
    INSERT INTO tbl_dept(deptName,locAdd) VALUES('RD',11);
    INSERT INTO tbl_dept(deptName,locAdd) VALUES('HR',12);
    INSERT INTO tbl_dept(deptName,locAdd) VALUES('MK',13);
    INSERT INTO tbl_dept(deptName,locAdd) VALUES('MIS',14);
    INSERT INTO tbl_dept(deptName,locAdd) VALUES('FD',15);

    INSERT INTO tbl_emp(NAME,deptId) VALUES('z3',1);
    INSERT INTO tbl_emp(NAME,deptId) VALUES('z4',1);
    INSERT INTO tbl_emp(NAME,deptId) VALUES('z5',1);

    INSERT INTO tbl_emp(NAME,deptId) VALUES('w5',2);
    INSERT INTO tbl_emp(NAME,deptId) VALUES('w6',2);

    INSERT INTO tbl_emp(NAME,deptId) VALUES('s7',3);

    INSERT INTO tbl_emp(NAME,deptId) VALUES('s8',4);

## 文氏图与SQL语句的编写以及查询结果

### 内连接

#### 内连接文氏图

![表的内连接](https://of9xsczb1.bkt.clouddn.com/%E4%BA%A4%E9%9B%86.png)

##### 执行的sql语句以及执行的查询结果

- 执行的sql语句

      select * from tbl_dept a inner join tbl_emp b on a.id=b.deptId;

- 查询结果\
  ![这里写图片描述](https://of9xsczb1.bkt.clouddn.com/%E5%86%85%E8%BF%9E%E6%8E%A5.png)

## 左外连接

### 左外连接文氏图

![左连接](https://of9xsczb1.bkt.clouddn.com/%E5%85%A8A.png)

##### 执行的sql语句以及执行的查询结果

- 执行的sql语句

<!-- -->

    select * from tbl_dept a left join tbl_emp b on a.id=b.deptId;

- 查询结果\
  ![左外连接](https://of9xsczb1.bkt.clouddn.com/%E5%B7%A6%E8%BF%9E%E6%8E%A5.png)

### 右外连接

#### 右外连接文氏图

![这里写图片描述](https://of9xsczb1.bkt.clouddn.com/%E5%85%A8B.jpg)

##### 执行的sql语句以及执行的查询结果

- 执行的sql语句

<!-- -->

    select * from tbl_dept a right join tbl_emp b on a.id=b.deptId;

- 查询结果\
  ![这里写图片描述](https://of9xsczb1.bkt.clouddn.com/%E5%8F%B3%E5%A4%96%E9%93%BE%E6%8E%A5.png)

### 左连接

#### 左连接文氏图

![这里写图片描述](https://of9xsczb1.bkt.clouddn.com/%E7%8B%AC%E6%9C%89A.png)

##### 执行的sql语句以及执行的查询结果

- 执行的sql语句

<!-- -->

    elect * from tbl_dept a left join tbl_emp b on a.id=b.deptId where b.deptId is null;

- 查询结果

![这里写图片描述](https://of9xsczb1.bkt.clouddn.com/%E5%B7%A6%E5%A4%96%E8%BF%9E%E6%8E%A5.png)

### 右连接

#### 右连接文氏图

![右连接](https://of9xsczb1.bkt.clouddn.com/%E7%8B%AC%E6%9C%89B.jpg)

##### 执行的sql语句以及执行的查询结果

- 执行的sql语句

<!-- -->

    select * from tbl_dept a right join tbl_emp b on a.id=b.deptId where a.id is null;

- 查询结果

![右连接](https://of9xsczb1.bkt.clouddn.com/%E5%8F%B3%E8%BF%9E%E6%8E%A5.png)

### 全连接

#### 全连接文氏图

![这里写图片描述](https://of9xsczb1.bkt.clouddn.com/%E5%85%A8%E9%9B%86.png)

##### 执行的sql语句以及执行的查询结果

- 执行的sql语句

<!-- -->

    select * from tbl_dept a right join tbl_emp b on a.id=b.deptId 
    union 
    select * from tbl_dept a left join tbl_emp b on a.id=b.deptId;

- 查询结果\
  ![全连接](https://of9xsczb1.bkt.clouddn.com/%E5%85%A8%E8%BF%9E%E6%8E%A5.png)

### 两张表中都没有出现的数据集

#### 文氏图

![](https://of9xsczb1.bkt.clouddn.com/%E7%8B%ACA%E7%8B%ACB%E5%B9%B6%E9%9B%86.png)

##### 执行的sql语句以及执行的查询结果

- 执行的sql语句

<!-- -->

    select * from tbl_dept a right join tbl_emp b on a.id=b.deptId where a.id is null union select * from tbl_dept a left join tbl_emp b on a.id=b.deptId where b.deptId is null;

- 查询结果

![这里写图片描述](https://img.hchstudio.cn/mysql-result.png)

