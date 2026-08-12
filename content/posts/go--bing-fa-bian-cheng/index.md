---
categories: ["go"]
title: "go 并发编程"
date: "2020-07-01T00:00:00+08:00"
tags: ["Go", "并发", "性能优化"]
summary: "基本的同步原语 Go 语言在 sync 包中提供了用于同步的一些基本原语，包括常见的 sync.Mutex、sync.RWMutex、sync.WaitGroup、sync.Once。Mutex 数据结构 Go 语言的 sync.Mute"
translationKey: "go--bing-fa-bian-cheng"
---

> 📌 本文原发布于代码星冰乐：[go 并发编程](https://changhuin.github.io/article/2020/e8fc/)

## 基本的同步原语

Go 语言在 sync 包中提供了用于同步的一些基本原语，包括常见的 sync.Mutex、sync.RWMutex、sync.WaitGroup、sync.Once。

### Mutex

**数据结构**

Go 语言的 sync.Mutex 由两个字段 state 和 sema 组成。其中 state 表示当前互斥锁的状态，而 sema 是用于控制锁状态的信号量。

    type Mutex struct { 
        state int32 
        sema uint32 
    }

上述两个字段加起来只占 8 字节空间的结构体表示了 Go 语言中的互斥锁。

**实现原理**

互斥锁的状态比较复杂，如下图所示，最低三位分别表示 mutexLocked、mutexWoken 和 mutexStarving，剩下的位置用来表示当前有多少个 Goroutine 等待互斥锁的释放。

在默认情况下，互斥锁的所有状态位都是 0，int32 中的不同位分别表示了不同的状态：

- mutexLocked — 表示互斥锁的锁定状态；
- mutexWoken — 表示从正常模式被从唤醒；
- mutexStarving — 当前的互斥锁进入饥饿状态；
- waitersCount — 当前互斥锁上等待的 Goroutine 个数；

**正常模式和饥饿模式**\
sync.Mutex 有两种模式 — 正常模式和饥饿模式。我们需要在这里先了解正常模式和饥饿模式都是什么，它们有什么样的关系。

在正常模式下，锁的等待者会按照先进先出的顺序获取锁。但是刚被唤起的 Goroutine 与新创建的 Goroutine 竞争时，大概率会获取不到锁，为了减少这种情况的出现，一旦 Goroutine 超过 1ms 没有获取到锁，它就会将当前互斥锁切换到饥饿模式，防止部分 Goroutine 被『饿死』。

饥饿模式是在 Go 语言 1.9 版本引入的优化，目的是保证互斥锁的公平性。

在饥饿模式中，互斥锁会被直接交给等待队列最前面的 Goroutine。新的 Goroutine 在该状态下不能获取锁、也不会进入自旋状态，它们只会在队列的末尾等待。如果一个 Goroutine 获得了互斥锁并且它在队列的末尾或者它等待的时间少于 1ms，那么当前的互斥锁就会被切换回正常模式。

相比于饥饿模式，正常模式下的互斥锁能够提供更好的性能，饥饿模式能避免 Goroutine 由于陷入等待无法获取锁而造成的高尾延时。

**锁的使用**\

    var lock = sync.Mutex{}
    func test_lock() {
        lock.Lock()
        defer lock.Unlock()
        // do something 
    }

**注意事项**

1，Unlock 未加锁或者已解锁的 Mutex 会 panic

2，Mutex 不会比较当前请求的 goroutine 是否已经持有这个锁，所以可以一个 goroutine Lock ,另一个 goroutine Unlock, 但是慎用，避免死锁

3，Mutex 是非重入锁。如果想重入，使用扩展的同步原语。

注：这里解释下重入锁与非重入锁

重入锁：顾名思义，就是指当前线程在获取锁成功后可以反复进入的锁。

不可重入锁：就是指在获取锁成功后需要释放当前锁之后才能再次获取锁。

RWMutex

读写互斥锁 sync.RWMutex 是细粒度的互斥锁，它不限制资源的并发读，但是读写、写写操作无法并行执行。适合写少读多的状态，对并发的读很适合。

|     | 读  | 写  |
|-----|-----|-----|
| 读  | Y   | N   |
| 写  | N   | N   |

一般常见的服务场景中，对资源的读多写少，因为大多数的读请求之间不会相互影响，所以我们可以对读写资源操作进行分离，提高服务的性能。

数据结构\

    type RWMutex struct {
        w           Mutex
        writerSem   uint32
        readerSem   uint32
        readerCount int32
        readerWait  int32
    }

在上面的代码中的五个字段的含义分别是：

- w — 复用互斥锁提供的能力；
- writerSem 和 readerSem — 分别用于写等待读和读等待写：
- readerCount 存储了当前正在执行的读操作的数量；
- readerWait 表示当写操作被阻塞时等待的读操作个数；

### 写锁

**获取写锁**\

    func (rw *RWMutex) Lock() {
        rw.w.Lock()
            // 阻塞后续的读操作
        r := atomic.AddInt32(&rw.readerCount, -rwmutexMaxReaders) + rwmutexMaxReaders
        if r != 0 && atomic.AddInt32(&rw.readerWait, r) != 0 {
            runtime_SemacquireMutex(&rw.writerSem, false, 0)
        }
    }

**释放写锁**\

    func (rw *RWMutex) Unlock() {
            // 调用 atomic.AddInt32 函数将变回正数，释放读锁；
        r := atomic.AddInt32(&rw.readerCount, rwmutexMaxReaders)
        if r >= rwmutexMaxReaders {
            throw("sync: Unlock of unlocked RWMutex")
        }
            // 通过 for 循环触发所有由于获取读锁而陷入等待的 Goroutine：
        for i := 0; i < int(r); i++ {
            runtime_Semrelease(&rw.readerSem, false, 0)
        }
        rw.w.Unlock()
    }

### 读锁

**获取读锁**\

    func (rw *RWMutex) RLock() {
            // 如果该方法返回负数 — 其他 Goroutine 获得了写锁，当前 Goroutine 就会调用 sync.runtime_SemacquireMutex 陷入休眠等待锁的释放；否则则成功获取读锁
        if atomic.AddInt32(&rw.readerCount, 1) < 0 {
            runtime_SemacquireMutex(&rw.readerSem, false, 0)
        }
    }

**释放读锁**\

    func (rw *RWMutex) RUnlock() {
            // 如果返回值大于等于零 — 读锁直接解锁成功；
            // 如果返回值小于零 — 有一个正在执行的写操作，在这时会调用sync.RWMutex.rUnlockSlow 方法；
        if r := atomic.AddInt32(&rw.readerCount, -1); r < 0 {
            rw.rUnlockSlow(r)
        }
    }

    func (rw *RWMutex) rUnlockSlow(r int32) {
        if r+1 == 0 || r+1 == -rwmutexMaxReaders {
            throw("sync: RUnlock of unlocked RWMutex")
        }
        if atomic.AddInt32(&rw.readerWait, -1) == 0 {
            runtime_Semrelease(&rw.writerSem, false, 1)
        }
    }

### WaitGroup

如下图所示，WaitGroup 可以将原本顺序执行的代码在多个 Goroutine 中并发执行，加快程序处理的速度。

sync.WaitGroup 必须在 sync.WaitGroup.Wait 方法返回之后才能被重新使用；\
sync.WaitGroup.Done 只是对 sync.WaitGroup.Add 方法的简单封装，我们可以向 sync.WaitGroup.Add 方法传入任意负数（需要保证计数器非负）快速将计数器归零以唤醒其他等待的 Goroutine；\
可以同时有多个 Goroutine 等待当前 sync.WaitGroup 计数器的归零，这些 Goroutine 会被同时唤醒；

waitGroup 的例子：\

    package main

    import (
        "fmt"
        "sync"
        "time"
    )

    func worker(id int, wg *sync.WaitGroup) {

        defer wg.Done()

        fmt.Printf("Worker %d starting\n", id)

        time.Sleep(time.Second)
        fmt.Printf("Worker %d done\n", id)
    }

    func main() {

        var wg sync.WaitGroup

        for i := 1; i <= 5; i++ {
            wg.Add(1)
            go worker(i, &wg)
        }

        wg.Wait()
    }
    ``` 
    ### sync.Once
    Go 语言标准库中 sync.Once 可以保证在 Go 程序运行期间的某段代码只会执行一次。

    结构体
    ``` go
    type Once struct {
        done uint32
        m    Mutex
    }

sync.Once.Do 是 sync.Once 结构体对外唯一暴露的方法，该方法会接收一个入参为空的函数：

如果传入的函数已经执行过，就会直接返回；\
如果传入的函数没有执行过，就会调用 sync.Once.doSlow 执行传入的函数：\

    func (o *Once) Do(f func()) {
        if atomic.LoadUint32(&o.done) == 0 {
            o.doSlow(f)
        }
    }

    func (o *Once) doSlow(f func()) {
        o.m.Lock()
        defer o.m.Unlock()
        if o.done == 0 {
            defer atomic.StoreUint32(&o.done, 1)
            f()
        }
    }

sync.Once 执行逻辑：

- 为当前 Goroutine 获取互斥锁；
- 执行传入的无入参函数；
- 运行延迟函数调用，将成员变量 done 更新成 1；
- 通过成员变量 done 确保函数不会执行第二次。

关于 sync.Once 使用的例子：\

    package main

    import (
        "fmt"
        "sync"
    )

    func main() {
        o := &sync.Once{}
        for i := 0; i < 10; i++ {
            o.Do(func() {
                fmt.Println("only once")
            })
            
        }
    }

## Channel

Go 语言中最常见的、也是经常被人提及的设计模式就是：不要通过共享内存的方式进行通信，而是应该通过通信的方式共享内存。

在很多主流的编程语言中，多个线程传递数据的方式一般都是共享内存的方式来实现的，为了解决线程冲突的问题，我们需要限制同一时间能够读写这些变量的线程数量，这与 Go 语言鼓励的方式并不相同。

通过共享内存的方式实现多线程之间的数据传递：

go 中使用 channel 实现 goroutine 之间的数据共享：\

### Channel 类型

- 无缓冲区的 channel
- 有缓冲区的 channel

下图是示意图：\

**非缓冲通道特性：**

- 向此类通道发送元素值的操作会被阻塞，直到至少有一个针对该通道的接收操作开始进行为止。
- 从此类通道接收元素值的操作会被阻塞，直到至少有一个针对该通道的发送操作开始进行为止。
- 针对非缓冲通道的接收操作会在与之相应的发送操作完成之前完成。\
  总结来说就是：如果接收者没有准备好，则发送者会阻塞，反之亦然。

<!-- -->

    package main
    import "fmt"
    func main() {
        var c = make(chan int)
        var a string

        go func() {
            a = "hello world"
            <-c
        }()

        c <- 0
        fmt.Println(a)
    }

### select 多路复用

select 语句提供了一种处理多通道的方法。跟 switch 语句很像，但是每个分支都是一个通道：

- 所有通道都会被监听
- select 会阻塞直到某个通道读取到内容
- 如果多个通道都可以处理，则会以伪随机的方式处理
- 如果有默认分支，并且没有通道就绪，则会立即执行

结合 goroutine、channel、select 的一个简单示例，将 6 个数字 1~6 发送到一个容量为 3 的管道中，两个 goroutine 每秒接收一次数字后打印信息：

    package main

    import (
        "fmt"
        "sync"
        "time"
    )

    func main() {

        ch := make(chan int, 3)
        var wg sync.WaitGroup

        // start 2 goroutines
        for i := 0; i < 2; i++ {
            wg.Add(1)
            go func(id int) {
                tick := time.Tick(1 * time.Second)
                for {
                    select {
                    case <-tick:
                        {
                            i, ok := <-ch
                            if !ok {
                                wg.Done()
                                return
                            }
                            fmt.Println("goroutine", id, "recv", i)
                        }
                    }
                }
            }(i)
        }

        // sender
        for i := 0; i < 6; i++ {
            ch <- i
            fmt.Println("send", i)
        }

        close(ch)
        wg.Wait()
        fmt.Println("main goroutine end")
    }

## 参考文献

<a href="https://colobu.com/2018/12/18/dive-into-sync-mutex/" target="_blank" rel="noopener">https://colobu.com/2018/12/18/dive-into-sync-mutex/</a>

<a href="https://iswade.github.io/articles/go_concurrency/" target="_blank" rel="noopener">https://iswade.github.io/articles/go_concurrency/</a>

<a href="https://segmentfault.com/a/1190000016466500" target="_blank" rel="noopener">https://segmentfault.com/a/1190000016466500</a>

<a href="https://draveness.me/golang/docs/part3-runtime/ch06-concurrency/golang-channel/" target="_blank" rel="noopener">https://draveness.me/golang/docs/part3-runtime/ch06-concurrency/golang-channel/</a>

