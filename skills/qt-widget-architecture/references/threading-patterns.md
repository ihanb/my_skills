# 多线程模式 (Threading Patterns)

## Qt 线程模型核心原则

> **GUI 线程只做 GUI 的事。所有 I/O、计算、阻塞操作必须在工作线程。**

违反这条原则的直接后果：界面卡顿、无响应，用户强制关闭应用。

## 线程角色划分

```
┌─────────────────────────────────────────────────────────┐
│  主线程 (GUI Thread / Main Thread)                       │
│  - 所有 QWidget 创建、显示、更新                          │
│  - 用户交互事件 (鼠标、键盘、触摸)                         │
│  - QTimer (UI 刷新、动画帧)                               │
│  - 信号槽分发                            ‎                │
│  ⚠️ 此线程不做 I/O、不做耗时计算                          │
└─────────────────────────────────────────────────────────┘
         │                    │                    │
    signal/slot          signal/slot          signal/slot
   + invokeMethod       + invokeMethod       + invokeMethod
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Worker Thread │  │ Worker Thread │  │ QThreadPool  │
│ 设备 I/O      │  │ 数据库写入    │  │ 零散异步任务 │
│ QTcpSocket    │  │ QSqlDatabase │  │ QtConcurrent │
│ QSerialPort   │  │ 文件 I/O     │  │ run()        │
└──────────────┘  └──────────────┘  └──────────────┘
```

## 模式 1：Worker QObject + QThread (推荐)

这是最安全、最灵活的线程模式：

```cpp
// worker.h
class DeviceWorker : public QObject {
    Q_OBJECT
public:
    explicit DeviceWorker(QObject* parent = nullptr);

public slots:
    void ConnectToDevice(const QString& address, int port);
    void Disconnect();
    void SendCommand(const QByteArray& data);

signals:
    void Connected();
    void Disconnected();
    void DataReceived(QByteArray raw);
    void ErrorOccurred(QString message);

private:
    QTcpSocket* socket_ = nullptr;
    void OnSocketConnected();
    void OnSocketReadyRead();
    void OnSocketError(QAbstractSocket::SocketError error);
};

// 启动代码 (在主线程)
auto* deviceThread = new QThread(this);
auto* deviceWorker = new DeviceWorker();  // 无 parent！
deviceWorker->moveToThread(deviceThread);

// 线程启动时执行连接
connect(deviceThread, &QThread::started,
        deviceWorker, [deviceWorker, addr = "192.168.1.10", port = 8080]() {
    deviceWorker->ConnectToDevice(addr, port);
});

// 线程结束时清理
connect(deviceThread, &QThread::finished,
        deviceWorker, &QObject::deleteLater);

// 主线程 ← Worker 通信
connect(deviceWorker, &DeviceWorker::DataReceived,
        this, &MainWindow::OnDeviceData,
        Qt::QueuedConnection);  // 必须队列连接

deviceThread->start();
```

**关键细节**：
- Worker 创建时**不能带 parent**——带 parent 的 QObject 不能 moveToThread
- `QThread::finished` 信号连接 `deleteLater` 保证 Worker 被正确销毁
- 使用 lambda 或 `QMetaObject::invokeMethod` 向 Worker 槽投递任务

## 模式 2：QtConcurrent + QThreadPool (任务级并发)

适合零散的计算密集型任务：

```cpp
#include <QtConcurrent>

// 单个任务
QFuture<QList<DeviceInfo>> future = QtConcurrent::run([this]() {
    // 这个 lambda 在线程池中执行
    QList<DeviceInfo> result;
    auto query = QSqlQuery(database_);  // 线程独立的数据库连接
    query.exec("SELECT * FROM devices");
    while (query.next()) {
        result.append(DeviceInfo::FromRecord(query.record()));
    }
    return result;
});

// 使用 QFutureWatcher 监控完成
auto* watcher = new QFutureWatcher<QList<DeviceInfo>>(this);
connect(watcher, &QFutureWatcher<QList<DeviceInfo>>::finished,
        this, [this, watcher]() {
    auto devices = watcher->result();
    model_->SetDevices(devices);  // 回到主线程更新 UI
    watcher->deleteLater();
});
watcher->setFuture(future);

// 批量并发处理
QList<QByteArray> rawFrames = GetPendingFrames();
QFuture<QList<DataFrame>> results = QtConcurrent::mapped(
    rawFrames,
    [](const QByteArray& raw) { return ParseFrame(raw); }
);
```

## 模式 3：QObject::invokeMethod (跨线程方法调用)

适合工作线程主动向其他线程的特定对象发送请求：

```cpp
// 主线程调用工作线程的方法
QMetaObject::invokeMethod(deviceWorker_, "SendCommand",
                          Qt::QueuedConnection,
                          Q_ARG(QString, "emergency_stop"),
                          Q_ARG(QVariantMap, params));

// 工作线程调用主线程对象的方法 (不推荐，用信号更好)
QMetaObject::invokeMethod(mainWindow_, "ShowAlert",
                          Qt::QueuedConnection,
                          Q_ARG(QString, "设备断开"),
                          Q_ARG(int, 5000));  // 显示 5 秒
```

**invokeMethod vs 信号的取舍**：
- 使用信号：当通知是事件驱动的、可能有多个接收者时
- 使用 invokeMethod：当请求是命令式的、目标是特定对象、且不想为了一个调用定义信号时

## 铁律 (Non-Negotiables)

### 1. GUI 线程不做阻塞 I/O

```cpp
// ❌ 致命错误：在主线程阻塞等待网络
socket->waitForConnected(5000);  // GUI 冻结 5 秒

// ✅ 正确：异步连接 + 信号通知
socket->connectToHost(addr, port);
// 通过 connected() 信号获知连接结果
```

### 2. 跨线程只发信号，不直接调用

```cpp
// ❌ 错误：工作线程直接操作 UI 对象
void DeviceWorker::OnDataReceived(QByteArray raw) {
    statusLabel_->setText("收到数据");  // 跨线程直接调用 QWidget → 崩溃
}

// ✅ 正确：通过信号转发到主线程
void DeviceWorker::OnDataReceived(QByteArray raw) {
    emit DataReceived(raw);  // mainWindow 在主线程接收
}
```

### 3. QSqlDatabase 线程隔离

```cpp
// ❌ 错误：跨线程共享数据库连接
auto db = QSqlDatabase::database();  // 默认连接
QtConcurrent::run([&db]() {
    QSqlQuery query(db);  // 在其他线程使用默认连接 → 未定义行为
});

// ✅ 正确：每个线程创建自己的连接
QtConcurrent::run([]() {
    QSqlDatabase db = QSqlDatabase::addDatabase("QSQLITE", "worker_conn");
    db.setDatabaseName("data.db");
    db.open();
    QSqlQuery query(db);
    // ...
});
QSqlDatabase::removeDatabase("worker_conn");  // 用完清理
```

### 4. Mutex 粒度要细

```cpp
// ❌ 大锁：锁定时间过长
{
    QMutexLocker lock(&mutex_);
    auto data = ParseLargeJson(raw);     // CPU 密集
    db_.Insert(data);                     // I/O
    emit UpdateUI(data);                  // 可能触发跨线程操作
}
// 锁持有时间可能 > 100ms

// ✅ 细粒度：仅锁住数据结构的读写
{
    QMutexLocker lock(&mutex_);
    auto rawCopy = raw;  // 快速拷贝
}  // 立即释放锁
auto data = ParseLargeJson(rawCopy);  // 无锁
db_.Insert(data);                       // 无锁 (db 有自己的连接)
emit UpdateUI(data);
```

## 线程安全容器与工具

| 需求 | 推荐方案 |
|------|----------|
| 生产者-消费者队列 | `QQueue<T>` + `QMutex` + `QWaitCondition` |
| 简单原子变量 | `std::atomic<T>`, `QAtomicInt` |
| 读多写少缓存 | `QReadWriteLock` |
| 跨线程一次性初始化 | `QAtomicInt::testAndSetAcquire` + 双重检查锁定 |
| 批量处理 | 收集到 vector → 一次性交换 → 处理 |

## 常见线程 Bug 排查

### "Cannot create children for a parent that is in a different thread"

```cpp
// 原因：在 Worker 线程中创建了 QWidget (或其他 parent 在主线程的 QObject)
void Worker::ProcessData() {
    auto* dialog = new QDialog();  // ❌ QDialog 必须属于 GUI 线程
}

// 修复：通过信号通知主线程创建 UI
void Worker::ProcessData() {
    emit ShowDialogRequested();  // 主线程的槽函数中创建 QDialog
}
```

### 对象过早销毁

```cpp
// ❌ 问题：Worker 的槽还在队列中，但 Worker 已销毁
deviceWorker->deleteLater();
// 此时队列中可能还有待执行的槽调用

// ✅ 修复：先停止线程，等线程结束再清理
deviceThread->quit();
deviceThread->wait();  // 等待事件循环结束
deviceWorker->deleteLater();
```
