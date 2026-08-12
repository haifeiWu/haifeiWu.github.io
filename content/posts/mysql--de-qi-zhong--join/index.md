---
categories: ["Java"]
title: "MySQL 的七种 join"
date: "2017-02-06T00:00:00+08:00"
tags: ["MySQL", "数据库", "SQL"]
summary: "对于 SQL 的 Join，在学习起来可能是比较乱的。我们知道，SQL 的 Join 语法有很多 inner 的，有 outer 的，有 left 的，有时候，对于 Select 出来的结果集是什么样子有点不是很清楚。Coding Horror 上有一篇文章（实在不清楚"
translationKey: "mysql--de-qi-zhong--join"
---

> 📌 本文原发布于代码星冰乐：[MySQL 的七种 join](https://changhuin.github.io/article/2017/56cd/)

对于 SQL 的 Join，在学习起来可能是比较乱的。我们知道，SQL 的 Join 语法有很多 inner 的，有 outer 的，有 left 的，有时候，对于 Select 出来的结果集是什么样子有点不是很清楚。Coding Horror 上有一篇文章（实在不清楚为什么 Coding Horror 也被墙）通过 文氏图 Venn diagrams 解释了 SQL 的 Join。\

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

## 文氏图与 SQL 语句的编写以及查询结果

### 内连接

#### 内连接文氏图
> 📷 图注：表的内连接

##### 执行的 SQL 语句以及执行的查询结果

- 执行的 SQL 语句

      select * from tbl_dept a inner join tbl_emp b on a.id=b.deptId;

- 查询结果\
  

## 左外连接

### 左外连接文氏图
> 📷 图注：左连接

##### 执行的 SQL 语句以及执行的查询结果

- 执行的 SQL 语句

<!-- -->

    select * from tbl_dept a left join tbl_emp b on a.id=b.deptId;

- 查询结果\
> 📷 图注：左外连接

### 右外连接

#### 右外连接文氏图

##### 执行的 SQL 语句以及执行的查询结果

- 执行的 SQL 语句

<!-- -->

    select * from tbl_dept a right join tbl_emp b on a.id=b.deptId;

- 查询结果\
  

### 左连接

#### 左连接文氏图

##### 执行的 SQL 语句以及执行的查询结果

- 执行的 SQL 语句

<!-- -->

    elect * from tbl_dept a left join tbl_emp b on a.id=b.deptId where b.deptId is null;

- 查询结果

### 右连接

#### 右连接文氏图
> 📷 图注：右连接

##### 执行的 SQL 语句以及执行的查询结果

- 执行的 SQL 语句

<!-- -->

    select * from tbl_dept a right join tbl_emp b on a.id=b.deptId where a.id is null;

- 查询结果
> 📷 图注：右连接

### 全连接

#### 全连接文氏图

##### 执行的 SQL 语句以及执行的查询结果

- 执行的 SQL 语句

<!-- -->

    select * from tbl_dept a right join tbl_emp b on a.id=b.deptId 
    union 
    select * from tbl_dept a left join tbl_emp b on a.id=b.deptId;

- 查询结果\
> 📷 图注：全连接

### 两张表中都没有出现的数据集

#### 文氏图

##### 执行的 SQL 语句以及执行的查询结果

- 执行的 SQL 语句

<!-- -->

    select * from tbl_dept a right join tbl_emp b on a.id=b.deptId where a.id is null union select * from tbl_dept a left join tbl_emp b on a.id=b.deptId where b.deptId is null;

- 查询结果

