---
categories: ["后端"]
title: "I-team 博客全文检索 Elasticsearch 实战"
date: "2018-07-12T16:26:02+08:00"
tags: ["Go", "Spring Boot", "Elasticsearch", "Java", "Linux"]
summary: "一直觉得博客缺点东西，最近还是发现了，当博客慢慢多起来的时候想要找一篇之前写的博客很是麻烦，于是作为后端开发的楼主觉得自己动手丰衣足食，也就有了这次博客全文检索功能 Elasticsearch 实战，这里还要感谢一下‘辉哥’赞助的一台服务器。"
---

> 📌 本文原发布于掘金社区：[I-team 博客全文检索 Elasticsearch 实战](https://juejin.cn/post/6844903637433450503)

一直觉得博客缺点东西，最近还是发现了，当博客慢慢多起来的时候想要找一篇之前写的博客很是麻烦，于是作为后端开发的楼主觉得自己动手丰衣足食，也就有了这次博客全文检索功能 Elasticsearch 实战，这里还要感谢一下‘辉哥’赞助的一台服务器。\
<span id="user-content-more"></span>

## [](#全文检索工具选型 "#全文检索工具选型")全文检索工具选型

众所周知，支持全文检索的工具有很多，像 Lucene，solr，Elasticsearch 等，相比于其他的工具，显然 Elasticsearch 社区更加活跃，遇到问题相对来说也比较好解决，另外 Elasticsearch 提供的 restful 接口操作起来还是比较方便的，这也是楼主选择 Elasticsearch 的重要原因，当然 Elasticsearch 占据的内存相对来说比较大，楼主 2G 的云服务器跑起来也是捉襟见肘。

## [](#数据迁移，从-MySQL-到-Elasticsearch "#数据迁移，从-MySQL-到-Elasticsearch")数据迁移，从 MySQL 到 Elasticsearch

这个功能相对来说比较简单，就是定时从 MySQL 更新数据到 Elasticsearch 中，本来楼主打算自己写一个数据迁移的工具，但是想起之前楼主做数据迁移时用到的 DataX 很是不错，看了下官方文档还是支持的，但是楼主硬是没有跑起来，原因就是楼主 2G 内存的云服务器不够使啊，DataX 光是跑起来就要 1G 多的内存，所以楼主只能另谋它法。对 DataX 感兴趣的小伙伴可以看看楼主的另一篇文章<a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2018%2F4928%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/article/2018/4928/">阿里离线数据同步工具 DataX 踩坑记录</a>。

说起可以省内存的语言，小伙伴可能会想到最近比较火的 golang，没错楼主也想到了。最后楼主使用的就是一个叫 go-mysql-elasticsearch 的工具，它是使用 golang 实现的从 MySQL 将数据迁移到 Elasticsearch 的工具。具体搭建过程楼主不在这里细说，感兴趣的小伙伴请移步<a href="https://link.juejin.cn?target=https%3A%2F%2Fgithub.com%2Fsiddontang%2Fgo-mysql-elasticsearch" target="_blank" data-ref="nofollow noopener noreferrer" title="https://github.com/siddontang/go-mysql-elasticsearch">go-mysql-elasticsearch</a>，另外 Elasticsearch 环境的搭建，需要注意的就是安装 Elasticsearch 的机器内存应该大于或者等于 2G，否则可能会出现启动不起来的情况，楼主也不在这里赘述了，比较简单，请小伙伴们自行 google。

另外需要注意的是，在使用 go-mysql-elasticsearch 的时候应该开启 MySQL 的 binlog 功能，go-mysql-elasticsearch 实现数据同步的思想就是将自己作为 MySQL 的一个 slave 挂载在 MySQL 上，这样就可以很轻松地将数据实时同步到 Elasticsearch 中，在启动 go-mysql-elasticsearch 的机器上最少应该有 MySQL client 工具，否则会启动报错。楼主的建议是跟 MySQL 部署在同一台机器上，因为 golang 耗费内存极少，并不会有太大影响。下面给出楼主同步数据时 go-mysql-elasticsearch 的配置文件：

    # MySQL address, user and password
    # user must have replication privilege in MySQL.
    my_addr = "127.0.0.1:3306"
    my_user = "root"
    my_pass = "******"
    my_charset = "utf8"

    # Set true when elasticsearch use https
    #es_https = false
    # Elasticsearch address
    es_addr = "127.0.0.1:9200"
    # Elasticsearch user and password, maybe set by shield, nginx, or x-pack
    es_user = ""
    es_pass = ""

    # Path to store data, like master.info, if not set or empty,
    # we must use this to support breakpoint resume syncing.
    # TODO: support other storage, like etcd.
    data_dir = "./var"

    # Inner Http status address
    stat_addr = "127.0.0.1:12800"

    # pseudo server id like a slave
    server_id = 1001

    # mysql or mariadb
    flavor = "mysql"

    # mysqldump execution path
    # if not set or empty, ignore mysqldump.
    mysqldump = "mysqldump"

    # if we have no privilege to use mysqldump with --master-data,
    # we must skip it.
    #skip_master_data = false

    # minimal items to be inserted in one bulk
    bulk_size = 128

    # force flush the pending requests if we don't have enough items >= bulk_size
    flush_bulk_time = "200ms"

    # Ignore table without primary key
    skip_no_pk_table = false

    # MySQL data source
    [[source]]
    schema = "billboard-blog"

    # Only below tables will be synced into Elasticsearch.
    tables = ["content"]
    # Below is for special rule mapping
    [[rule]]
    schema = "billboard-blog"
    table = "content"
    index = "contentindex"
    type = "content"

    [rule.field]
    title="title"
    blog_desc="blog_desc"
    content="content"


    # Filter rule
    [[rule]]
     schema = "billboard-blog"
     table = "content"
     index = "contentindex"
     type = "content"

    # Only sync following columns
    filter = ["title", "blog_desc", "content"]

    # id rule
    [[rule]]
     schema = "billboard-blog"
     table = "content"
     index = "contentindex"
     type = "content"
     id = ["id"]

## [](#实现全文检索功能的服务 "#实现全文检索功能的服务")实现全文检索功能的服务

要想实现全文检索的功能并对外提供服务，web 服务必不可少，楼主使用 Spring Boot 搭建 web 服务，对 Spring Boot 感兴趣的小伙伴也可以看一下楼主的另一篇文章，<a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2018%2F6f25%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/article/2018/6f25/">使用 Spring Boot 实现博客统计服务</a>。好了废话不多说了，请看代码

接口实现代码，代码比较简单就是接收参数，调用 service 代码

    @ApiOperation(value="全文检索接口", notes="")
    @ApiImplicitParam(name = "searchParam", value = "博客搜索条件（作者，描述，内容，标题）", required = true, dataType = "String")
    @RequestMapping(value = "/get_content_list_from_es", method = RequestMethod.GET)
    public ResultCode<List<ContentsWithBLOBs>> getContentListFromEs(String searchParam) {
        ResultCode<List<ContentsWithBLOBs>> resultCode = new ResultCode();
        try {
            LOGGER.info(">>>>>> method getContentListFromEs request params : {},{}，{}",searchParam);
            resultCode = contentService.getContentListFromEs(searchParam);
            LOGGER.info(">>>>>> method getContentListFromEs return value : {}",JSON.toJSONString(resultCode));
        } catch (Exception e) {
            e.printStackTrace();
            resultCode.setCode(Messages.API_ERROR_CODE);
            resultCode.setMsg(Messages.API_ERROR_MSG);
        }
        return resultCode;
    }

service 代码实现，这里的代码主要功能就是调用 es 的工具类，对博客描述，作者，博客标题，博客内容进行全文检索。

    @Override
    public ResultCode<List<ContentsWithBLOBs>> getContentListFromEs(String searchParam) {
        ResultCode resultCode = new ResultCode();

        // 校验参数，参数不能为空
        if (StringUtils.isBlank(searchParam)) {
            LOGGER.info(">>>>>> params not be null");
            resultCode.setMsg(Messages.INPUT_ERROR_MSG);
            resultCode.setCode(Messages.INPUT_ERROR_CODE);
            return resultCode;
        }

        String matchStr = "blog_desc=" + searchParam;
        List<Map<String, Object>> result = ElasticsearchUtils.searchListData(BillboardContants.ES_CONTENT_INDEX,BillboardContants.ES_CONTENT_TYPE,BillboardContants.ES_CONTENT_FIELD,true,matchStr);

        matchStr = "author=" + searchParam;
        result.addAll(ElasticsearchUtils.searchListData(BillboardContants.ES_CONTENT_INDEX,BillboardContants.ES_CONTENT_TYPE,BillboardContants.ES_CONTENT_FIELD,true,matchStr));

        matchStr = "title=" + searchParam;
        result.addAll(ElasticsearchUtils.searchListData(BillboardContants.ES_CONTENT_INDEX,BillboardContants.ES_CONTENT_TYPE,BillboardContants.ES_CONTENT_FIELD,true,matchStr));

        matchStr = "content=" + searchParam;
        result.addAll(ElasticsearchUtils.searchListData(BillboardContants.ES_CONTENT_INDEX,BillboardContants.ES_CONTENT_TYPE,BillboardContants.ES_CONTENT_FIELD,true,matchStr));

        List<ContentsWithBLOBs> data = JSON.parseArray(JSON.toJSONString(result),ContentsWithBLOBs.class);
        LOGGER.info("es return data : {}",JSON.toJSONString(result));
        resultCode.setData(data);
        return resultCode;
    }

楼主用到的 es 的工具类代码实现，就是使用 es 的 Java 客户端对 es 进行检索。

    /**
     * 使用分词查询
     *
     * @param index       索引名称
     * @param type        类型名称,可传入多个type逗号分隔
     * @param fields      需要显示的字段，逗号分隔（缺省为全部字段）
     * @param matchPhrase true 使用，短语精准匹配
     * @param matchStr    过滤条件（xxx=111,aaa=222）
     * @return
     */
    public static List<Map<String, Object>> searchListData(String index, String type, String fields, boolean matchPhrase, String matchStr) {
        return searchListData(index, type, 0, 0, null, fields, null, matchPhrase, null, matchStr);
    }

    /**
     * 使用分词查询
     *
     * @param index          索引名称
     * @param type           类型名称,可传入多个type逗号分隔
     * @param startTime      开始时间
     * @param endTime        结束时间
     * @param size           文档大小限制
     * @param fields         需要显示的字段，逗号分隔（缺省为全部字段）
     * @param sortField      排序字段
     * @param matchPhrase    true 使用，短语精准匹配
     * @param highlightField 高亮字段
     * @param matchStr       过滤条件（xxx=111,aaa=222）
     * @return
     */
    public static List<Map<String, Object>> searchListData(String index, String type, long startTime, long endTime, Integer size, String fields, String sortField, boolean matchPhrase, String highlightField, String matchStr) {

        SearchRequestBuilder searchRequestBuilder = client.prepareSearch(index);
        if (StringUtils.isNotEmpty(type)) {
            searchRequestBuilder.setTypes(type.split(","));
        }
        BoolQueryBuilder boolQuery = QueryBuilders.boolQuery();

        if (startTime > 0 && endTime > 0) {
            boolQuery.must(QueryBuilders.rangeQuery("processTime")
                    .format("epoch_millis")
                    .from(startTime)
                    .to(endTime)
                    .includeLower(true)
                    .includeUpper(true));
        }

        //搜索的的字段
        if (StringUtils.isNotEmpty(matchStr)) {
            for (String s : matchStr.split(",")) {
                String[] ss = s.split("=");
                if (ss.length > 1) {
                    if (matchPhrase == Boolean.TRUE) {
                        boolQuery.must(QueryBuilders.matchPhraseQuery(s.split("=")[0], s.split("=")[1]));
                    } else {
                        boolQuery.must(QueryBuilders.matchQuery(s.split("=")[0], s.split("=")[1]));
                    }
                }

            }
        }

        // 高亮（xxx=111,aaa=222）
        if (StringUtils.isNotEmpty(highlightField)) {
            HighlightBuilder highlightBuilder = new HighlightBuilder();

            //highlightBuilder.preTags("<span style='color:red' >");//设置前缀
            //highlightBuilder.postTags("</span>");//设置后缀

            // 设置高亮字段
            highlightBuilder.field(highlightField);
            searchRequestBuilder.highlighter(highlightBuilder);
        }


        searchRequestBuilder.setQuery(boolQuery);

        if (StringUtils.isNotEmpty(fields)) {
            searchRequestBuilder.setFetchSource(fields.split(","), null);
        }
        searchRequestBuilder.setFetchSource(true);

        if (StringUtils.isNotEmpty(sortField)) {
            searchRequestBuilder.addSort(sortField, SortOrder.DESC);
        }

        if (size != null && size > 0) {
            searchRequestBuilder.setSize(size);
        }

        //打印的内容 可以在 Elasticsearch head 和 Kibana  上执行查询
        LOGGER.info("\n{}", searchRequestBuilder);

        SearchResponse searchResponse = searchRequestBuilder.execute().actionGet();

        long totalHits = searchResponse.getHits().totalHits;
        long length = searchResponse.getHits().getHits().length;

        LOGGER.info("共查询到[{}]条数据,处理数据条数[{}]", totalHits, length);

        if (searchResponse.status().getStatus() == 200) {
            // 解析对象
            return setSearchResponse(searchResponse, highlightField);
        }

        return null;

    }

最后，楼主使用 postman 测试 web 服务，如下图所示：

<a href="https://link.juejin.cn?target=http%3A%2F%2Fimg.hchstudio.cn%2Fpostman_es.png" target="_blank" data-ref="nofollow noopener noreferrer" title="http://img.hchstudio.cn/postman_es.png"><img src="https://p1-jj.byteimg.com/tos-cn-i-t2oaga2asx/gold-user-assets/2018/7/12/1648c8ba4bdfe787~tplv-t2oaga2asx-jj-mark:3024:0:0:0:q75.png" loading="lazy" alt="postman图" /></a>postman 图

## [](#过程中遇到的坑 "#过程中遇到的坑")过程中遇到的坑

### [](#IK分词器的设置 "#IK分词器的设置")IK 分词器的设置

这里需要注意的是，Elasticsearch 的版本一定要与 ik 分词器的版本对应，不对应的话 Elasticsearch 会报错的。

    $ ./bin/elasticsearch-plugin install https://github.com/medcl/elasticsearch-analysis-ik/releases/download/v6.3.0/elasticsearch-analysis-ik-6.3.0.zip

接着，重新启动 Elastic，就会自动加载这个新安装的插件。

然后，新建一个 Index，指定需要分词的字段。这一步根据数据结构而异，下面的命令只针对本文。基本上，凡是需要搜索的中文字段，都要单独设置一下。

    $ curl -X PUT 'localhost:9200/contentindex'  -H 'Content-Type: application/json' -d '
    {
      "mappings": {
        "content": {
          "properties": {
            "content": {
              "type": "text",
              "analyzer": "ik_max_word",
              "search_analyzer": "ik_max_word"
            },
            "title": {
              "type": "text",
              "analyzer": "ik_max_word",
              "search_analyzer": "ik_max_word"
            },
            "blog_desc": {
              "type": "text",
              "analyzer": "ik_max_word",
              "search_analyzer": "ik_max_word"
            },
            "author": {
              "type": "text",
              "analyzer": "ik_max_word",
              "search_analyzer": "ik_max_word"
            }
          }
        }
      }
    }'

上面代码中，首先新建一个名称为 contentindex 的 Index，里面有一个名称为 content 的 Type。content 有好多个字段，这里只为其中四个字段指定分词，**content**，**title**，**blog_desc**，**author**。

这四个字段都是中文，而且类型都是文本（text），所以需要指定中文分词器，不能使用默认的英文分词器。

### [](#MySQL-binlog的设置 "#MySQL-binlog的设置")MySQL binlog 的设置

因为楼主运行 go-mysql-elasticsearch 的时候使用的 MySQL 的客户端跟要导出数据的 MySQL server 端的版本不一致导致报错，最终在 go-mysql-elasticsearch 原作者的帮助下解决，所以一定要使用同版本的 MySQL server 与 client，因为不同版本的 MySQL 特性不一样，也就导致了 go-mysql-elasticsearch 导出数据有略微的不同。

## [](#小结 "#小结")小结

整个过程相对来说比较简单，当然楼主通过这个功能的实现，也对 es 有了一个相对的认识，学习了一项新的技能，可能有的小伙伴对楼主的整个工程的代码比较感兴趣，暂时不能透露，等楼主完善好了一并贡献出来。

## [](#参考文章 "#参考文章")参考文章

- <a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.ruanyifeng.com%2Fblog%2F2017%2F08%2Felasticsearch.html" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.ruanyifeng.com/blog/2017/08/elasticsearch.html">全文搜索引擎 Elasticsearch 入门教程</a>

作 者：haifeiWu\
原文链接：<a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2018%2F2150%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/article/2018/2150/">www.hchstudio.cn/article/201…</a>\
版权声明：非特殊声明均为本站原创作品，转载时请注明作者和原文链接。
