---
categories: ["Raft"]
title: "【译】Raft 学生指南"
date: "2020-02-02T00:00:00+08:00"
tags: ["Raft", "分布式", "一致性"]
summary: "在过去的几个月中，我一直担任 MIT 的 6.824 分布式系统课程的助教。传统上，该班级有许多基于 Paxos 共识算法的实验，但是今年，我们决定转向 Raft。Raft 的设计更易于理解，我们希望这种改变可以使学生的学习更轻松。这篇文"
translationKey: "yi--raft--xue-sheng-zhi-nan"
---

> 📌 本文原发布于代码星冰乐：[【译】Raft 学生指南](https://changhuin.github.io/article/2020/62e/)

在过去的几个月中，我一直担任 MIT 的 <a href="https://pdos.csail.mit.edu/6.824/" target="_blank" rel="noopener">6.824 分布式系统课程</a>的助教。传统上，该课程有许多基于 Paxos 共识算法的实验，但是今年，我们决定转向 <a href="https://raft.github.io/" target="_blank" rel="noopener">Raft</a>。Raft 的设计更易于理解，我们希望这种改变可以使学生的学习更轻松。

这篇文章，以及随附的<a href="https://thesquareplanet.com/blog/instructors-guide-to-raft/" target="_blank" rel="noopener">《Raft 教师指南》</a>一文，记录了我们使用 Raft 的旅程，并希望对 Raft 协议的教学者和试图更好地了解 Raft 内部原理的学生有所帮助。如果您想对 Paxos 与 Raft 进行比较，或者需要对 Raft 进行更多的教学分析，请阅读<a href="https://thesquareplanet.com/blog/instructors-guide-to-raft/" target="_blank" rel="noopener">《Raft 教师指南》</a>。这篇文章的底部包含 6.824 学生常见的<a href="https://thesquareplanet.com/blog/raft-qa/" target="_blank" rel="noopener">Q&amp;A</a>。如果您遇到的问题未在本文的主要内容中列出，请查看<a href="https://thesquareplanet.com/blog/raft-qa/" target="_blank" rel="noopener">Q&amp;A</a>。这篇文章很长，但它提出的所有观点都是许多 6.824 学生遇到的实际问题，这是值得一读的。

## 背景

在我们深入研究 Raft 之前，有些背景可能会有用。6.824 曾经有一组用 Go 编写的基于 Paxos 的实验；选择 Go 是因为它语法简单易于学习，而且非常适合编写并发的分布式应用程序。在四个实验过程中，学生将构建一个容错的分布式 KV 存储系统。第一个实验让他们建立了一个基于共识的日志库，第二个实验在此基础上添加了一个键值存储，第三个实验通过多个容错的分片主节点处理配置更改，在多个容错集群之间分割键空间。我们还有第四个实验，学生必须在磁盘完好无损的情况下处理机器的故障和恢复。该实验可作为学生的默认最终项目使用。

今年，我们决定使用 Raft 重写所有这些实验。前三个实验保持不变，但是第四个实验被删除了，因为 Raft 已经内置了持久化和故障恢复功能。本文将主要讨论我们在第一个实验中的经验，因为它与 Raft 最直接相关，尽管我还将介绍如何在 Raft 之上构建应用程序。

Raft 是什么呢？对于那些刚开始了解它的人，我们最好用 Raft 官网上的文字来描述：

> Raft 是一种共识算法，旨在使其易于理解。在容错和性能方面与 Paxos 相当。区别在于它被分解为相对独立的子问题，并且彻底地解决了实际系统所需的所有主要问题。我们希望 Raft 将使共识能够为更广泛的受众所接受，并且希望这个更广泛的受众能够开发出更高质量的基于共识的系统。

<a href="http://thesecretlivesofdata.com/raft/" target="_blank" rel="noopener">像这样的</a>可视化演示很好地概述了协议的主要组成部分，并且更直观地描述了 Raft 的各个阶段。如果您还没有阅读过 <a href="http://nil.csail.mit.edu/6.824/2018/papers/raft-extended.pdf" target="_blank" rel="noopener">Raft 论文</a>，那么在继续本文之前，您应该先阅读该文档，因为我假设您对 Raft 相当熟悉。

与所有分布式共识协议一样，细节之处非常重要。在没有故障的稳定状态下，Raft 的行为很容易理解，并且可以直观地解释。例如，从可视化中很容易看出，假设没有失败，最终将选举一名 leader，并且最终发送给 leader 的所有操作将由 followers 按正确的顺序执行。但是，当引入延迟的消息，网络分区和故障服务器时，每一个 if，but 和 and 都变得至关重要。特别是，我们反复看到许多错误都源于阅读本文时的误解或疏忽。这个问题并非 Raft 独有，而是所有提供正确性的复杂分布式系统中都存在的问题。

## Raft 协议的实现

Raft 的权威指南在 Raft 论文的 Figure 2 中。该图指定了 Raft 服务器之间交换的每个 RPC 的行为，给出了服务器必须维护的各种不变量，并指定了何时应执行某些操作。在本文的其余部分中，我们将大量讨论 Figure 2。如下文描述的一样。

Figure 2 定义了每个服务器在任何状态下对于每个传入的 RPC 应该做什么，以及何时应该发生某些其他事情（例如，何时可以安全地在日志中应用条目）。刚开始，您可能会倾向于将 Figure 2 视为非正式指南。您只需阅读一次，然后开始编写大致按照其要求来实现的代码。这样做，您将快速让大多数正常的 Raft 操作运行起来。然后问题开始浮现了。

实际上，Figure 2 是非常精确的，并且应将其所作的每个陈述都视为必须，而不应视为应该。例如，每当您收到 AppendEntries 或 RequestVote RPC 时，您都可以合理地重置对等方的选举计时器，因为这两者都表明其他一些服务器要么认为自己是 leader，要么正试图成为 leader。这意味着我们不应该干涉。但是，如果您仔细阅读 Figure 2，如 Raft 论文所示：

> 如果在没有收到当前 leader 的 AppendEntries RPC 或未向候选人授予投票的情况下经过选举超时，请转换为候选人。

事实证明，区别非常重要，因为在某些情况下，前一种实现可能导致活性大大降低。

### Raft 协议实现的细节

为了使讨论更加具体，让我们考虑一个例子，这个例子曾难倒不少上 6.828 课程的学生。Raft 论文在许多地方提到了心跳 RPC。具体来说，leader 每个心跳间隔至少会向所有对等方发送一次 AppendEntries RPC，以防止他们开始新的选举。如果领导者没有新条目要发送到特定对等方，则 AppendEntries RPC 不包含任何条目，并被视为心跳。

我们的许多学生都认为心跳在某种程度上是“特殊的”。当对等方收到心跳时，应将其与非心跳 AppendEntries RPC 区别对待。特别是，许多人在接收到心跳信号后便会简单地重置其选举计时器，然后返回成功，而无需执行 Figure 2 中指定的任何检查。这非常危险。通过接受 RPC，followers 可以隐式告诉 leader，他们的日志与领导者的日志相匹配，并且包括 AppendEntries 参数中的 prevLogIndex。收到答复后，领导者可能错误地认为某些条目已被复制到大多数服务器，然后开始提交。

许多人遇到的另一个问题（通常是在解决上述问题后立即发生）是，一旦收到心跳，他们就会在 prevLogIndex 之后截断 followers 的日志，然后追加 AppendEntries 参数中包含的所有条目。这也是不正确的。我们可以再次转到 Figure 2：

> 如果现有条目与新条目（索引相同但任期不同）冲突，则删除现有条目及其后的所有条目。

这个“如果”在这里至关重要。如果 followers 具有 leader 发送的所有条目，则 followers 务必不要截断其日志。领导者发送的条目之后的任何条目都必须保留。这是因为我们可能会从领导者那里收到过时的 AppendEntries RPC，而截断日志意味着“收回”我们可能已经告诉领导者我们在日志中的条目。

## 调试 Raft 协议

不可避免地，您的 Raft 实现的第一次迭代会出现错误。第二个也是如此。第三。第四。总的来说，每个错误都比前一个错误少，并且根据经验，大多数错误是由于不忠实地遵循 Figure 2 而导致的。

在调试 Raft 时，通常有四个主要的 bug 来源：死锁，错误或不完整的 RPC 处理程序，未遵循规则以及任期混乱。死锁也是一个普遍的问题，但是通常可以通过记录所有锁和解锁并找出获取后未释放的锁来调试死锁。让我们依次考虑以下每个方面：

### 未释放锁

当系统发生死锁时，系统中的每个节点都在做某事，但是总的来说，您的节点都处于没有进展的状态。在 Raft 中，这很容易发生，特别是如果您不认真地遵循 Figure 2。一种死锁情况特别经常出现。没有选举任何 leader，或者一旦选举了 leader，其他节点开始选举，迫使最近当选的 leader 立即退位。

出现这种情况的原因有很多，但我们已经看到许多学生犯了一些错误：

- 确保您按照 Figure 2 所述正确地重置了选举计时器。具体来说，您仅应在以下情况下重新启动选举计时器：a）从当前 leader 那里获得了 AppendEntries RPC（如果 AppendEntries 参数中的任期已过时，则不应重置计时器）；b）您正在开始选举；c）您给另一位 follower 投票。

  在不可靠的网络中，后一种情况尤为重要，在这种网络中，followers 可能拥有不同的日志。在这种情况下，您通常只会获得少数服务器的投票，而大多数服务器都愿意投票。如果您在有人要求您投票给他们时重置选举计时器，则日志过时的服务器和日志较长的服务器一样有可能前进。

  实际上，由于只有很少的服务器具有足够的最新日志，因此这些服务器很难获得足够的静默期来进行选举。如果您遵循 Figure 2 中的规则，则具有最新日志的服务器将不会因过时的服务器选举而中断，因此更有可能完成选举并成为 leader。

- 请按照 Figure 2 的指示来决定何时开始选举。特别要注意的是，如果您是候选人（即您当前正在进行选举），但是选举计时器触发了，则应该重新进行选举。这对于避免由于 RPC 延迟或丢失而导致的系统停顿非常重要。

- 在处理传入的 RPC 之前，请确保遵循“服务器规则”中的第二条规则。第二条规则指出：

  > 如果 RPC 请求或响应包含条件 T > currentTerm：设置 currentTerm = T，则转换为 followers

例如，如果您已经对当前任期进行了投票，而传入的 RequestVote RPC 具有较高的任期，那么您应该首先卸任并采用其任期（从而重置 votedFor），然后处理 RPC，这将导致您同意投票！

### 不正确的 RPC 处理程序

即使 Figure 2 清楚地说明了每个 RPC 处理程序应该做什么，但仍然有些微妙之处容易遗漏。这是我们反复看到的少数几个问题，您在实施时应格外注意：

- 如果某个步骤说“答复错误”，则意味着您应立即答复，而不要执行任何后续步骤。
- 如果您获得带有指向日志末尾的 prevLogIndex 的 AppendEntries RPC，则应像该条目存在但任期不匹配一样处理它（即，回复 false）。
- 注意 #2，即使领导者未发送任何条目，也应执行 AppendEntries RPC 处理程序。
- AppendEntries 的最后一步（＃5）中的最小值是必需的，并且需要使用最后一个新条目的索引进行计算。仅具有当 lastApplied 和 commitIndex 停在日志末尾时应用日志内容的功能还不够。这是因为在领导者发送给您的条目之后，您的日志中可能有与领导者的日志不同的条目（所有条目都与您的日志中的条目匹配）。由于＃3 要求您仅在条目冲突时才截断日志，因此不会删除这些条目，并且如果 LeaderCommit 超出了领导者发送给您的条目，则您可能会应用错误的条目。
- 严格按照第 5.4 节中的描述实施“最新日志”检查很重要。没有作弊，只是检查长度！

### 不遵守规则

尽管 Raft 论文非常明确地说明了如何实现每个 RPC 处理程序，但它也留下了许多规则和不变量的实现，未作明确规定。它们在 Figure 2 右侧的“服务器规则”块中列出。尽管其中一些是不言自明的，但也有一些需要非常仔细地设计应用程序，以使其不违反 The Rules：

- 在执行过程中的任何时候执行 `go if commitIndex> lastApplied`，则应应用特定的日志条目。立即执行操作（例如，在 AppendEntries RPC 处理程序中）不是至关重要的，但是确保此应用操作仅由一个实体完成很重要。具体来说，您将需要一个专用的“应用例程”，或者锁定这些应用例程，以便其他一些例程也不会检测到需要应用条目并尝试应用。
- 确保您定期或在更新 commitIndex 之后（即在 matchIndex 更新之后）检查 commitIndex> lastApplied。例如，如果在将 AppendEntries 发送给对等方的同时检查 commitIndex，则可能必须等到下一个条目追加到日志之后才能应用刚刚发送并得到确认的条目。
- 如果领导者发出一个 AppendEntries RPC 并被拒绝，但不是由于日志不一致（只有在我们的任期过去时才可能发生），那么您应该立即下台，而不要更新 nextIndex。如果这样做，并且立即连任，则可能与 nextIndex 的重置产生竞争。
- 领导者不允许将 commitIndex 更新到上一个任期（或就此而言，将来的任期）中的某个位置。因此，按照规则所说，您特别需要检查 log\[N\].term == currentTerm。这是因为 Raft 领导者如果不是从其当前任期开始，就无法确定该条目是否确实已提交（将来也不会更改）。Raft 论文的 Figure 8 对此进行了说明。

造成混淆的一个常见原因是 nextIndex 和 matchIndex 之间的差异。特别是，您可能会注意到 matchIndex = nextIndex-1，而根本没有实现 matchIndex。这不安全。通常将 nextIndex 和 matchIndex 同时更新为相似的值（具体来说，nextIndex = matchIndex + 1），但两者的作用却截然不同。nextIndex 是对领导者与给定跟随者共享的前缀的猜测。它通常是相当乐观的（我们共享一切），并且仅在负面响应时才向后移动。例如，当刚刚选择一个领导者时，将 nextIndex 设置为日志末尾的索引。在某种程度上，nextIndex 用于提高性能–您只需要将这些内容发送给该对等方即可。

matchIndex 用于安全。这是对领导者与给定跟随者共享日志的前缀的保守度量。matchIndex 永远不能设置为太高的值，因为这可能导致 commitIndex 移得太远。这就是为什么将 matchIndex 初始化为-1（即我们没有前缀），并且仅在跟随者肯定地确认 AppendEntries RPC 时才进行更新的原因。

### 任期不一致

任期混淆是指服务器被来自旧任期的 RPC 混淆。通常，在接收 RPC 时这不是问题，因为 Figure 2 中的规则明确说明了您看到旧任期时应采取的措施。但是，Figure 2 通常不会讨论收到旧的 RPC 答复时应采取的措施。根据经验，到目前为止，最简单的方法是首先在答复中记录该任期（该任期可能高于您当前的任期），然后将当前任期与您在原始 RPC 中发送的任期进行比较。如果两者不同，请丢弃答复并返回。仅当两个任期相同时，您才可以继续处理答复。您可以使用一些聪明的协议推理在此处进行进一步的优化，但是这种方法似乎很好用。不这样做会让你走上一条充满眼泪和绝望的漫长曲折之路。

一个相关但不完全相同的问题是，假设在您发送 RPC 的时间与收到回复之间的状态没有发生变化。一个很好的例子是在收到对 RPC 的响应时设置 matchIndex = nextIndex-1 或 matchIndex = len（log）。这是不安全的，因为自发送 RPC 以来，这两个值都可能已更新。相反，正确的做法是将 matchIndex 更新为您最初在 RPC 中发送的参数的 prevLogIndex + len（entries \[\]）。

### 先把优化放在一边

Raft 包括几个有趣的可选功能。在 6.824 中，我们要求学生实施其中两个：日志压缩（第 7 节）和加速日志回溯（第 8 页左上角）。前者对于避免日志无限制增长是必要的，而后者对于使过时的 follower 快速更新很有用。

这些功能不是 Raft 最核心的一部分，因此在本文中没有像主要共识协议那样受到足够的重视。日志压缩已经相当全面地介绍了（在论文图 13 中），但是省略了一些设计细节，如果您随便阅读它可能会错过：

- 对应用程序状态进行快照时，需要确保应用程序状态与 Raft 日志中某个已知索引处的状态相对应。这意味着应用程序需要把该快照对应的索引告知 Raft，或者 Raft 需要延迟应用其他日志条目，直到快照完成为止。

- 本文不讨论服务器崩溃时的恢复协议，而这一问题在涉及快照时会重新出现。特别是，如果 Raft 状态和快照分别提交，则服务器可能在持久化快照和持久化更新后的 Raft 状态之间崩溃。这是一个问题，因为论文的图 13 中的步骤 7 指示必须删除快照覆盖的 Raft 日志。\
  如果在服务器恢复时读取了更新的快照，但读取了过时的日志，则可能最终应用了快照中已包含的一些日志条目。发生这种情况是因为 commitIndex 和 lastApplied 未持久保存，因此 Raft 不知道这些日志条目已被应用。解决此问题的方法是在 Raft 中引入一个持久状态，该状态记录 Raft 持久日志中第一个条目所对应的“真实”索引。然后可以将其与加载的快照的 lastIncludedIndex 进行比较，以确定要丢弃日志开头的哪些条目。

加速日志回溯优化的规格非常少，可能是因为作者认为对于大多数部署而言，它不是必需的。从文本中不清楚领导者应如何使用从跟随者发送回的冲突索引和任期来确定要使用的 nextIndex。我们认为作者可能希望您遵循的协议是：

- If a follower does not have prevLogIndex in its log, it should return with conflictIndex = len(log) and conflictTerm = None.
- If a follower does have prevLogIndex in its log, but the term does not match, it should return conflictTerm = log\[prevLogIndex\].Term, and then search its log for the first index whose entry has term equal to conflictTerm.
- Upon receiving a conflict response, the leader should first search its log for conflictTerm. If it finds an entry in its log with that term, it should set nextIndex to be the one beyond the index of the last entry in that term in its log.
- If it does not find an entry with that term, it should set nextIndex = conflictIndex.

一个半途而废的解决方案是只使用冲突索引（并忽略冲突 term），这简化了实现，但是领导者有时最终会向跟随者发送比严格追平最新日志所需更多的日志条目。

## 参考

<a href="https://thesquareplanet.com/blog/students-guide-to-raft/" target="_blank" rel="noopener">Students’ Guide to Raft</a>

