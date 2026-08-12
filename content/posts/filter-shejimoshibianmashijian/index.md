---
categories: ["后端"]
title: "Filter 设计模式编码实践"
date: "2018-09-21T10:55:49+08:00"
tags: ["设计模式", "后端", "Kafka", "Google"]
summary: "最近项目中遇到各种输出数据监控，数据校验等逻辑，一个个实现很是麻烦。项目是中途接手的，不是很熟悉，偶然一天发现项目中对 Filter 的使用扩展起来很是方便，所以，今天楼主来分享下，也为自己学习做个记录。下面我们从三方面来阐述。 Filter 在设计模式里面被称为责任链设计模式…"
translationKey: "filter-shejimoshibianmashijian"
---

> 📌 本文原发布于掘金社区：[Filter 设计模式编码实践](https://juejin.cn/post/6844903682689990664)

> 原文地址： <a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2018%2F4008%2F%3F_ref%3Djuejin" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/article/2018/4008/?_ref=juejin">haifeiWu和他朋友们的博客</a>\
> 博客地址：<a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2018%2F4008%2F%3F_ref%3Djuejin" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/article/2018/4008/?_ref=juejin">www.hchstudio.cn</a>\
> 欢迎转载，转载请注明作者及出处，谢谢！

最近项目中遇到各种输出数据监控，数据校验等逻辑，一个个实现很是麻烦。项目是中途接手的，不是很熟悉，偶然一天发现项目中对 Filter 的使用扩展起来很是方便，所以，今天楼主来分享下，也为自己学习做个记录。下面我们从三方面来阐述。

## 什么是 Filter

Filter 在设计模式里面被称为责任链设计模式，顾名思义，我们可以在这条责任链上对一组数据做不同的处理。这种类型的设计模式属于结构型模式，它结合多个标准来获得单一标准。UML见下图，

<figure>
<img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/9/21/165fa0c2905483f7~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp" loading="lazy" alt="Filter设计模式" />
</figure>

## 为什么要使用 Filter

好处是显而易见的，它使我们的代码将请求和处理分开。请求者可以不知道是谁处理的，处理者可以不用知道请求的全貌，两者解耦，提高系统的灵活性。从而我们的代码更加简洁跟易于扩展，而不是机械重复的Ctrl+C，Ctrl+V。当然好处还有好多，楼主就不在这里赘述了，感兴趣的小伙伴自行Google。

## 怎么用 Filter 项目中的代码实现逻辑

定义 Filter 接口，接口中定义进行数据处理的方法。

``` java
public interface IDataHandlerFilter {

    void filter(DataPackage dataPackage);
}
```

统一数据发送端，将业务系统处理好的数据，统一发送到 kafka。当然我们还可以实现 Filter 对数据进行其他处理。

``` java
public class DataSendHandlerFilter implements IDataHandlerFilter {

    public static final Logger log = LogManager.getLogger(DataSendHandlerFilter.class);

    private int logCenterType;

    //数据源类型 0-实时数据 1-wifi数据
    private String resourceType = StringUtils.isBlank(Repository.getCityConfig().getResourceType()) ? "0" : Repository.getCityConfig().getResourceType();

    public DataSendHandlerFilter() {

        logCenterType = Repository.getSysConfig().getLogCenterType();

        //初始化kafka
        if (logCenterType == Constant.LogcenterType.KAFKA){
            KafkaProducerHelper.init(Repository.getCityConfig().getCityId(), Repository.getSysConfig());
            log.info("初始化kafka");
        }
    }

    @Override
    public void filter(DataPackage dataPackage) {

        GpsData gpsData = dataPackage.getTargetData();

        /*重复数据和时间格式错误数据不发送*/
        if (null != gpsData && !gpsData.isError() && logCenterType == Constant.LogcenterType.KAFKA) {
            if (gpsData.isGps()) {
                KafkaProducerHelper.sendData(gpsData.toGpsStr(resourceType));
            }

            if (gpsData.isStn()) {
                KafkaProducerHelper.sendData(gpsData.toStnStr(resourceType));
            }
        }
    }
}
```

设置系统要使用的 Filter ，根据具体业务有所不同。

``` java
public class HanderFilterUtil {
    
    private static List<IDataHandlerFilter> list;

    /**
     * 这个是有先后顺序的
     * @return
     */
    public static List<IDataHandlerFilter> getDefaultFilter(SysConfig sysConfig, CityConfig cityConfig){
        
        if (null == list){
            list = new ArrayList<>();
        }
        
        //默认提供接收日志、重复校验、时间格式校验、属性校验、数据转发过滤器
        list.add(new RepeatHandlerFilter());
        list.add(new DataLogHandlerFilter());
        list.add(new DataSendHandlerFilter());
        // ......
        return list;
    }
}
```

最后我们通过调用 getDefaultFilter 方法来决定我们系统中使用哪几种 Filter 来处理数据。

## 小结

本文中的代码不能直接运行，只是提供一种写代码的思路，小伙伴遇到此种场景可以借鉴一下。

<figure>
<img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/9/21/165fa0c2852d91f8~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.awebp" loading="lazy" alt="关注我们" />
<figcaption aria-hidden="true">关注我们</figcaption>
</figure>
