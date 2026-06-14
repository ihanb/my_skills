# 信号槽通信模式 (Signal-Slot Patterns)

## 模式总览

Qt 项目的复杂度集中在通信模式上。选错模式会导致模块间耦合指数级增长。以下是四种核心模式，按适用场景排列：

| 模式 | 耦合度 | 适用场景 | 典型用法 |
|------|--------|----------|----------|
| 直接信号槽 | 中 | 父子组件、Owner-Ownee | `connect(button, &QPushButton::clicked, this, &MyWidget::OnClick)` |
| SignalBus | 低 | 跨模块广播、插件通信 | `SignalBus::Instance()->DataReceived(id, data)` |
| 回调/函数指针 | 高 | 高频数据流、性能敏感路径 | `parser->SetOnFrameCallback([](auto& f){ ... })` |
| QMetaObject::invokeMethod | 低 | 跨线程方法调用 | `QMetaObject::invokeMethod(worker, "Process", Qt::QueuedConnection, Q_ARG(...))` |

## 模式 1：直接信号槽

**适用条件**：
- 发送者和接收者之间存在明确的所有权关系（父子、Owner-Ownee）
- 连接数量 ≤ 3（一对 ≤ 三）
- 同一线程

```cpp
// ✅ 经典模式：父 Widget 连接子 Widget 的信号
class MainWindow : public QMainWindow {
    MainWindow() {
        auto* panel = new StatusPanel(this);
        auto* manager = new DeviceManager(this);

        // 子组件 → Manager
        connect(panel, &StatusPanel::ConnectRequested,
                manager, &DeviceManager::ConnectToDevice);

        // Manager → 子组件
        connect(manager, &DeviceManager::DataUpdated,
                panel, &StatusPanel::OnDataUpdated);

        // 生命周期：panel 和 manager 都是 MainWindow 的子对象，
        // MainWindow 销毁时自动回收，无需手动 disconnect
    }
};
```

**反模式警告**：

```cpp
// ❌ 不要连接信号到不相关的组件
connect(someRandomButton, &QPushButton::clicked,
        anotherRandomLabel, &QLabel::clear);
// 这建立了隐藏的耦合：button "知道" label 的存在
// 应该由共同的 Owner 来协调
```

## 模式 2：SignalBus（信号总线）

**适用条件**：
- 1 对 N 广播（一条数据 N 个消费者）
- 发送者和接收者完全解耦（互相不知道对方存在）
- 跨模块边界（插件 ↔ Core）

```cpp
// signal_bus.h —— 单例
class SignalBus : public QObject {
    Q_OBJECT
public:
    static SignalBus* Instance();

signals:
    // 按领域组织信号
    // 数据域
    void DataFrameReceived(DeviceId id, QVariantMap fields);
    void RawBytesReceived(DeviceId id, QByteArray data);

    // 设备域
    void DeviceConnected(DeviceId id);
    void DeviceDisconnected(DeviceId id);
    void DeviceSelected(DeviceId id);

    // 指令域
    void CommandRequested(DeviceId id, QString command, QVariantMap params);
    void CommandCompleted(DeviceId id, QString command, bool success);

    // 日志域
    void LogEntryAdded(DeviceId id, int level, QString source, QString message);

private:
    explicit SignalBus(QObject* parent = nullptr);
    static SignalBus* instance_;
};
```

**发送方**：

```cpp
// 任何位置，无需持有接收方的引用
SignalBus::Instance()->DataFrameReceived(deviceId, fields);
SignalBus::Instance()->LogEntryAdded(deviceId, LogLevel::kWarning, "protocol", "心跳超时");
```

**接收方**：

```cpp
// 构造函数中连接
StatusPanel::StatusPanel(QWidget* parent) : QWidget(parent) {
    auto* bus = SignalBus::Instance();
    connect(bus, &SignalBus::DataFrameReceived,
            this, &StatusPanel::OnDataFrame);
    connect(bus, &SignalBus::DeviceSelected,
            this, &StatusPanel::OnDeviceSelected);
}
```

### SignalBus 的设计原则

1. **按领域分组**：不要把 50 个信号平铺在一个类中，超过 15 个信号时考虑拆分为多个 Bus
2. **信号参数不要超过 4 个**：超过时用 struct 封装
3. **SignalBus 不包含逻辑**：它是纯粹的转发层，信号路由逻辑放在 Core 的 Manager/Service 中

```cpp
// ✅ 参数过多时用 struct
struct CommandEvent {
    DeviceId deviceId;
    QString command;
    QVariantMap params;
    QDateTime timestamp;
    int priority;
    QString requestId;
};
// 信号简化为
signals:
    void CommandRequested(const CommandEvent& event);

// ❌ 参数爆炸
signals:
    void CommandRequested(DeviceId, QString, QVariantMap, QDateTime, int, QString);
```

## 模式 3：函数回调 / std::function

**适用条件**：
- 高频数据流（如 100Hz 传感器帧），信号槽开销不可接受
- 紧耦合可接受（解析器和消费者通常一起编译）

```cpp
// 数据解析器使用回调而非信号
class DataParser {
public:
    using FrameCallback = std::function<void(const DataFrame&)>;

    void SetOnFrameReady(FrameCallback cb) { onFrameReady_ = std::move(cb); }

    void FeedBytes(QByteArray bytes) {
        // ... 解析
        if (frameReady && onFrameReady_) {
            onFrameReady_(frame);  // 直接调用，无事件循环开销
        }
    }

private:
    FrameCallback onFrameReady_;
};
```

**何时用回调 vs 信号**：
- 每秒 < 100 次调用：信号槽完全够用（开销 ~1μs）
- 每秒 100-1000 次：信号槽仍可用，但考虑批量投递
- 每秒 > 1000 次：使用回调或共享队列

## 模式 4：QMetaObject::invokeMethod

**适用条件**：
- 跨线程调用其他线程对象的方法
- 发送方不持有接收方类型的头文件

```cpp
// 主线程请求工作线程执行操作
QMetaObject::invokeMethod(deviceWorker_, "SendCommand",
                          Qt::QueuedConnection,
                          Q_ARG(QString, "emergency_stop"),
                          Q_ARG(QVariantMap, params));
```

**安全规则**：
- 总是使用 `Qt::QueuedConnection` 跨线程调用
- 使用 `Q_ARG` 宏确保类型正确
- `invokeMethod` 在目标对象被删除后静默失败，比直接调用安全

## 跨线程信号安全

```cpp
// 场景：Worker 在工作线程，MainWindow 在主线程

// ✅ 方式 1：显式指定队列连接
connect(worker_, &DeviceWorker::DataReady,
        this, &MainWindow::OnData,
        Qt::QueuedConnection);  // 数据从工作线程安全传递到主线程

// ✅ 方式 2：连接类型由 Qt 自动推断 (当 sender 和 receiver 在不同线程时自动 Queued)
connect(worker_, &DeviceWorker::DataReady,
        this, &MainWindow::OnData);
// 等价于方式 1，但显式写 Qt::QueuedConnection 更能表达意图

// ❌ 错误：跨线程直接连接
connect(worker_, &DeviceWorker::DataReady,
        this, &MainWindow::OnData,
        Qt::DirectConnection);  // OnData 在工作线程执行！UI 崩溃！
```

## 信号槽检查清单

在你的代码中检查：

- [ ] 直接信号槽只用于父子组件或同一 Owner 的组件
- [ ] 跨模块通信（如插件 ↔ Core）使用 SignalBus
- [ ] 没有信号槽链超过 3 层（A→B→C→D）——考虑 SignalBus 扁平化
- [ ] SignalBus 参数不超过 4 个，超过用 struct
- [ ] 跨线程连接明确指定 `Qt::QueuedConnection`
- [ ] 高频数据路径不使用信号槽（> 1000 calls/s），改用回调
- [ ] 不需要手动 disconnect：利用 QObject 父子关系自动回收
