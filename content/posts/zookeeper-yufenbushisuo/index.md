---
categories: ["后端"]
title: "Zookeeper 与分布式锁"
date: "2021-01-13T11:15:16+08:00"
tags: ["ZooKeeper", "Go"]
summary: "在上篇文章中讨论了基于 Redis 的单机分布式锁与集群分布式锁的方案，在数据一致性要求不是很高的情况下，Redis 实现的分布式锁可以满足我们的要求。最近在拜读了 zookeeper 的论文之后，对于 zookeeper 实现的分布式锁，也是有必要了解一下的。 使用 Zook…"
---

> 📌 本文原发布于掘金社区：[Zookeeper 与分布式锁](https://juejin.cn/post/6917077877989048327)

在<a href="https://link.juejin.cn?target=http%3A%2F%2Fwww.hchstudio.cn%2Farticle%2F2020%2F7bc5%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="http://www.hchstudio.cn/article/2020/7bc5/">上篇文章中</a>讨论了基于 Redis 的单机分布式锁与集群分布式锁的方案，在数据一致性要求不是很高的情况下，Redis 实现的分布式锁可以满足我们的要求。最近在拜读了 zookeeper 的论文之后，对于 zookeeper 实现的分布式锁，也是有必要了解一下的。

## ZooKeeper 是什么？

ZooKeeper 的论文是这样描述的：

> ZooKeeper 是一种用于协调的服务分布式应用程序。 由于 ZooKeeper 是关键基础结构的一部分，因此 ZooKeeper 旨在提供一个简单而高性能的内核，以在客户端构建更复杂的协调原语。 它在复制的集中式服务中合并了来自组消息传递，共享寄存器和分布式锁定服务的元素。 ZooKeeper 公开的接口具有共享寄存器的免等待方面，它具有事件驱动机制，类似于分布式文件系统的缓存失效，以提供简单而强大的协调服务。

## ZooKeeper 实现的简单的分布式锁

使用 Zookeeper 实现分布式锁的最简单的方案是在 Zookeeper 中创建一个临时状态（EPHEMERAL）的锁节点，为了获取锁，客户端尝试使用 EPHEMERAL 标志创建指定的 znode（如 lock ）。如果创建成功，则客户端将持有该锁。否则，客户端可以读取设置了监视标志的 znode，以便在当前领导者去世时得到通知。客户端死亡或显式删除 znode 时会释放该锁。 其他等待锁定的客户端一旦观察到 znode 被删除，就会再次尝试获取锁定。

## 对 ZooKeeper 分布式锁的优化

对于上面的方案， 细心的同学可能会发现，如果同时有 n 个客户端去获取锁资源，就会只能有一个客户端获取锁成功，那么就会有 n-1 个客户端设置对锁节点的监听，如果在 n 比较大的情况下会有客户端获取锁的时间被延长，甚至是无限延长，在某些情况下是不可接受的。

对于上面的这种极端情况，Zookeeper 官方给出了比较好的解决方案，就是将竞争的客户端进行排队，具体实现的伪代码如下所示：

```
Lock
1 n = create(l + “/lock-”, EPHEMERAL|SEQUENTIAL)
2 C = getChildren(l, false)
3 if n is lowest znode in C, exit
4 p = znode in C ordered just before n
5 if exists(p, true) wait for watch event
6 goto 2
Unlock
1 delete(n) 
```

在上面的代码中，Lock的第1行中使用SEQUENTIAL标志，可相对于所有其他尝试命令客户尝试获取锁定。 如果客户端的znode在第3行的序列号最低，则客户端将持有该锁。 否则，客户端将等待删除具有锁定或将在该客户端的znode之前收到锁定的znode。 通过仅查看客户端znode之前的znode，我们仅在释放锁或放弃锁请求时才唤醒一个进程，从而避免了羊群效应。 客户端监视的znode消失后，客户端必须检查它现在是否持有该锁。 （先前的锁定请求可能已被放弃，并且具有较低序号的znode仍在等待或保持锁定。）

总而言之，这个锁的实现方案具有以下优点：

- 1.删除一个znode只会导致一个客户端唤醒，因为每个znode都被另一个客户端监视，因此我们没有羊群效应。
- 2.没有轮询或超时。
- 3.由于我们实现了锁定的方式，因此通过浏览ZooKeeper数据可以看到锁定争用，中断锁定和调试锁定问题的数量。

``` go
// Lock attempts to acquire the lock. It will wait to return until the lock
// is acquired or an error occurs. If this instance already has the lock
// then ErrDeadlock is returned.
func (l *Lock) Lock() error {
    if l.lockPath != "" {
        return ErrDeadlock
    }

    prefix := fmt.Sprintf("%s/lock-", l.path)

    path := ""
    var err error
    for i := 0; i < 3; i++ {
        path, err = l.c.CreateProtectedEphemeralSequential(prefix, []byte{}, l.acl)
        if err == ErrNoNode {
            // Create parent node.
            parts := strings.Split(l.path, "/")
            pth := ""
            for _, p := range parts[1:] {
                var exists bool
                pth += "/" + p
                exists, _, err = l.c.Exists(pth)
                if err != nil {
                    return err
                }
                if exists == true {
                    continue
                }
                _, err = l.c.Create(pth, []byte{}, 0, l.acl)
                if err != nil && err != ErrNodeExists {
                    return err
                }
            }
        } else if err == nil {
            break
        } else {
            return err
        }
    }
    if err != nil {
        return err
    }

    seq, err := parseSeq(path)
    if err != nil {
        return err
    }

    for {
        children, _, err := l.c.Children(l.path)
        if err != nil {
            return err
        }

        lowestSeq := seq
        prevSeq := -1
        prevSeqPath := ""
        for _, p := range children {
            s, err := parseSeq(p)
            if err != nil {
                return err
            }
            if s < lowestSeq {
                lowestSeq = s
            }
            if s < seq && s > prevSeq {
                prevSeq = s
                prevSeqPath = p
            }
        }

        if seq == lowestSeq {
            // Acquired the lock
            break
        }

        // Wait on the node next in line for the lock
        _, _, ch, err := l.c.GetW(l.path + "/" + prevSeqPath)
        if err != nil && err != ErrNoNode {
            return err
        } else if err != nil && err == ErrNoNode {
            // try again
            continue
        }

        ev := <-ch
        if ev.Err != nil {
            return ev.Err
        }
    }

    l.seq = seq
    l.lockPath = path
    return nil
}
```

## 小结

就这样吧，先水一篇文章~

## 参考

- <a href="https://link.juejin.cn?target=https%3A%2F%2Ffpj.me%2F2016%2F02%2F10%2Fnote-on-fencing-and-distributed-locks%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="https://fpj.me/2016/02/10/note-on-fencing-and-distributed-locks/">Note on fencing and distributed locks</a>

- <a href="https://link.juejin.cn?target=https%3A%2F%2Fblog.didiyun.com%2Findex.php%2F2018%2F11%2F20%2Fzookeeper%2F" target="_blank" data-ref="nofollow noopener noreferrer" title="https://blog.didiyun.com/index.php/2018/11/20/zookeeper/">基于Zookeeper的分布式锁原理及实现</a>
