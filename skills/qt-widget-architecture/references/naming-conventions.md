# 命名规范详解 (Naming Conventions)

## 命名哲学

Qt 项目的命名挑战在于：**Qt 自身使用 PascalCase**，而 C++ 标准库使用 **snake_case**。我们在两者之间寻求一致性而非教条式的纯粹。

核心原则：
- **文件系统**：snake_case（跨平台兼容性最好）
- **C++ 层面**：与 Qt 一致的 PascalCase 用于类/函数，snake_case_ 用于成员变量
- **一致性 > 具体风格**：选择一种风格后，全项目严格遵守

## 文件命名

| 内容 | 约定 | 示例 |
|------|------|------|
| 类头文件 | `snake_case.h` | `device_manager.h` |
| 类源文件 | `snake_case.cpp` | `device_manager.cpp` |
| 模块头文件 (纯声明) | `snake_case.h` | `plugin_interfaces.h` |
| 测试文件 | `tst_snake_case.cpp` | `tst_device_manager.cpp` |
| UI Designer 文件 | `snake_case.ui` | `settings_dialog.ui` |
| 资源文件 | `snake_case.qrc` | `resources.qrc` |
| CMake 模块 | `PascalCase.cmake` | `CompilerWarnings.cmake` |
| QSS 样式表 | `snake_case.qss` | `dark_theme.qss` |

**文件命名要点**：
- 与内部主类名一致：`DeviceManager` 类的文件是 `device_manager.h`
- 一个 `.h` / `.cpp` 对只包含一个主类
- 小型辅助结构（enum、简短的 POD struct）可以放在所在模块的 `.h` 文件中

## 类命名

### 核心命名表

| 角色 | 命名模式 | 示例 |
|------|----------|------|
| 主窗口 | `MainWindow` | — |
| 管理器 (管理对象生命周期) | `XxxManager` | `DeviceManager`, `PluginManager` |
| 服务 (提供持续服务) | `XxxService` | `RecorderService`, `LogService`, `AlertService` |
| 自定义 Widget | `XxxWidget` | `SpeedometerWidget`, `BatteryGaugeWidget` |
| 面板 (Dock 内容) | `XxxPanel` | `StatusPanel`, `LogPanel`, `CommandPanel` |
| 对话框 | `XxxDialog` | `SettingsDialog`, `AboutDialog`, `DeviceWizard` |
| 数据 Model | `XxxModel` | `DeviceListModel`, `LogTableModel` |
| View Delegate | `XxxDelegate` | `LogLevelDelegate`, `StatusColorDelegate` |
| 数据记录 (struct) | `XxxData`, `XxxInfo`, `XxxRecord` | `SensorData`, `RecordingInfo` |
| 接口 (纯虚) | `IXxx` | `IPlugin`, `IDeviceProtocol`, `IDataFormat` |
| DAO | `XxxDao` | `DeviceDao`, `StatusHistoryDao` |
| 工具类 (静态方法) | `XxxUtils` | `StringUtils`, `TimeUtils` |
| Worker (线程) | `XxxWorker` | `DeviceWorker`, `DatabaseWorker` |

### Manager vs Service 的区分

这是最容易混淆的两个后缀：

```
Manager: 管理一组对象的生命周期、查找、增删改查
  → DeviceManager 管理 DeviceConfig 对象的集合
  → PluginManager 管理插件的加载/卸载/查找

Service: 提供持续运行的业务服务，内部有状态机或事件循环
  → RecorderService 有 录制中/暂停/停止 的状态机
  → LogService 持续收集、过滤、写入日志
  → AlertService 持续评估告警条件
```

## 成员变量

```cpp
class DeviceManager : public QObject {
private:
    // ✅ 普通成员：snake_case_ (尾下划线)
    QHash<QString, DeviceConfig> devices_;
    QList<DeviceId> pendingConnections_;
    bool isInitialized_ = false;

    // ✅ 指针成员：snake_case_ 并显式初始化为 nullptr
    RecorderService* recorder_ = nullptr;
    PluginManager* pluginManager_ = nullptr;

    // ✅ Qt 对象子成员：snake_case_
    QTimer heartbeatTimer_;
};
```

**为什么尾下划线**：
- 在成员函数体内，`devices_` 一眼可识别为成员，`devices` 是局部变量
- 与 Qt 框架源码 (qobject.h, qwidget.cpp) 风格一致
- `m_devices` 的匈牙利前缀在现代 IDE 中显得冗余，尾下划线足够了

## 函数命名

```cpp
class DeviceManager {
public:
    // ✅ 公开方法：PascalCase (与 Qt 一致)
    bool AddDevice(const DeviceConfig& cfg);
    bool RemoveDevice(DeviceId id);
    std::optional<DeviceConfig> GetDevice(DeviceId id) const;
    int DeviceCount() const;

    // ✅ Qt 事件处理：遵循 Qt 命名
    void timerEvent(QTimerEvent* event) override;
    void customEvent(QEvent* event) override;

private:
    // ✅ 私有辅助方法：PascalCase 或以小写开头均可，但保持统一
    void LoadFromDatabase();
    bool ValidateConfig(const DeviceConfig& cfg) const;
};
```

### Getter / Setter

Qt 属性系统推荐无前缀的 getter：

```cpp
// ✅ Qt 风格：无 "get" 前缀
QString Name() const;
void SetName(const QString& name);

// ❌ Java 风格：不推荐在 Qt 项目中使用
QString getName() const;
void setName(const QString& name);

// 例外：返回 bool 的 getter 用 Is/Has/Can 前缀
bool IsConnected() const;
bool HasPendingCommands() const;
bool CanExecute(DeviceId id) const;
```

## 信号命名

信号描述**已发生的事件**，用过去时：

```cpp
signals:
    // ✅ 好的信号名
    void DeviceAdded(DeviceId id, const DeviceConfig& cfg);
    void DeviceRemoved(DeviceId id);
    void ConnectionStateChanged(DeviceId id, bool connected);
    void DataReceived(DeviceId id, QByteArray raw);
    void CommandExecuted(DeviceId id, const CommandResult& result);
    void ErrorOccurred(DeviceId id, QString message);
    void SpeedLimitExceeded(DeviceId id, double speed, double limit);

    // ❌ 不好的信号名 (命令式，像函数调用)
    void addDevice(DeviceId id);
    void changeConnection(DeviceId id);
    void error(DeviceId id, QString msg);  // 太泛化
```

## 槽函数命名

```cpp
public slots:
    // ✅ 模式 1：On + 事件 (Qt 经典风格)
    void OnDeviceSelected(DeviceId id);
    void OnDataFrameReceived(DeviceId id, const DataFrame& frame);
    void OnConnectionStateChanged(DeviceId id, bool connected);

    // ✅ 模式 2：动作名
    void RefreshDeviceList();
    void ClearLogs();
    void ExportToCsv();

private slots:
    void OnHeartbeatTimeout();
    void OnReconnectTimer();
```

## 枚举命名

```cpp
// ✅ enum class + 枚举值 k PascalCase
enum class ConnectionState {
    kDisconnected,
    kConnecting,
    kConnected,
    kDisconnecting,
};

enum class LogLevel {
    kDebug = 0,
    kInfo = 1,
    kWarning = 2,
    kError = 3,
    kFatal = 4,
};

// ✅ 需要 QML/QVariant 支持时使用 Q_NAMES / Q_ENUM
class DeviceManager : public QObject {
    Q_OBJECT
public:
    enum class DeviceStatus {
        kOnline,
        kOffline,
        kError,
    };
    Q_ENUM(DeviceStatus)  // 注册到 Qt 元对象系统
};

// ❌ 避免：C 风格 enum
enum { ONLINE, OFFLINE, ERROR }; // 没有作用域，命名冲突风险
```

## 变量与常量

```cpp
// ✅ 局部变量：snake_case
int retry_count = 0;
QString device_name = config.name;

// ✅ constexpr 常量：k PascalCase (放在 constants.h)
namespace Constants {
    constexpr int kMaxRetryAttempts = 3;
    constexpr int kHeartbeatIntervalMs = 5000;
    constexpr int kDefaultPort = 8080;
    constexpr double kSpeedLimitKmh = 120.0;
}

// ✅ 宏 (不得已时)：UPPER_SNAKE_CASE
#define PLUGIN_API_VERSION "1.0"
#define SAFE_DELETE(ptr) do { delete (ptr); (ptr) = nullptr; } while (0)
```

## QML / Q_PROPERTY 命名

```cpp
// ✅ Q_PROPERTY 命名：PascalCase property, snake_case 成员
class DeviceInfo : public QObject {
    Q_OBJECT
    Q_PROPERTY(QString deviceId READ DeviceId WRITE SetDeviceId NOTIFY DeviceIdChanged)
    Q_PROPERTY(bool isOnline READ IsOnline NOTIFY IsOnlineChanged)

public:
    QString DeviceId() const { return deviceId_; }
    void SetDeviceId(const QString& id) { deviceId_ = id; emit DeviceIdChanged(); }
    bool IsOnline() const { return isOnline_; }

signals:
    void DeviceIdChanged();
    void IsOnlineChanged();

private:
    QString deviceId_;
    bool isOnline_ = false;
};
```
