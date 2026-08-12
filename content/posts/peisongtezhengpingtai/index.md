---
categories: ["后端"]
title: "配送特征平台"
date: "2021-06-21T16:02:12+08:00"
tags: ["后端", "架构"]
summary: "现实世界中，一个运单的完成过程是从用户下单开始到用户收餐骑手离客为止，需经历一系列室内室外的场景——用户下单，系统派单，骑手室外骑行到目的地然后下车步行到商家，等待取餐驻留室内，商家出餐，骑手取餐离店"
translationKey: "peisongtezhengpingtai"
---

> 📌 本文原发布于掘金社区：[配送特征平台](https://juejin.cn/post/6976154240678887455)

# 一、业务背景

现实世界中，一个运单的完成过程是从用户下单开始到用户收餐骑手离客为止，需经历一系列室内室外的场景——用户下单，系统派单，骑手室外骑行到目的地然后下车步行到商家，等待取餐驻留室内，商家出餐，骑手取餐离店后步行上车，室外骑行到用户目的地，下车步行上楼送餐，驻留室内等待用户收餐，最后用户收餐骑手离客。那么特征平台就是上述过程中涉及到骑手的基础数据沉淀下来，进行数据挖掘提供特征数据，来辅助算法平台更好的完成骑手派单，配送费的计算以及倾斜等场景。

# 二、整体架构与服务拆分

## 整体架构

特征平台的整体架构需要兼顾下面的基本规范。

- 流程标准化：从数据输入，加工计算到数据输出做了一个流程的标准化。
- 数据分层，将共性沉淀下来。
- 特征兜底，降低风险。

<img src="https://p1-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/bf56d06107054024994fc24464c1adc3~tplv-k3u1fbpfcp-zoom-in-crop-mark:1512:0:0:0.awebp?" loading="lazy" alt="流程图.jpg" />

基于定制的基本规范，服务的整体架构如上图所示，共分为 7 层：

1.  数据源层：主要有线上的业务表运单表、骑手表等，以及离线 Hive 表
2.  数据层：将数据进行清洗和转换，最后形成实时特征与离线特征的宽表。
3.  计算层：通过标准化的 SQL 对宽表数据进行计算。
4.  存储层：存储计算层输出的特征数据。
5.  服务层：提供统一的 RPC 特征读取服务，将存储层数据统一输出应用层应用。
6.  应用层：主要有 ETA 时间预估服务、分单引擎服务、骑手管控服务以及供需服务。
7.  管理系统：负责特征元数据从创建到销毁的整个生命周期的管理，以及特征的计算口径，数据源，存储格式的管理，特征默认值。
8.  监控报警：包括对特征生产链路服务依赖的监控，以及对特征数据质量的可视化，通过人工巡检的方式发现数据问题。

## 服务拆分

1.  特征读取服务：抽象统一的特征读取的 RPC 接口。
2.  实时特征写入服务：提供基于 RPC，HTTP，MQ 的实时特征数据写入。
3.  离线特征写入服务：依赖大数据平台，将离线数据在线化操作。
4.  特征管理平台：特征元数据管理。三、特征抽象 数据源模型（feature_source）：抽象特征生产源，来定义特征生产数据源的元数据模型。如下

``` json
{
    "product_id": "",
    "feature_ids": ""
}
```

特征使用业务方模型(feature_business)：抽象使用特征的业务方，来定义业务方的元数据模型。如下

``` json
{
    "business_id": "",
    "feature_ids": ""
}
```

特征元数据(feature)：通过抽象特征的共性，来定义特征的元数据模型。如下

``` json
{
    "feature_id": "",
    "feature_name_space": "",
    "object_id":"", // 特征实体ID（骑手，店铺，用户等维度），骑手的特征就是骑手id
    "feature_val": "",
    "expire_time": "",
    "update_time": "",
    "source": ""
}
```

特征数据源，特征业务方以及特征三者之间的关系：

> feature_source vs feature (1:n)\
> feature_business vs feature (1:n)

# 四、实时特征

介绍实时特征从数据源到存储的整个流程。

<img src="https://p9-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/ca663ed9d7c14a0d96f518fcf6f2c221~tplv-k3u1fbpfcp-zoom-in-crop-mark:1512:0:0:0.awebp?" loading="lazy" alt="流程图 (1).jpg" />

上图是整个实时特征从数据源到存储的整个流程，整个架构可以分成 4 层，

1.  特征管理平台：负责特征从创建到销毁的整个生命周期的管理，以及关于整个特征管理其他业务抽象的管理，包括特征实时生产任务，特征离线生产任务管理等。
2.  任务调度平台：使用开源的 airflow 分布式调度平台，通过抽象特征生产任务共性，定制自定义的 DAG 任务，实现实时特征的秒级或者分钟级的生产，将生产的特征数据写入到 MQ。
3.  flink 数据同步任务：通过 flink 任务实时同步线上业务的业务数据到索引宽表与明细宽表。
4.  consumer 服务：提供 RPC，MQ，HTTP 的特征写入，将特征数据按照特征管理平台定制的统一数据模型写入到存储中。

# 五、离线特征

介绍离线特征从数据源到存储的整个流程。

<img src="https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/6da92bfdeb13468dab19cf22bd9da19a~tplv-k3u1fbpfcp-zoom-in-crop-mark:1512:0:0:0.awebp?" loading="lazy" alt="流程图.jpg" />

上图是整个离线特征从数据源到存储的整个流程，整个架构可以分成 4 层，

1.  任务调度平台：这里的任务调度平台是指大数据的离线任务调度平台，负责离线任务调度的整个生命周期。
2.  特征管理平台：负责特征从创建到销毁的整个生命周期的管理，以及关于整个特征管理其他业务抽象的管理，包括特征实时生产任务，特征离线生产任务管理等。
3.  特征抽取任务：抽象的统一的特征抽取任务，依赖特征管理平台的配置信息，生成标准的 Hive SQL，并将抽取结果数据写入到特征共享表（特征宽表）。
4.  特征聚合任务：将特征宽表的数据根据特征管理平台的配置，生成特定业务方的特征数据。
5.  特征同步任务：将聚合任务生成的结果数据，通过离线数据在线化的工具，将特征数据加载到线上存储。

# 六、特征算子的思考

举个例子：有一个骑手历史完单量的特征 a（T-1），以及另一个骑手当天完单量的实时特征 b。现在我们需要一个骑手完单量的特征 c，c = a + b。对于这种情况我们可以复用 a，b 两个特征来计算 c 特征。对于上述情况，就可以设计通用的算子来进行特征的复用，只要简单提供一些配置项，就可以在不写代码的情况下完成计算和存储流程。比如上面的骑手完单量特征的表达式算子，可以支持下面这些形式的“计算”：

<img src="https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/5088591715d14987b5126b4ea717d3fe~tplv-k3u1fbpfcp-zoom-in-crop-mark:1512:0:0:0.awebp?" loading="lazy" alt="流程图 (1).jpg" />

# 七、相关资料

<a href="https://link.juejin.cn?target=https%3A%2F%2Ftech.meituan.com%2F2017%2F09%2F22%2Fonline-feature-system02.html" target="_blank" data-ref="nofollow noopener noreferrer" title="https://tech.meituan.com/2017/09/22/online-feature-system02.html">人工智能在线特征系统中的生产调度</a>

<a href="https://link.juejin.cn?target=https%3A%2F%2Ftech.meituan.com%2F2017%2F07%2F06%2Fonline-feature-system.html" target="_blank" data-ref="nofollow noopener noreferrer" title="https://tech.meituan.com/2017/07/06/online-feature-system.html">人工智能在线特征系统中的数据存取技术</a>

<a href="https://link.juejin.cn?target=https%3A%2F%2Ftech.meituan.com%2F2021%2F03%2F04%2Ffeatureplatform-in-mtwaimai.html" target="_blank" data-ref="nofollow noopener noreferrer" title="https://tech.meituan.com/2021/03/04/featureplatform-in-mtwaimai.html">美团外卖特征平台的建设与实践</a>

<a href="https://link.juejin.cn?target=https%3A%2F%2Fwww.infoq.cn%2Farticle%2F40uuwny38rbvsf3wm3my" target="_blank" data-ref="nofollow noopener noreferrer" title="https://www.infoq.cn/article/40uuwny38rbvsf3wm3my">美团配送实时特征平台建设实践</a>

<a href="https://link.juejin.cn?target=https%3A%2F%2Fxargin.com%2Ffeature-system-dev%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="https://xargin.com/feature-system-dev/">一套实时特征系统的迭代过程</a>
