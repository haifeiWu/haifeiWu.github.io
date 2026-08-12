---
categories: ["后端"]
title: "阿里云离线同步工具 DataX 源码略读"
date: "2018-07-06T10:47:57+08:00"
tags: ["阿里巴巴", "Java", "数据库", "MySQL", "源码"]
summary: "最近在做一些数据迁移相关工作，并最终采用了 DataX，楼主也本着知其然，也要知其所以然的精神粗略的看一看 Datax 的源码。"
translationKey: "aliyunlixiantongbugongjudataxyuanmalvedu"
---

> 📌 本文原发布于掘金社区：[阿里云离线同步工具 DataX 源码略读](https://juejin.cn/post/6844903634195447821)

最近在做一些数据迁移相关工作，并最终采用了 DataX，楼主也本着知其然，也要知其所以然的精神粗略地看一看 Datax 的源码。\
<span id="user-content-more"></span>

## [](#代码下载 "#代码下载")代码下载

相信这部分作为程序员的我们，大家都知道，github 是个大家庭，所以楼主直接去 github 上扒下来就好了，项目是基于 Maven 构建的，直接使用 IDE 导入工程即可。

    git clone git@github.com:alibaba/DataX.git

## [](#快速开始 "#快速开始")快速开始

这部分楼主也不多说了，因为楼主在上篇文章中已经讲清楚了，感兴趣的小伙伴请移步<a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2018%2F4928%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/article/2018/4928/">阿里离线数据同步工具 DataX 踩坑记录</a>

## [](#DataX概览-（摘抄自官网） "#DataX概览-（摘抄自官网）")DataX 概览（摘抄自官网）

<a href="https://link.juejin.cn?target=http%3A%2F%2Fimg.hchstudio.cn%2FdataX-struct.png" target="_blank" data-ref="nofollow noopener noreferrer" title="http://img.hchstudio.cn/dataX-struct.png"><img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/7/6/1646d7d4549eca4c~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.png" title="DataX结构图" loading="lazy" alt="DataX结构图" /></a>DataX 结构图

- 设计理念\
  为了解决异构数据源同步问题，DataX 将复杂的网状同步链路变成了星型数据链路，DataX 作为中间传输载体负责连接各种数据源。当需要接入一个新的数据源的时候，只需要将此数据源对接到 DataX，便能跟已有的数据源做到无缝数据同步。

- 当前使用现状\
  DataX 在阿里巴巴集团内被广泛使用，承担了所有大数据的离线同步业务，并已持续稳定运行了 6年之久。目前每天完成同步 8w 多道作业，每日传输数据量超过 300TB。

## [](#源码分析 "#源码分析")源码分析

如上图所示，DataX 的源码大部分都是用来适配各种各样的数据源的 reader 与 writer，核心转换的 framework 就是 core 这个 model，打开这 model，我们可以直接看到一个叫 Engine 的文件

<a href="https://link.juejin.cn?target=http%3A%2F%2Fimg.hchstudio.cn%2Fdatax-source.png" target="_blank" data-ref="nofollow noopener noreferrer" title="http://img.hchstudio.cn/datax-source.png"><img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/7/6/1646d7d44a370e42~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.png" title="DataX结构图" loading="lazy" alt="DataX结构图" /></a>DataX 结构图

根据我们的代码习惯，这个就该是 DataX 的入口代码，如下所示，代码是删除异常处理的代码，很简单，就三行，我们接着看 entry 这个方法

    public static void main(String[] args) throws Exception {
          int exitCode = 0;
          Engine.entry(args);
          System.exit(exitCode);
      }

通过代码我们知道，这个方法就是初始化一些启动参数，并调用 start 方法\

    public static void entry(final String[] args) throws Throwable {
            Options options = new Options();
            options.addOption("job", true, "Job config.");
            options.addOption("jobid", true, "Job unique id.");
            options.addOption("mode", true, "Job runtime mode.");

            BasicParser parser = new BasicParser();
            CommandLine cl = parser.parse(options, args);

            String jobPath = cl.getOptionValue("job");

            // 如果用户没有明确指定jobid, 则 datax.py 会指定 jobid 默认值为-1
            String jobIdString = cl.getOptionValue("jobid");
            RUNTIME_MODE = cl.getOptionValue("mode");

            Configuration configuration = ConfigParser.parse(jobPath);

            long jobId;
            if (!"-1".equalsIgnoreCase(jobIdString)) {
                jobId = Long.parseLong(jobIdString);
            } else {
                // only for dsc & ds & datax 3 update
                String dscJobUrlPatternString = "/instance/(\\d{1,})/config.xml";
                String dsJobUrlPatternString = "/inner/job/(\\d{1,})/config";
                String dsTaskGroupUrlPatternString = "/inner/job/(\\d{1,})/taskGroup/";
                List<String> patternStringList = Arrays.asList(dscJobUrlPatternString,
                        dsJobUrlPatternString, dsTaskGroupUrlPatternString);
                jobId = parseJobIdFromUrl(patternStringList, jobPath);
            }

            boolean isStandAloneMode = "standalone".equalsIgnoreCase(RUNTIME_MODE);
            if (!isStandAloneMode && jobId == -1) {
                // 如果不是 standalone 模式，那么 jobId 一定不能为-1
                throw DataXException.asDataXException(FrameworkErrorCode.CONFIG_ERROR, "非 standalone 模式必须在 URL 中提供有效的 jobId.");
            }
            configuration.set(CoreConstant.DATAX_CORE_CONTAINER_JOB_ID, jobId);

            //打印vmInfo
            VMInfo vmInfo = VMInfo.getVmInfo();
            if (vmInfo != null) {
                LOG.info(vmInfo.toString());
            }

            LOG.info("\n" + Engine.filterJobConfiguration(configuration) + "\n");

            LOG.debug(configuration.toJSON());

            ConfigurationValidate.doValidate(configuration);
            Engine engine = new Engine();
            engine.start(configuration);
        }

下面代码就是获取配置文件中的配置，初始化 container 的具体类型，初始化 Job 或者 Task 的运行容器，并运行插件的 Job 或者 Task 逻辑\

    /* check job model (job/task) first */
       public void start(Configuration allConf) {

           // 绑定column转换信息
           ColumnCast.bind(allConf);

           /**
            * 初始化PluginLoader，可以获取各种插件配置
            */
           LoadUtil.bind(allConf);

           boolean isJob = !("taskGroup".equalsIgnoreCase(allConf
                   .getString(CoreConstant.DATAX_CORE_CONTAINER_MODEL)));
           //JobContainer会在schedule后再行进行设置和调整值
           int channelNumber =0;
           AbstractContainer container;
           long instanceId;
           int taskGroupId = -1;
           if (isJob) {
               allConf.set(CoreConstant.DATAX_CORE_CONTAINER_JOB_MODE, RUNTIME_MODE);
               container = new JobContainer(allConf);
               instanceId = allConf.getLong(
                       CoreConstant.DATAX_CORE_CONTAINER_JOB_ID, 0);

           } else {
               container = new TaskGroupContainer(allConf);
               instanceId = allConf.getLong(
                       CoreConstant.DATAX_CORE_CONTAINER_JOB_ID);
               taskGroupId = allConf.getInt(
                       CoreConstant.DATAX_CORE_CONTAINER_TASKGROUP_ID);
               channelNumber = allConf.getInt(
                       CoreConstant.DATAX_CORE_CONTAINER_TASKGROUP_CHANNEL);
           }

           //缺省打开perfTrace
           boolean traceEnable = allConf.getBool(CoreConstant.DATAX_CORE_CONTAINER_TRACE_ENABLE, true);
           boolean perfReportEnable = allConf.getBool(CoreConstant.DATAX_CORE_REPORT_DATAX_PERFLOG, true);

           //standlone模式的datax shell任务不进行汇报
           if(instanceId == -1){
               perfReportEnable = false;
           }

           int priority = 0;
           try {
               priority = Integer.parseInt(System.getenv("SKYNET_PRIORITY"));
           }catch (NumberFormatException e){
               LOG.warn("prioriy set to 0, because NumberFormatException, the value is: "+System.getProperty("PROIORY"));
           }

           Configuration jobInfoConfig = allConf.getConfiguration(CoreConstant.DATAX_JOB_JOBINFO);
           //初始化PerfTrace
           PerfTrace perfTrace = PerfTrace.getInstance(isJob, instanceId, taskGroupId, priority, traceEnable);
           perfTrace.setJobInfo(jobInfoConfig,perfReportEnable,channelNumber);
           container.start();
       }

### [](#DataX的core模块的配置文件 "#DataX的core模块的配置文件")DataX 的 core 模块的配置文件

从配置文件中可以看出 DataX 要求的 JVM 的堆内存最小是 1G，这是之前楼主使用 DataX 遇到的一个小小的问题，其他的配置都是一些通用配置。

    {
        "entry": {
            "jvm": "-Xms1G -Xmx1G",
            "environment": {}
        },
        "common": {
            "column": {
                "datetimeFormat": "yyyy-MM-dd HH:mm:ss",
                "timeFormat": "HH:mm:ss",
                "dateFormat": "yyyy-MM-dd",
                "extraFormats":["yyyyMMdd"],
                "timeZone": "GMT+8",
                "encoding": "utf-8"
            }
        },
        "core": {
            "dataXServer": {
                "address": "http://localhost:7001/api",
                "timeout": 10000,
                "reportDataxLog": false,
                "reportPerfLog": false
            },
            "transport": {
                "channel": {
                    "class": "com.alibaba.datax.core.transport.channel.memory.MemoryChannel",
                    "speed": {
                        "byte": -1,
                        "record": -1
                    },
                    "flowControlInterval": 20,
                    "capacity": 512,
                    "byteCapacity": 67108864
                },
                "exchanger": {
                    "class": "com.alibaba.datax.core.plugin.BufferedRecordExchanger",
                    "bufferSize": 32
                }
            },
            "container": {
                "job": {
                    "reportInterval": 10000
                },
                "taskGroup": {
                    "channel": 5
                },
                "trace": {
                    "enable": "false"
                }

            },
            "statistics": {
                "collector": {
                    "plugin": {
                        "taskClass": "com.alibaba.datax.core.statistics.plugin.task.StdoutPluginCollector",
                        "maxDirtyNumber": 10
                    }
                }
            }
        }
    }

## [](#小结 "#小结")小结

这次楼主只是大概地梳理了一下 DataX 的代码，水平有点水，相信热爱学习的楼主，可以 day day up

作 者：haifeiWu 原文链接：<a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2018%2Fd91b%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/article/2018/d91b/">www.hchstudio.cn/article/201…</a>版权声明：非特殊声明均为本站原创作品，转载时请注明作者和原文链接。
