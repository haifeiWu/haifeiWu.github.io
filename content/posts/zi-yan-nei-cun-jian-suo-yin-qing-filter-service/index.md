---
categories: ["后端"]
title: "自研内存检索引擎：筛选服务（Filter Service）的架构与设计取舍"
date: "2026-09-14T16:20:00+08:00"
tags: ["Go", "搜索引擎", "倒排索引", "位图", "架构设计"]
summary: "一套约 2.7 万行 Go 代码的自研内存检索引擎，支撑教育选课场景的高并发条件筛选。本文拆解它的倒排索引与位图运算、火山模型执行树、快照持久化与 Etcd 主备选举，也记录源码里几处值得注意的设计取舍。"
---

做检索，第一反应通常是 Elasticsearch。但如果把场景收窄——数据量在十万级、字段类型基本是整数与枚举、筛选条件组合极其灵活、要求毫秒级返回且不想维护一个独立集群——那么"自研一个内存检索引擎"就从一个疯狂的想法变成了一个可以在可控成本内落地的工程问题。

本文要拆解的 `filter` 仓库，就是这么一套东西：约 **2.7 万行 Go 代码、162 个源文件**，实现了一个对标轻量级 Elasticsearch 的内存筛选引擎，业务上支撑教育场景的选课搜索（课程、课程包、老师三类对象的筛选、排序、分页、分组与聚合）。

文章的写法是"顺着代码读下去"：先讲清它怎么组织数据、怎么执行查询，再讲快照与高可用，最后把**读代码过程中发现的几处值得记录的取舍与坑点**单独拿出来讨论——这部分是我认为比架构图更有价值的内容。

> **关于代码片段**：文中代码摘自 `filter` 仓库，为便于阅读省略了部分日志输出、错误处理与锁操作，变量命名与核心逻辑保持原样，每处都标注了所在文件。

## 一、先看问题：这套引擎要解决什么

选课场景的检索请求有几个鲜明特征：

- **QPS 高、请求密集**。用户在前端不断勾选筛选条件（年级、学科、学期、难度、版本、价格区间、省份、设备、老师……），每一次勾选变化几乎都会触发一次检索。
- **结果集不大，但条件组合极多**。一次检索最终返回的往往只有几十条，但参与筛选的字段有十几个，且组合方式由用户自由决定。
- **数据规模可控**。课程、老师这类对象是万级到十万级，远没有到必须依赖分布式检索集群的量级。
- **业务字段变化频繁**。中台体系（文中称"乐高"体系）会不断调整字段语义、映射规则和排序权重，检索层需要快速适配。

用 Elasticsearch 当然能做，但要付出集群运维、JVM 内存、网络往返、mapping 变更这几项成本。而这里的数据规模小到**可以完整放进单机内存**——一旦接受这个前提，倒排索引 + 位图运算就能把这个场景做到极致：没有网络、没有磁盘 IO、没有序列化开销。

## 二、三套程序与整体分层

仓库里其实包含三套独立运行的程序：

| 程序 | 定位 | 说明 |
|------|------|------|
| `filter-server` | 筛选引擎服务 | 常驻 HTTP 服务，提供检索、文档/索引管理、快照导入导出 |
| `course` | 课程数据同步任务 | 离线/定时 ETL，把业务库数据加工后批量写入引擎 |
| `course-count` | 购课数统计任务 | 基于引擎快照并行统计购课数并写回业务库 |

整体分四层，外加数据生产链路与消费端：

{{< mermaid >}}
flowchart TB
    subgraph 消费端
        APP["App / Web / 选课中台"]
    end

    subgraph 生产链路
        MYSQL[("业务 MySQL")]
        ETL["course 数据同步任务<br/>生产者-消费者流水线"]
        CC["course-count 购课数统计<br/>快照导入 + 并行计数"]
        STAT[("统计 MySQL")]
    end

    subgraph 引擎["filter-server 筛选引擎"]
        subgraph 接入层
            HTTP["HTTP 服务（Gin）<br/>search / doc / index / db 路由"]
        end
        subgraph 查询处理层
            PARSER["Parser<br/>JSON DSL → 查询计划"]
            EXEC["Executor<br/>执行树 Open / Next / Close"]
            AGG["聚合器<br/>桶聚合 + 指标聚合"]
        end
        subgraph 存储引擎层
            MEM[("内存 DB<br/>多索引管理")]
            INVERT["字段倒排索引<br/>哈希 / 跳表"]
            BITMAP["文档位图<br/>RoaringBitmap 交并差"]
        end
    end

    subgraph 基础组件
        ETCD[("Etcd<br/>主备选举")]
        NACOS["Nacos<br/>动态配置"]
        STORE[("持久化 Store<br/>Redis / OSS / 文件")]
    end

    APP -->|检索请求| HTTP
    HTTP --> PARSER --> EXEC
    EXEC --> AGG
    EXEC --> MEM
    AGG --> MEM
    MEM --> INVERT
    MEM --> BITMAP

    MYSQL -->|原始数据| ETL
    ETL -->|批量写入文档| HTTP
    MEM -->|定时导出快照| STORE
    STORE -->|导入快照| MEM
    STORE -->|读取快照| CC
    CC -->|统计结果| STAT

    ETCD -. 主备竞选 .-> MEM
    NACOS -. 配置下发 .-> HTTP
{{< /mermaid >}}

这个分层里最值得注意的一点是：**查询处理与存储是解耦的，而且读取路径上没有锁**。查询全程只读内存索引，写入（文档变更、快照导入）才加锁，因此一次耗时的快照导入不会长时间阻塞查询。

## 三、存储引擎：倒排索引与位图

### 3.1 文档模型：只存"原始 JSON"

```go
type Doc struct {
	ID         int    `json:"id"`
	JSONValues string `json:"json_values"`
	fields     sync.Map
}
```

文档的原始 JSON 以**字符串**形式原样保存，不解码成结构体；同时把需要检索的字段值解析成 `[]int` 另存一份在 `fields` 里。

这个设计贯穿始终：**检索阶段只碰 `int` 数组和位图，绝不反序列化 JSON**；只有最后要把结果吐给业务方时，才把 `JSONValues` 作为 `json.RawMessage` 直接拼进响应体。省掉的是整个查询链路上反复的 JSON 解析开销。

### 3.2 字段索引的两种形态

每个索引（Index）下按字段建立 `FieldIndex`：

```go
type FieldIndex struct {
	Ctx       context.Context
	Field     string
	Type      int64
	IndexType string
	Hash      *FieldIndexHash
	SkipList  *skiplist.SkipList

	index *Index

	// string to int
	lastID      int64
	stringToInt sync.Map
}
```

（`Type` 取值 `TypeInt` / `TypeKeyword`；`IndexType` 取值为 `IndexTypeRange = "range"` 时才有跳表。`Hash` 负责精确匹配，`SkipList` 负责范围匹配。）

关键的一行判断在构造函数里：

```go
if i.IndexType == IndexTypeRange {
	i.SkipList = skiplist.NewIntMap()
}
```

**并不是所有字段都付出跳表的代价**。只有显式声明为 `range` 的字段才建立有序结构，其余字段只保留 `值 → 位图` 的哈希映射。这是"按字段的实际查询模式分配存储成本"的典型做法——一个只做枚举筛选的字段，维护有序性纯属浪费。

### 3.3 被改造过的跳表：节点上挂位图

仓库里的跳表实现是从 Google 的开源实现改的（保留了原版注释与作者署名），改动点很小但很关键——`node` 结构体里多了位图：

```go
type node struct {
	forward    []*node
	backward   *node
	key, value interface{}
	bitmap     []*roaring.Bitmap
}
```

为什么要在跳表节点上挂位图？因为范围查询的诉求是"值落在 [1000, 5000] 区间内的所有文档"，而跳表只给了值的有序性，还需要把区间内每个值对应的文档集合合并起来。

做法是：**让跳表的每个节点直接持有"该节点及之前所有节点"的累积位图**。这样区间查询只需要定位到区间的上下界、取出两个累积位图做一次差集，而不需要遍历区间内所有值再逐个求并。有序性和集合运算被合并到一次操作里完成：

```go
func (i *FieldIndex) ThroughBetween(gt *int, gte *int, lt *int, lte *int) (*DocIDSet, error) {
	if i.IndexType != IndexTypeRange {
		return nil, fmt.Errorf("field index %s does not support range search", i.Field)
	}
	return &DocIDSet{bitmap: i.SkipList.ThroughBetween(gt, gte, lt, lte)}, nil
}
```

### 3.4 字符串编码为整数：位图化的前提

位图只能装整数，而业务字段里有大量字符串枚举（学科名、版本名、难度名……）。引擎的解法是在写入时把字符串编码成自增整数，一次编码同时解决两个问题：

```go
func (i *FieldIndex) ConvertStrToInt(value string) int {
	if v, ok := i.stringToInt.Load(value); ok {
		return v.(int)
	}

	// get last id
	v := atomic.AddInt64(&i.lastID, 1)
	i.stringToInt.Store(value, int(v))

	if i.index.Dict == nil {
		i.index.Dict = make(map[string]map[string]string)
	}
	if i.index.Dict[i.Field] == nil {
		i.index.Dict[i.Field] = make(map[string]string)
	}
	i.index.Dict[i.Field][strconv.Itoa(int(v))] = value

	return int(v)
}
```

- 正向映射 `stringToInt`：让字符串字段也能参与位图运算；
- 反向字典 `index.Dict`：结果返回前把编码翻译回可读值（业务方看到的是"数学"而不是 `7`）。

两件事用一次编码一起做完，不用维护两套结构。代价是字典**只增不减**——删除文档不会回收已分配的编码。对低基数的枚举字段（学科、年级、难度）这是完全合理的取舍；但如果把它用在高基数、高频变更的字段上（比如用户 ID），字典会持续膨胀，这是使用时必须注意的边界。

### 3.5 DocIDSet：把位图运算包装成语义

```go
type DocIDSet struct {
	bitmap *roaring.Bitmap
}

func (s *DocIDSet) And(docIDSet *DocIDSet)    { s.bitmap.And(docIDSet.bitmap) }
func (s *DocIDSet) Or(docIDSet *DocIDSet)     { s.bitmap.Or(docIDSet.bitmap) }
func (s *DocIDSet) AndNot(docIDSet *DocIDSet) { s.bitmap.AndNot(docIDSet.bitmap) }
func (s *DocIDSet) Count() int                { return int(s.bitmap.GetCardinality()) }
```

底层是 RoaringBitmap（压缩位图）。十万级文档规模下，多个条件的交、并、差就是几次微秒级的位运算——这正是"毫秒级筛选"的物理基础。

### 3.6 写入路径：先拆旧再建新

```go
func (i *Index) Index(doc *Doc) error {
	i.lock.Lock()
	defer i.lock.Unlock()

	if docOld, ok := i.Get(doc.ID); ok {
		i.FieldIndices.Range(func(key, value interface{}) bool {
			field := key.(string)
			index := value.(*FieldIndex)
			if v, ok := docOld.fields.Load(field); ok {
				for _, value := range v.([]int) {
					index.Delete(doc.ID, value)   // 按旧值逐一撤位
				}
			}
			return true
		})
		i.Docs.Delete(doc.ID)
	}

	i.Docs.Index(doc)
	i.FieldIndices.Range(func(key, value interface{}) bool {
		value.(*FieldIndex).IndexDoc(doc)         // 按新值重新占位
		return true
	})
	return nil
}
```

这是一个幂等的"重建式更新"：同一个 ID 反复写入不会有重复。代价是每次更新都要遍历**所有字段索引**（而不是只处理实际变化的字段），更新成本与字段总数成正比。对于"批量导入为主、单文档更新为辅"的场景，这个取舍是划算的——它把复杂度换成了正确性。

## 四、查询引擎：DSL → 计划 → 执行树

### 4.1 类 Elasticsearch 的 JSON DSL

对外接口是一套类 ES 的查询 DSL：

```json
{
  "index": "index-course",
  "query": {
    "bool": {
      "must":     [{ "term":  { "field": "lego_grade_id", "value_int": 3 } }],
      "filter":   [{ "range": { "field": "price", "gte": 1000, "lte": 5000 } }],
      "must_not": [{ "terms": { "field": "teacher_id", "values": [1, 2] } }]
    }
  },
  "sort": [{ "price": { "order": "desc" } }],
  "from": 0,
  "size": 20,
  "aggs": { "by_grade": { "terms": { "field": "lego_grade_id" } } }
}
```

解析用的是 `gjson` 而不是标准库的 `encoding/json`：**按路径取值，只解析需要的部分**，避免为一次查询把整个请求体反序列化成结构体。同时解析器用注册表模式组织，新增一种条件类型只需要多加一个 parser：

```go
var queryParsers = map[string]queryParser{
	"term":  parseTermQuery,
	"terms": parseTermsQuery,
	"range": parseRangeQuery,
}
```

### 4.2 三个阶段

```text
JSON DSL  ──Parser──▶  planner.Search（查询计划）  ──Builder──▶  Exec 执行树  ──Execute──▶  Chunk 结果
           语法校验            模型化：查询/排序/分组/聚合            组装算子树            执行
```

`planner` 层把 DSL 变成一个纯数据模型（`Search` / `Q` / `BoolQuery` / `Sort` / `Aggs`），与执行完全解耦。这一层还顺带承载了业务侧传入的参数（品牌、设备、省份、年级等），为后面的执行阶段提供上下文。

### 4.3 执行树：一个"倒着组装"的顺手写法

执行树由 `ExecutorBuilder.BuildSearch` 组装，写法很有意思——**按业务重要性的反序挂载，最后挂查询条件**：

```go
// executor/builder.go
search := newSearchExec(b.session)
current = search

if len(s.Group) > 0 {
	limit := newGroupLimitExec(b.session)
	limit.setLimit(s.From, s.Size)
	current.base().children = append(current.base().children, limit)
	current = limit
	if len(s.Sort) > 0 {
		sort := newGroupSortExec(b.session, index)
		sort.setSortItems(ctx, s.Sort)
		current.base().children = append(current.base().children, sort)
		current = sort
	}
} else {
	limit := newLimitExec(b.session)
	limit.setLimit(s.From, s.Size)
	current.base().children = append(current.base().children, limit)
	current = limit
	if len(s.Sort) > 0 {
		sort := newSortExec(b.session, index)
		sort.setSortItems(ctx, s.Sort)
		current.base().children = append(current.base().children, sort)
		current = sort
	}
}

if s.Aggs != nil {
	aggs := b.buildAggs(s.Aggs)        // 聚合
	current.base().children = append(current.base().children, aggs)
	current = aggs
}

if len(s.Group) > 0 {
	group := newGroupExec(ctx, b.session, index, s.Group, s.GroupSort)
	current.base().children = append(current.base().children, group)
	current = group
}

if s.Query != nil {
	query := b.buildQuery(ctx, s.Query)   // 查询条件 —— 最后挂，成为叶子
	current.base().children = append(current.base().children, query)
}
```

（上面省去了各步骤的错误处理，保留了参数与调用顺序。）

每挂一个算子就把 `current` 指向它，最终形成一条链。执行时数据从叶子向根流动：

{{< mermaid >}}
flowchart TD
    SEARCH["SearchExec<br/>（返回结果）"] --> LIMIT["LimitExec<br/>切片分页"]
    LIMIT --> SORT["SortExec<br/>排序"]
    SORT --> AGG["AggregateExec<br/>聚合"]
    AGG --> GROUP["GroupExec<br/>分组"]
    GROUP --> QUERY["QueryExec<br/>位图筛选"]
    QUERY -. 数据从叶子逐层向上流动 .-> SEARCH
{{< /mermaid >}}

这种写法的好处是**心里不用反着建树**：从"用户最终拿到什么"开始写，分页、排序、聚合依次往上挂，最底层的筛选最后写。Builder 的代码顺序和业务的阅读顺序一致。

### 4.4 火山模型：Open / Next / Close

所有算子实现同一个接口：

```go
type Exec interface {
	base() *baseExec
	Open(context.Context) error
	Next(ctx context.Context, chunk *Chunk) error
	Close() error
}
```

`baseExec` 提供了默认实现，把递归遍历子节点这件事统一掉了：

```go
func (e *baseExec) Open(ctx context.Context) error {
	for _, child := range e.children {
		if err := child.Open(ctx); err != nil { return err }
	}
	return nil
}

func (e *baseExec) Close() error {
	var firstErr error
	for _, src := range e.children {
		if err := src.Close(); err != nil && firstErr == nil { firstErr = err }
	}
	return firstErr
}
```

于是每个算子只需要写自己的 `Next`。新增一种查询算子 = 新增一个文件 + 在 Builder 里挂一行，不需要改任何已有算子。这是这套引擎可扩展性的来源。

### 4.5 Chunk：算子间的数据单元与"惰性物化"

`Chunk` 是整个引擎里最关键的抽象：

```go
type Chunk struct {
	Index     *db.Index
	Total     int
	DocIDSet  *db.DocIDSet    // 位图：筛选阶段的唯一载体
	Docs      []*db.Doc       // 文档：只在需要时才物化
	SortItems []planner.Sort
	Sorted    bool
	Limited   bool
	Aggs      []aggregation.Agg
	Groups    []*Group
	Grouped   bool
	PinnedOrder map[int]int
}
```

它的核心设计是**位图与文档分离**：筛选阶段（布尔运算）全程只操作 `DocIDSet`，完全不碰文档对象；直到最后一个算子需要输出结果时才把 ID 批量换成文档：

```go
func (c *Chunk) GetDocs() []*db.Doc {
	if len(c.Docs) == 0 && !c.Sorted && !c.Limited {
		ids := c.docIDs()                  // 位图 → ID 数组
		if len(ids) > 0 {
			c.Docs = c.Index.GetMany(ids)  // 批量取文档
		}
	}
	return c.Docs
}
```

一次典型的选课查询可能从十万文档筛到几十条，而这十万次"排除"的代价只是几次位图与运算——**没有一次文档解引用，没有一次 JSON 解析**。这就是毫秒级的来源。

`Count()` 也跟着做了区分：还没物化时直接读位图基数，物化之后就用切片长度。

```go
func (c *Chunk) Count() int {
	if len(c.Docs) == 0 && !c.Limited {
		return c.DocIDSet.Count()
	}
	return len(c.Docs)
}
```

### 4.6 布尔查询：筛选就是位图运算

`must` 与 `filter` 的实现几乎一样——都是把子条件的结果逐个求交：

```go
func (e *MustQueryExec) Next(ctx context.Context, chunk *Chunk) error {
	first := true
	for _, child := range e.children {
		c := NewChunk()
		if err := child.Next(ctx, c); err != nil { return err }

		if first {
			chunk.SetDocIDSet(c.DocIDSet)   // 第一个条件作为起点
			first = false
		} else {
			chunk.And(c)                    // 后续条件逐个求交
		}
	}
	chunk.Index = e.index
	return nil
}
```

`must_not` 则是"先并后排"——把多个排除条件先并成一个集合，再对结果做差集：

```go
func (e *MustNotQueryExec) Next(ctx context.Context, chunk *Chunk) error {
	mustNotChunk := NewChunk()
	first := true
	for _, child := range e.children {
		if first {
			child.Next(ctx, mustNotChunk)   // 第一个排除条件
			first = false
		} else {
			c := NewChunk()
			child.Next(ctx, c)
			mustNotChunk.And(c)             // 多个排除条件取交集
		}
	}

	chunk.AndNot(mustNotChunk)              // 对当前结果集做差集
	chunk.Index = e.index
	return nil
}
```

注意这里有个容易被忽略的语义：**`must_not` 是对"上游已经收敛的结果集"做差**，而不是先在全量数据上排除再筛选。因为布尔算子的子节点顺序就是 `must → filter → must_not`，执行到这里时结果集已经很小了，差集操作的位图规模也随之变小。这个顺序对性能是友好的（后面会看到，它对正确性也有影响）。

至于 `must` 和 `filter` 在实现上完全一致——在这套引擎里没有相关性打分环节，两者的区别只剩下语义表达，保留两个名字是为了和 ES 的使用习惯对齐。这也是自研引擎的一个隐性好处：**不需要为不存在的功能付出复杂度**。

## 五、排序与分组

### 5.1 排序：一次针对性的捷径

```go
e.Docs = chunk.GetDocs()
if e.SortItems[0].Field == "id" {
	if e.SortItems[0].IsDesc {
		reverse(e.Docs)          // 降序：反转
	}
	// 升序：什么都不做
} else {
	sort.Sort(e)                 // 其他字段：比较排序
}
```

按 `id` 排序时完全跳过比较排序：升序什么都不做，降序只反转一次。

这条捷径的正确性来自一个容易被忽略的细节——**`DocIDSet.ToArray()` 返回的 ID 天然是升序的**：

```go
// db/doc.go
func (s *DocIDSet) ToArray() []int {
	docIDs := make([]int, 0)
	for _, k := range s.bitmap.ToArray() {     // RoaringBitmap.ToArray() 保证升序
		docIDs = append(docIDs, int(k))
	}
	return docIDs
}
```

而 `Chunk.GetDocs()` 正是通过 `DocIDSet.ToArray()` → `DocSet.GetMany(ids)` 取文档的，`GetMany` 保持传入顺序：

```go
// db/doc.go
func (s *DocSet) GetMany(ids []int) []*Doc {
	var docs []*Doc
	for _, id := range ids {
		if d, ok := s.Get(id); ok {
			docs = append(docs, d)
		}
	}
	return docs
}
```

所以"按 id 升序"是**压缩位图的固有性质顺带送来的**，而不是因为存储层维护了什么有序结构。值得一提的反例是 `DocSet` 底下其实是 `sync.Map`（无序），`GetAll()` 拿到的序列顺序并不确定；`GetAllOrdered()` 才是显式做了 `sort.Ints`。用哪个方法，决定了"按 id 排序"这条捷径是否成立——这一点在 11.5 里会再提到。

选课场景里"按 id 排序"常被用作默认排序，所以这条捷径命中的频率不低。这是"识别真实业务高频路径并为它开一条专门通道"的典型例子——代码不优雅，但收益明确。

### 5.2 多字段排序与缺失值处理

```go
func (e *SortExec) Less(i, j int) bool {
	for _, item := range e.SortItems {
		var left, right int
		switch item.Field {
		case "teacher_intimacy":
			// ……虚拟字段，见 5.3
		default:
			if values, ok := e.Docs[i].Field(item.Field); ok {
				left = values[0]
			} else {
				continue     // 字段缺失：跳过这个排序键，交给下一个
			}
			if values, ok := e.Docs[j].Field(item.Field); ok {
				right = values[0]
			} else {
				continue
			}
			if left == right { continue }
			if item.IsDesc { return left > right }
			return left < right
		}
	}
	return e.Docs[i].ID < e.Docs[j].ID    // 全部相等时按 ID 兜底
}
```

两个细节值得记：

1. **字段缺失时 `continue`**，把决定权交给下一个排序键。比"缺失一律排最后"更灵活，但也意味着缺失值排序依赖于后续字段；
2. **最后的 `return e.Docs[i].ID < e.Docs[j].ID` 是必需的**。在多字段排序里，如果所有键都相等就返回 `false`，`sort.Sort`（非稳定排序）会让相等元素的相对顺序不确定，分页时就会出现同一文档在不同页重复出现或漏掉。这个兜底保证了全序关系的唯一性。

### 5.3 虚拟排序字段：把业务权重从索引里挪出来

`teacher_intimacy`（老师亲密值）是一个**不在任何索引里**的排序字段。它的值由 `(老师ID, 学科, 年级)` 三元组从业务配置字典里查出来：

```go
leftKey := genTeacherIntimacyKey(leftTeacherID, subject3IDs[0], gradeIDs[0])
if value, ok := e.session.Server.ConfigBiz().TeacherIntimacy[leftKey]; ok {
	left = value
}
```

这个设计的价值在于**把"随业务策略变化的排序权重"从索引结构中剥离**：调整老师排序策略（运营侧常做的事）不需要重建索引、不需要重新推送数据，只要更新配置即可生效。

代价也很明确：排序的比较次数是 O(n log n)，而每次比较都要拼字符串 key + 查 map，这个常数不小。属于"语义灵活性"换来的热路径开销——一个很典型、也很值得优化的点（在 11.5 里会再提到）。

### 5.4 分组：用多叉前缀树表达层级

多字段分组的实现是一棵树：

```go
type GroupNode struct {
	parent    *GroupNode
	fields    *[]string
	sortItems *[]planner.Sort
	groups    *[]*Group
	level     int
	field     string
	value     int
	leaf      bool
	group     *Group                 // 只有叶子节点持有真正的分组
	nodes     map[int]*GroupNode
}
```

第一层按第一个字段的取值建节点，第二层在各分支下按第二个字段的取值建节点……直到最深层成为叶子，叶子持有一个 `Group`（文档集合）。

```go
func (n *GroupNode) Dispatch(doc *db.Doc) {
	if n.leaf {
		n.group.AddDoc(doc)
		return
	}
	field := (*n.fields)[n.level+1]
	if vs, ok := doc.Field(field); ok {
		for _, v := range vs {
			if sn, ok := n.nodes[v]; ok {
				sn.Dispatch(doc)
			} else {
				n.nodes[v] = newGroupNode(n, n.fields, n.sortItems, n.groups, n.level+1, field, v, doc)
			}
		}
	}
}
```

这样做的好处：

- **不存在空的组合桶**——节点是通过文档实际出现才被创建的，不需要预先枚举出所有字段取值的笛卡尔积；
- **分组与筛选共享同一次文档遍历**——`Dispatch` 是流式的，拿到文档就地分发，不需要为分组再做一次扫描；
- **层级语义天然表达**——"年级 → 学科 → 难度"三层分组直接对应树的三层。

有一个语义细节值得留意：**一个文档如果在分组字段上是多值（例如一节课面向多个年级），它会被分发到多个分组里**。所以各组文档数之和会大于实际文档总数，业务侧做统计时必须知道这一点。

### 5.5 分组场景有独立的分页与排序

执行树在分组场景下换成了另一套算子：

```go
sort.Sort(e)                              // 组间排序
for _, g := range e.Groups {
	sort.Sort(g)                          // 组内文档排序
}
chunk.SetSortedGroups(e.Groups, e.SortItems)
```

分页作用于"组"而不是"文档"——`GroupLimitExec` 切片的是 `chunk.GetGroups()`。这与业务语义完全对得上：**按年级分组、每组取前 N 门课**，用户要的是"每个组各看前 N 条"，而不是"全局前 N 条再分组"。

## 六、快照持久化：把内存库变成可搬运的数据

### 6.1 一个关键取舍：存原始文档，不存倒排索引

这是整套设计里我认为最值得讨论的一个决定：

```go
func (i *Index) ExportIndex() *ExportedIndex {
	i.Timestamp = time.Now().Unix()
	ei := ExportedIndex{
		Name: i.Name, ID: i.Docs.IDField, Timestamp: i.Timestamp,
		AggBucketTermsSort: i.AggBucketTermsSort, Dict: i.Dict, Sort: i.Sort, BgSave: i.BgSave,
	}

	i.FieldIndices.Range(func(key, value interface{}) bool {
		index := value.(*FieldIndex)
		ei.Fields = append(ei.Fields, ExportedField{
			Name: index.Field, Type: index.Type, IndexType: index.IndexType,
		})
		return true
	})

	for _, doc := range i.GetAllOrdered() {
		ei.Docs = append(ei.Docs, doc.JSONValues)    // ← 存的是原始 JSON
	}
	return &ei
}
```

快照里放的是**字段元数据 + 原始 JSON 文档列表**，倒排索引和位图一个都不存。导入时逐文档重建索引（`ImportIndex` → `NewDoc` → `Index`）。

这个取舍的两面：

**收益**
- 快照格式与索引实现**解耦**：换位图库、改跳表结构、调整编码方式，都不影响快照的兼容性；
- 快照天然是"数据的真值"，可以独立校验、独立分析（后面会看到，`course-count` 就是直接拿快照当数据源做统计的，完全不需要起一个引擎实例）；
- 体积小：存索引结构反而会因为每个字段的哈希与位图产生大量冗余。

**代价**
- 导入需要**重建全部索引**，是 CPU 密集操作，恢复时间与文档数成正比；
- 导入后的索引质量**完全取决于元数据是否被完整回填**——这一点在 11.1 里会看到它真实地出了问题。

另外注意 `ExportDB` 里的过滤条件：只有 `BgSave = true` 的索引才会进入快照，临时索引不参与持久化。

### 6.2 序列化链路

```text
内存 DB
  → ExportedDB（Go 结构）
  → Protobuf（PbExportedDB：Timestamp + repeated PbExportedIndex）
  → gzip BestCompression
  → OSS / Redis / 本地文件
```

有三个细节：

- **Protobuf 用 gogo 生成**（`protoc --gofast_out`），追求序列化性能；
- **gzip 选择 `BestCompression`**：导出是低频后台任务，用 CPU 换传输体积和存储成本，方向正确；
- proto 里的字段名保持 Go 风格（`Timestamp` / `Indices` / `Docs`），说明这份 `.proto` 是从既有的 Go 结构反向对齐出来的，而不是先设计 IDL 再生成代码。对内部使用的小规模协议，这是务实的做法。

### 6.3 MD5 去重：内容没变就不上传

```go
md5Str, err := calcMD5(file, true)
if err != nil { /* ... */ }

logger.Ix(ctx, "EXPORT", "last md5: %s now: %s", lastMD5, md5Str)
if lastMD5 != "" && md5Str == lastMD5 {
	logger.Ix(ctx, "EXPORT", "db no updated")
	return nil            // 内容与上次一致，跳过上传
}
// …… 否则上传 OSS，并记录 lastMD5
```

导出任务可能被频繁触发，但数据往往几分钟甚至几十分钟才变一次。用一次 MD5 计算挡住"内容未变"的重复上传，省掉的是 OSS 带宽和存储。

内存里持有 `lastMD5`，进程重启后第一次导出必然上传一次——这个"多传一次"的代价远小于"漏传一次"，取舍方向正确。

这里还有个不显眼但必要的配合：导出时用的是 `GetAllOrdered()` 而不是 `GetAll()`。

```go
for _, doc := range i.GetAllOrdered() {
	ei.Docs = append(ei.Docs, doc.JSONValues)
}
```

`DocSet` 底层是 `sync.Map`，`Range` 的遍历顺序**不保证稳定**。如果导出用 `GetAll()`，那么"数据完全没变"的两次导出也可能产生字节不同的快照，MD5 比对失效、去重形同虚设。用 `GetAllOrdered()`（内部 `sort.Ints` 后再取）把顺序钉死，才让内容去重真正可靠——**一个性能优化的正确性，依赖另一个看起来无关的细节，这在工程里比想象中常见**。

### 6.4 多后端可插拔

```go
type IO interface {
	Name() string
	Export(ctx context.Context, d *db.ExportedDB) error
	Import(ctx context.Context, d *db.DB) (*db.ExportedDB, error)
	GetConfig() *config.StoreConfig
}
```

`NewIO` 按配置把 `redis` / `cloud`（OSS）/ `file` / `mock_file` 中的一个实例化出来，`Store` 持有多个 `IO` 并按名字分发。多后端同时启用时互为备份——主后端不可用可以切到另一个后端继续同步。

`mock_file` 的存在说明这个抽象也被测试用上了，属于"为可测试性留的口子"。

## 七、一致性：时间戳单调 + 版本校验

快照同步的核心是两条规则，都写在 `WatchStore` 里：

```go
if c.Version != config.StoreVersion {
	logger.Ix(ctx, "WATCH_STORE", "store version mismatched, want %d got %d", ...)
	continue                                        // 协议版本不匹配：跳过
}

if c.Timestamp > srv.DB.Timestamp {                 // 严格大于：拒绝回退
	io, err := store.NewIO(c)
	srv.ImportDBFromIO(ctx, io)
	srv.Ready = true
}
```

两条规则各自解决一个经典问题：

- **`Timestamp >`（严格大于而不是 `>=`）**：防止旧快照覆盖新数据。存储配置可能被重复投递、乱序到达，用严格大于把"回退"这件事从根上排除。比较的基准是 `srv.DB.Timestamp`，即当前内存库实际的数据版本，而不是本地上次看到的时间戳。
- **`Version` 相等校验**：给快照格式演进留出开关。`StoreVersion` 目前是 4，说明格式已经演进过 4 次；版本不匹配时宁可跳过，也不去误读一个结构未知的快照。

数据同步的方向由"存储配置"这个中间层驱动，而不是实例之间直接推数据：导出方把快照写入存储并更新存储配置（带时间戳），各实例观察配置变化后自己去导入。**把"通知"和"数据"分离**，实例就不需要知道彼此的存在，新增实例只需要能读到存储配置即可——这是这套同步机制能支撑多集群双活的原因。

配置的获取方式是**轮询**：

```go
ticker := time.NewTicker(12 * time.Second)      // 存储配置：12 秒一轮
// ...
ticker := time.NewTicker(76 * time.Second)      // 业务配置：76 秒一轮
```

取舍很清楚：实现简单、没有 watch 长连接的维护成本（断线重连、事件乱序都要处理），代价是配置生效有最长 12 秒 / 76 秒的延迟。对于"分钟级同步一次"的数据链路，这个延迟完全可以接受；但**如果业务要求"改了配置立刻生效"，轮询就是错的**，必须换成 watch。

`Ready` 标志用于表达"数据是否可用"：导入成功后才置位，接入层可以据此拒绝服务或降级，避免在数据尚未就绪时返回错误结果。

## 八、高可用：Etcd 主备选举

多实例同时导出快照会产生写冲突，也浪费资源。引擎用 Etcd 的 `concurrency` 包做租约选举，保证同一时刻只有一个"主"承担导出职责：

```go
session, err := concurrency.NewSession(cli, concurrency.WithTTL(30))   // 30 秒租约
srv.election = concurrency.NewElection(session, srv.Cfg.PrimaryElectionPrefix)

// 1) 启动时先看有没有主
if resp, err := srv.election.Leader(ctx); err == nil { /* 记录当前主 */ }

// 2) 持续观察主的变化
for resp := range srv.election.Observe(ctx) {
	primaryAddr := string(resp.Kvs[0].Value)
	if srv.primaryAddr != primaryAddr {
		// 区分四种角色迁移：首次成为主 / 从主降为副本 / 副本仍是副本 / 我成为新主
	}
	if primaryAddr != srv.addr {
		go srv.campaign(ctx)     // 我不是主 —— 参与竞选，等着接管
	}
}
```

设计上的几个要点：

- **TTL 30 秒**：主实例宕机后，租约到期，其他实例在 30 秒内接管。这个数字是"故障恢复速度"与"误判导致双主"之间的权衡。
- **本地 `TryLock` 防重入**：`campaign` 入口先抢一个本地互斥锁，避免每次收到 observe 事件都重复发起竞选。
- **角色迁移日志完备**：把"首次成为主""从主降为副本""副本仍然是副本""我成为新主"四种情况分开打日志。这类分布式状态机的排障难点往往不是逻辑错，而是**不知道自己现在是什么角色**，日志把这一点直接说清楚。
- **从副本不再承担写职责**：非主实例只做 observe 和导入，导出/写入集中在主实例，天然避免了快照写冲突。

## 九、数据生产链路：生产者-消费者流水线

引擎的性能依赖"数据已经在内存里"这个前提，所以数据怎么写进去同样重要。

### 9.1 Transporter：一个通用流水线骨架

```go
type Transporter struct {
	name        string
	producers   []Producer
	consumers   []Consumer
	producerWg  sync.WaitGroup
	consumerWg  sync.WaitGroup
	displayInfo bool
}

const BufferSize = 5
```

启动后的拓扑是：

{{< mermaid >}}
flowchart TD
    P1["producer1"] --> OUT["producerOut<br/>（汇聚）"]
    P2["producer2"] --> OUT
    P3["producer3"] --> OUT
    OUT --> C1["consumer1"] --> C2["consumer2"] --> CN["consumerN"] --> D["（排空）"]
{{< /mermaid >}}

几个工程细节做得很扎实：

- **多生产者并行、结果汇聚**：每个 producer 有独立的输出 channel，再由一个 goroutine 汇总到 `producerOut`，最后 `producerWg.Wait()` 确认所有生产者结束后才 `close(producerOut)`——关闭时机的处理是正确的（不会关得太早导致 panic，也不会漏数据）。
- **消费者串行成链**：`consumer1 → consumer2 → …`，每个环节之间是容量 5 的小缓冲 channel。小缓冲是有意的：既提供一定的流水线并行度，又能在下游变慢时尽快把背压传导回上游，不会把大量数据积压在内存里。
- **尾部排空**：`go func() { for { <-producerIn } }()` 保证消费链的最后一环不会因为无人读取而阻塞——这是这类流水线里一个容易漏掉的收尾动作。
- **可观测性内置**：`DisplayInfo()` 后每 5 秒打印一次各环节的自定义指标（`Info()`），长跑任务在终端上就能看到进度。数据同步任务往往要跑几十分钟，没有进度输出就只能"干等 + 猜"。
- **优雅退出**：监听 `SIGINT`，收到信号后 `cancel()` 通知整条链路，5 秒超时后强退。

抽象成 `Producer` / `Consumer` 两个接口后，这条链路的编排就是纯配置：

```text
课程生产者 ─▶ 基础组装 ─▶ 外呼接口补全（促销/销量/班级/满意度）─▶ 乐高字段映射 ─▶ 写入引擎
```

把"慢且可能失败的外部依赖"放在中间环节，任一环节出问题都能从进度输出里立刻定位到是哪一级卡住、卡在哪条数据上。这是流水线设计相对"一个大函数顺序执行"的实际收益。

### 9.2 攒批：NewBuffer

单条消息逐条写入引擎会产生大量锁竞争和索引更新。`NewBuffer` 负责把单条流攒成批（下面只保留两个分支的骨架，省略了切片拷贝与收尾处理）：

```go
func NewBuffer(in <-chan interface{}, size int) <-chan []interface{} {
	buffer := make([]interface{}, 0, size)
	out := make(chan []interface{}, size)

	go func() {
		for {
			select {
			case item, ok := <-in:
				// 有数据：攒起来，攒够 size 就发一批
			default:
				// 没有数据：如果 buffer 非空，先发出去（避免低流量时死等）；
				// 否则阻塞等一条数据（避免空转烧 CPU）
			}
		}
	}()
	return out
}
```

这个 `select + default` 的写法解决了一个实际问题：**既要批量效率，又不能因为流量低而长时间不发送**。纯攒批（攒满才发）在夜间低流量时会让数据迟迟不写入引擎；纯逐条发又丢掉了批量收益。先非阻塞尝试、攒不到就发、真的没数据才阻塞等——两头都照顾到了。

用于写入引擎时，批量写入把 N 次"加锁 + 更新索引 + 更新位图"合并成一次，收益是线性的。
### 9.3 并行计数：worker pool + 全或无

`course-count` 任务的做法值得单独说，因为它体现了一种明确的正确性取舍：

```go
func (c *Counter) Counting() error {
	ctx, cancel := context.WithCancel(context.Background())

	for i := 0; i < c.numWorkers; i++ {
		go c.Worker(ctx)                 // N 个 worker
	}
	go c.Dispatch(ctx, c.numCourses)     // 分发任务（课程下标）

	// 全或无：任何一条数据统计失败，本轮整体作废
	for i := 0; i < c.numCourses; i++ {
		if res := <-c.resultsCh; res == false {
			cancel()
			return errors.New("dirty data in exported DB file")
		}
	}
	cancel()
	return nil
}
```

（为聚焦主线，上面省去了日志输出与 `logger.Ex` 调用。）

- **任务分发用 channel 传下标**（`coursesCh chan int`），worker 按索引去快照里取数据，避免在 channel 里搬运大对象；
- **结果回传用 `resultsCh`**，主协程逐个收结果，一旦发现失败立即 `cancel()` 终止全局；
- **写库在单事务内完成**（`Write2Mysql` 里 `Begin` → `Prepare` → 循环 `Exec` → `Commit`），要么全写进去，要么一条都不写。

这就是"统计数据的正确性优先于时效性"：**宁可这一轮不产出结果，也不允许把半截脏数据写进业务库**。对下游依赖这个统计结果的业务来说，一份缺失的数据远好过一份错误的汇总。

计数结构用的是分段锁的 `ConcurrentMap`，key 是 `[4]int{课程类别, 学科, 年级, 省份}`——统计维度是低基数的枚举组合，map 的规模可控。

## 十、业务适配：把变化关进配置里

这套引擎被三个品牌/业务线复用，差异主要靠配置吸收。配置分了四层：

| 层次 | 内容 | 变更方式 | 生效延迟 |
|------|------|----------|----------|
| 基础配置 | 端口、存储后端、日志、Etcd/Nacos 地址 | 本地 TOML + 环境变量 | 需重启 |
| 业务配置 | 品牌维度的搜索类型、MySQL 连接、接口密钥 | TOML + Nacos | 最长 76 秒 |
| 乐高配置 | 字段映射、课程包规则、学科/年级/难度排序、字典、老师亲密值 | JSON 文件 + DB | 随数据同步任务加载 |
| 存储配置 | 快照时间戳、存储后端 | 运行时更新 | 最长 12 秒 |

控制器的处理流程很能说明这种分层是怎么落地的：

```go
typ := int(gjson.Parse(paramsJSON).Get("query.type").Int())
switch typ {
case TypeCourse, TypeJiaJiaGou:      // 课程 / 加加购
	search, err = parser.ParseSearchCourse(paramsJSON)
	fixSearchCourse(search, cfg.SearchType, cfg.LegoCourseSort, cfg.Env)
case TypeCoursePack:                 // 课程包
	search, err = parser.ParseSearchCoursePack(paramsJSON)
	fixSearchCoursePack(search, cfg.SearchType)
case TypeTeacher:                    // 老师
	search, err = parser.ParseSearchTeacher(paramsJSON)
	fixSearchTeacher(search, cfg.SearchType)
}
```

`fixSearchCourse` 这类函数的职责是**把"品牌差异"集中到一个地方**：按当前品牌加载排序规则、乐高字段映射、字典翻译表，然后修正查询计划。同一份引擎代码，不同品牌走不同规则。

`planner.Search` 里保留了业务参数（`Brand`、`DeviceID`、`ProvinceIDs`、`LegoSubject3IDs`……），而 `executor` 层完全不知道自己服务的是哪个品牌——**业务差异被挡在了解析层与计划层，执行引擎保持通用**。这个边界划得很干净，也是这套代码能被复用而不是被 if-else 淹没的根本原因。

## 十一、几处值得记录的取舍与坑点

前面讲的是"它是怎么设计的"，这一节讲"读代码时我觉得值得记下来的东西"。它们不影响"这套架构是否成立"的判断，但每一处对后来者都有参考价值。

### 11.1 快照导出了 IndexType，导入时却没有回填

导出侧老老实实把 `IndexType` 写进了快照：

```go
ei.Fields = append(ei.Fields, ExportedField{
	Name: index.Field, Type: index.Type, IndexType: index.IndexType,   // ← 导出了
})
```

导入侧却没有消费它：

```go
for _, field := range ei.Fields {
	i.AddFieldIndex(NewFieldIndex(ctx, field.Name, field.Type, ""))    // ← 第四个参数写死空串
}
```

而 `NewFieldIndex` 里只有 `IndexType == "range"` 才会创建跳表：

```go
if i.IndexType == IndexTypeRange {
	i.SkipList = skiplist.NewIntMap()
}
```

于是：**从快照恢复出来的索引，全部字段的 `IndexType` 都是空串，所有 range 索引丢失**，`SkipList == nil`，范围查询能力随之失效。

`ExportedField` 里明明有 `IndexType` 字段，导出写了、导入没读——典型的"给结构加了字段，但只改了写侧"。影响面取决于使用方式：如果实例启动后总会全量重建索引，问题会被掩盖；如果走的是"启动导入快照 + 后续增量更新"的路径，那么价格区间、时间区间这类 range 条件在恢复之后就不再生效。

### 11.2 条件构建失败被降级为 Warn，查询语义静默改变

这一条比上一条更值得警惕。`ExecutorBuilder` 在构建查询条件时，对失败的处理是**记一条警告然后丢掉这个条件**：

```go
rang := newRangeQueryExec(b.session, index)
if err := rang.setFieldAndValue(r.Field, r.Gt, r.Gte, r.Lt, r.Lte); err == nil {
	must.base().children = append(must.base().children, rang)
} else {
	logger.Wx(ctx, "BUILD_QUERY", err)      // ← 只记警告，条件被静默丢弃
}
```

字段不存在、字段类型不支持、range 索引缺失……这些错误都不会让请求失败，而是**悄悄丢掉这个筛选条件继续往下执行**。

对 `must` 语义来说，丢掉一个条件意味着结果集**变大**：业务侧观察到的是"这个筛选没生效"，而不是"接口报错了"。这类问题在测试环境往往发现不了（字段齐全、索引完整），只会在生产环境的边缘场景里冒出来，而且排查时因为只有一行 Warn 日志，很容易被淹没。

容错的初衷可以理解——某个字段暂时不可用时不至于让整个查询失败。但**筛选条件是用户明确表达的约束，丢掉它的代价是结果错误**。更稳的分级方式：结构性错误（字段不存在、类型不支持）直接让请求失败；只有真正的运行时降级能力才走警告。

把 11.1 和 11.2 连起来看，这条路径就更清楚了：快照恢复导致 range 索引丢失 → 构建 range 条件时报错 → 错误被降级成 Warn → 条件被丢弃 → 用户看到"价格筛选不起作用"。**整条链路没有任何一处抛出异常或返回错误**，这才是最需要防范的一类缺陷。

### 11.3 must_not 依赖上游先产出结果集

```go
func (c *Chunk) AndNot(chunk *Chunk) {
	if c.Count() == 0 || chunk.Count() == 0 {
		return                              // 空集时直接返回
	}
	c.DocIDSet.AndNot(chunk.DocIDSet)
}
```

`must_not` 的语义是"对当前 chunk 做差集"。如果查询里**只有** `must_not`，而没有 `must` 或 `filter` 先产出结果集，那么 chunk 的位图是初始的空位图，`Count() == 0` 直接返回——**排除条件等于没写**。

`match_all` 也无法兜底，因为它只设置了文档列表，没有设置位图：

```go
func (e *MatchAllExec) Next(ctx context.Context, chunk *Chunk) error {
	chunk.Docs = e.index.Docs.GetAll()     // ← 只设置了 Docs
	chunk.Index = e.index
	return nil                              // ← 没有设置 DocIDSet
}
```

目前这个问题被 DSL 的结构掩盖了：`bool` 与 `match_all` 是互斥分支，而 `bool` 里通常一定有 `must`。但如果哪天要支持"排除若干 ID 之后返回全部数据"这类查询，它会立刻变成一个非常安静的 bug。

修法也很直接：让 `match_all` 同时产出全量位图，或者让 `must_not` 在 chunk 为空时以全量位图为起点。**关键是要让"单独使用 must_not"这个组合要么正确工作，要么明确报错**，而不是返回一个看似合理却错误的结果。

### 11.4 分页是全量排序后切片

```go
// SortExec：对结果集全量排序
e.Docs = chunk.GetDocs()
sort.Sort(e)
chunk.SetSortedDocs(e.Docs, e.SortItems)
```

```go
// LimitExec：在已排序的切片上做分页
chunk.SetLimitedDocs(docs[e.from : e.from+e.size])
```

在课程这种万级数据量下，这笔开销可以接受。但两个问题值得注意：

1. **深分页的成本没有改善**。`from = 10000, size = 20` 时仍然要全量排序，而用户只需要 20 条。
2. **每次请求都重新排序**。同一个排序条件下的连续翻页会重复做完全相同的工作。

标准解法是 **Top-K 堆**：维护一个大小为 `size` 的最小堆（或最大堆，视排序方向），把复杂度从 O(n log n) 降到 O(n log k)，其中 k 是页大小。对 `from + size` 不太大的场景，收益是数量级的。实现上也不复杂——在执行树里给排序算子加一个"只保留前 K 个"的能力即可，但要小心 `Total` 的语义：返回的总数仍应是完整命中数，而不是被截断后的数量。

### 11.5 其他小观察

| 位置 | 观察 | 说明 |
|------|------|------|
| `db/index.go` `Index.Index` | 更新单个文档要遍历**所有**字段索引删除旧值 | 更新成本与字段总数成正比，与实际变化的字段数无关；批量更新场景下值得按"字段是否变化"筛选 |
| `db/doc.go` `FieldIndex.Delete` | 位图空了会删掉哈希节点，但 `stringToInt` 字典条目永久保留 | 对枚举字段是合理取舍；用在高基数、高频变更字段上会持续增长 |
| `executor/sort.go` `Less` | 每次比较都重新拼 `teacherID,subject3ID,gradeID` 字符串并查 map | 比较次数是 O(n log n)，常数不小；可以在文档上预先算好 key 并缓存 |
| `executor/sort.go` | 排序算子隐含要求 `SortItems` 非空 | `Next` 里直接访问 `e.SortItems[0]`，空切片会 panic；目前依赖 Builder 保证 |
| `executor/match_all.go` | `match_all` 用的是 `GetAll()`（`sync.Map` 无序） | 它会把 `Docs` 直接置位，于是 `SortExec` 里"按 id 排序不排序"的捷径前提不再成立（见 5.1），两条路径对有序性的假设不一致 |
| `db/doc.go` `DocSet.GetMany` | 位图里的 ID 在 `DocMap` 中找不到时会**静默跳过** | 位图与文档一旦不同步，`hits` 长度会与 `Total` 对不上，且不报任何错 |
| `server/server.go` | 包级单例 `srv` + `Srv()` 在未初始化时只打日志返回 nil | 调用方拿到 nil 会 panic，初始化顺序成了隐式契约，可用显式依赖注入替代 |
| `biz/trans/transporter.go` | 末尾保留了一个未被调用的调试函数（goroutine + `println`） | 清理项，不影响功能 |

### 11.6 取舍一览

| 设计决策 | 换来了什么 | 付出了什么 |
|----------|-----------|-----------|
| 全内存 + 位图运算 | 毫秒级筛选，无外部依赖 | 数据规模受单机内存限制，无水平扩展 |
| 只给 range 字段建跳表 | 按查询模式分配存储成本 | 字段类型声明必须准确，否则查询能力缺失 |
| 字符串统一编码为整数 | 位图化 + 字典翻译一次完成 | 字典只增不减，高基数字段会膨胀 |
| Chunk 惰性物化 | 筛选阶段零文档解引用 | 算子需要正确维护 `DocIDSet`/`Docs`/`Limited`/`Sorted` 的状态组合 |
| 快照存原始文档而非索引 | 格式与实现解耦，可独立分析 | 导入需重建索引；元数据不全会导致索引能力缺失 |
| 配置轮询而非 watch | 实现简单，无长连接维护成本 | 配置生效有 12s / 76s 延迟 |
| 条件构建失败降级为 Warn | 单字段不可用不拖垮整个查询 | 筛选条件可能被静默丢弃，结果错误且难以发现 |
| 统计任务全或无 | 不会写出半截脏数据 | 一条坏数据导致整轮统计作废，时效性受损 |
| Etcd 主备选举 | 写职责唯一，避免快照写冲突 | 引入 Etcd 依赖，故障切换有最长 30 秒窗口 |

## 十二、小结

把这两万多行代码读完，我觉得最有价值的几点可以这样总结：

**1. 位图是多条件筛选的天然数据结构。** 当数据能全部放进内存时，把"筛选"翻译成位图的交并差，是这套引擎性能的根本来源。`must` / `filter` / `must_not` 的语义与集合运算是天然对应的，代码里几乎看不到"遍历、判断、收集"这种传统写法。

**2. `Chunk` 的惰性物化是架构里最巧的一处。** 位图与文档在同一个数据结构里分离存放，筛选阶段全程只动位图，直到最后才批量取文档。这一个决定同时降低了 CPU 和 GC 的压力，也让"筛十万取二十"这种场景变得廉价。

**3. 快照存原始数据而不是存索引结构，是一笔很划算的买卖。** 它让存储格式与索引实现解耦，还顺带让快照成为一个可以被独立消费的数据源（统计任务直接用快照，不需要起引擎）。代价是恢复时要重建索引——对分钟级的恢复窗口来说，这个代价是值得的。

**4. 配置驱动的边界划得很清楚。** 品牌差异、字段映射、排序权重全在配置里，执行引擎完全不知道业务方是谁。这是同一套代码能服务多个品牌和业务线的原因，也应该是所有"会被复用"的引擎类项目的标准做法。

**5. 但容错设计需要分级。** 11.1 和 11.2 连起来看，是一条"快照恢复缺元数据 → 条件构建失败 → 错误降级为日志 → 查询结果静默改变"的完整链路，全程没有任何一处报错。这提醒我们：**对"用户明确表达的约束"要用失败来表达异常，而不是用降级**；降级只应该留给"可选的增强能力"。

如果说这套引擎体现了一种工程思路，那就是：**先承认场景的边界（数据量可控、单机内存足够），然后在这个边界内把性能与简洁性做到极致**——而不是为了应对想象中的规模，提前把系统复杂化。它当然不能替代 Elasticsearch，但它在自己被设计的那一类场景里，比 Elasticsearch 更快、更简单、也更便宜。
