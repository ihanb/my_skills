---
name: qt-widget-architecture
description: >
  Qt6 C++ Widget 工程架构规范。当你需要创建 Qt Widget 项目、组织 Qt 项目目录结构、
  设计 Qt 类层次结构、制定 CMake 构建配置、规范信号槽通信模式、设计多线程架构、
  建立 Model-View 分离模式、规划插件架构，或者审查 Qt 项目的架构设计时，使用此 skill。
  Also use this when the user asks about Qt project structure, Qt best practices,
  Qt architecture design, Qt naming conventions, or how to organize a Qt application.
  This skill provides battle-tested patterns from real Qt6 + C++20 projects.
compatibility: Qt 6.x, C++17/20, CMake 3.25+
---

# Qt C++ Widget 工程架构规范

本规范适用于基于 **Qt 6 + CMake + C++17/20** 的 Widget 桌面应用程序。遵循这些规范可确保项目的可维护性、可扩展性和团队协作效率。

## 核心架构原则

### 分层架构 (Layered Architecture)

每个 Qt Widget 项目至少应具备三层分离：

```
┌──────────────────────────────────────┐
│  UI 层 (Presentation)                │
│  QMainWindow, QWidget, QDialog,      │
│  QDockWidget, Custom Controls        │
│  → 仅负责界面布局、控件交互、数据展示   │
├──────────────────────────────────────┤
│  逻辑层 (Business Logic / Core)       │
│  Manager 类, Service 类, Controller  │
│  → 业务规则、数据编排、插件管理        │
│  → 不依赖任何 UI 类，可独立测试        │
├──────────────────────────────────────┤
│  数据层 (Data / Infrastructure)       │
│  DAO, Repository, Network, Serial   │
│  → SQLite/SQL, 网络通信, 文件 I/O     │
│  → 纯数据操作，不含业务逻辑            │
└──────────────────────────────────────┘
```

**为什么要分层**：当 UI 层混杂业务逻辑时，单元测试无法进行，界面框架迁移（如 Qt 5→6）极其痛苦，团队协作时频繁合并冲突。分层是工业化项目的底线要求。

> 详见 [references/layered-architecture.md](references/layered-architecture.md)

### 通信规则 (Communication Rules)

层级间通信遵循严格的方向约束：

| 方向 | 机制 | 规则 |
|------|------|------|
| UI → 逻辑层 | 直接调用 + 信号 | UI 可以调用逻辑层 public 方法，但不能绕过逻辑层直接访问数据层 |
| 逻辑层 → UI | **仅** Qt 信号 | 逻辑层**绝不** `#include` UI 头文件，通过信号通知 UI 更新 |
| 逻辑层 → 数据层 | 直接调用 | 逻辑层持有数据层对象的指针/引用 |
| 数据层 → 逻辑层 | 返回值 / 信号 (异步) | 网络请求等异步操作使用信号返回结果 |

```cpp
// ✅ 正确：逻辑层通过信号通知 UI
class DeviceManager : public QObject {
    Q_OBJECT
signals:
    void deviceConnected(DeviceId id);
    void dataUpdated(DeviceId id, const SensorData& data);
};

// ❌ 错误：逻辑层直接依赖 UI 类
class DeviceManager {
    StatusWidget* statusWidget_; // 编译依赖 UI 头文件，不可测试
};
```

> 详见 [references/signal-slot-patterns.md](references/signal-slot-patterns.md)

---

## 目录结构规范

### 标准项目模板

```
ProjectName/
├── CMakeLists.txt                  # 根构建脚本
├── cmake/                          # CMake 模块 (可选)
│   └── CompilerWarnings.cmake
├── src/
│   ├── main.cpp                    # 入口点
│   ├── app/                        # 应用层 (MainWindow, 应用配置)
│   │   ├── mainwindow.h / .cpp
│   │   └── appconfig.h / .cpp
│   ├── core/                       # 核心业务逻辑 (不依赖 UI)
│   │   ├── models/                 # 数据模型 (纯数据结构)
│   │   ├── managers/               # 管理器 (DeviceManager, TaskManager)
│   │   └── services/               # 服务 (RecorderService, LogService)
│   ├── ui/                         # 通用 UI 组件
│   │   ├── widgets/                # 自定义控件 (Speedometer, LED)
│   │   ├── dialogs/                # 对话框 (SettingsDialog, AboutDialog)
│   │   ├── panels/                 # 功能面板 (StatusPanel, LogPanel)
│   │   └── delegates/              # 自定义 View Delegate
│   ├── data/                       # 数据访问层
│   │   ├── dao/                    # Data Access Objects
│   │   ├── repository/             # Repository 模式封装
│   │   └── database/               # 数据库初始化、迁移脚本
│   ├── network/                    # 网络通信 (可选)
│   │   ├── tcp_client.h / .cpp
│   │   └── protocols/             # 协议解析器
│   ├── plugins/                    # 插件实现 (可选)
│   │   ├── interfaces/            # 插件接口定义
│   │   └── builtin/               # 内置插件
│   └── common/                     # 跨模块共享
│       ├── types.h                 # 通用数据类型
│       ├── constants.h             # 常量定义
│       └── utils.h / .cpp          # 工具函数
├── tests/                          # 单元测试
│   ├── CMakeLists.txt
│   ├── core/                       # 与 src/ 结构对应
│   └── ui/
├── resources/                      # Qt 资源文件
│   ├── resources.qrc
│   ├── icons/
│   ├── styles/                     # QSS 样式表
│   └── translations/              # .ts 翻译文件
├── docs/                           # 项目文档
└── deploy/                         # 部署脚本 (可选)
```

**关键决策**：
- `src/core/` 绝不引用 `src/ui/` 的任何头文件——这是编译层面的硬约束
- `src/common/` 仅放置纯数据结构、枚举和 constexpr 常量，不放任何有逻辑的类
- `tests/` 目录镜像 `src/` 结构，一个源文件对应一个测试文件

> 详见 [references/directory-structure.md](references/directory-structure.md)

---

## 命名规范

### 文件命名

| 类型 | 格式 | 示例 |
|------|------|------|
| 头文件 | `snake_case.h` | `device_manager.h`, `status_panel.h` |
| 源文件 | `snake_case.cpp` | `device_manager.cpp`, `status_panel.cpp` |
| 测试文件 | `tst_snake_case.cpp` | `tst_device_manager.cpp` |
| UI 表单 | `snake_case.ui` | `settings_dialog.ui` |
| CMake 模块 | `PascalCase.cmake` | `CompilerWarnings.cmake` |

### 类命名

| 类型 | 格式 | 示例 |
|------|------|------|
| 管理器/服务 | `XxxManager`, `XxxService` | `DeviceManager`, `RecorderService` |
| 自定义 Widget | `XxxWidget` | `SpeedometerWidget`, `BatteryGaugeWidget` |
| 对话框 | `XxxDialog` | `SettingsDialog`, `AboutDialog` |
| 数据模型 (struct) | `XxxData`, `XxxInfo`, `XxxRecord` | `SensorData`, `RecordingInfo` |
| 接口类 | `IXxx` | `IDeviceProtocol`, `IPlugin` |
| 枚举类型 | `Xxx` 枚举值 `k PascalCase` | `LogLevel::kWarning` |
| DAO 类 | `XxxDao` | `DeviceDao`, `LogDao` |

### 成员变量与函数

```cpp
// 成员变量：snake_case_ (尾下划线)
class DeviceManager {
private:
    QHash<DeviceId, DeviceConfig> devices_;
    RecorderService* recorder_ = nullptr;  // 指针显式初始化
    bool isRunning_ = false;
};

// 函数：PascalCase (与 Qt 框架保持一致)
void ConnectDevice(DeviceId id);
bool IsConnected(DeviceId id) const;

// 信号：描述事件，已发生时态
signals:
    void DeviceConnected(DeviceId id);     // 设备已连接
    void DataUpdated(DeviceId id, const SensorData& data);
    void ErrorOccurred(DeviceId id, QString message);
    void ConnectionStateChanged(DeviceId id, bool connected);

// 槽函数：On + 事件名 (Qt 5 风格) 或 动作名
public slots:
    void OnDeviceSelected(DeviceId id);
    void OnDataReceived(QByteArray raw);
```

### 为什么命名一致性重要

在 Qt 项目中，命名不一致是最大的认知负担来源——开发者必须在不同作者的不同风格间切换。统一命名后，阅读代码时只需关注"这段逻辑在做什么"，而不需要先解析"这段代码叫什么"。

> 详见 [references/naming-conventions.md](references/naming-conventions.md)

---

## CMake 构建规范

### 最小模板

```cmake
cmake_minimum_required(VERSION 3.25)
project(MyApp VERSION 1.0.0 LANGUAGES CXX)

# ── C++ 标准 ──
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ── Qt6 自动处理 ──
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

# ── Qt6 ──
find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets Network Sql)

# ── 源文件组织 ──
set(SOURCES
    src/main.cpp
    src/app/mainwindow.cpp
    # ... 按目录分段列出
)

set(HEADERS
    src/app/mainwindow.h
    # ...
)

# ── 可执行文件 ──
qt_add_executable(${PROJECT_NAME} ${SOURCES} ${HEADERS})

target_include_directories(${PROJECT_NAME} PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

target_link_libraries(${PROJECT_NAME} PRIVATE
    Qt6::Core Qt6::Gui Qt6::Widgets Qt6::Network Qt6::Sql
)
```

### 关键实践

1. **始终使用 `qt_add_executable`** 而非 `add_executable`——前者正确处理 Qt 平台差异
2. **`target_include_directories` 使用 `src/` 根路径**，使 `#include` 从项目根开始：`#include "core/managers/device_manager.h"` 而非 `#include "../core/device_manager.h"`
3. **用变量分组管理源文件列表**，按功能模块分段注释，避免几百行源码混在一起
4. **禁止使用 `file(GLOB ...)`** 收集源文件——新文件需要手动 `cmake --reconfigure`，且容易意外包含测试/临时文件

> 详见 [references/cmake-patterns.md](references/cmake-patterns.md)

---

## 信号槽通信模式

### 松耦合模式：SignalBus

当项目模块超过 5 个，模块间直接信号槽连接会形成 N×N 的依赖网。引入 **SignalBus** 作为中介：

```cpp
// 单例模式，全局唯一
class SignalBus : public QObject {
    Q_OBJECT
public:
    static SignalBus* Instance();

signals:
    // 数据流：设备 → UI
    void DataFrameReceived(DeviceId id, QVariantMap fields);
    // 指令流：UI → 设备
    void CommandDispatched(DeviceId id, QString command, QVariantMap params);
    // 事件流
    void DeviceSelected(DeviceId id);
    void LogEntryAdded(DeviceId id, int level, QString message);

private:
    explicit SignalBus(QObject* parent = nullptr);
};
```

**使用方式**：所有模块只连接到 SignalBus，不相互连接。

```cpp
// 发送方：直接调用
SignalBus::Instance()->DataFrameReceived(deviceId, fields);

// 接收方：构造函数中连接
connect(SignalBus::Instance(), &SignalBus::DataFrameReceived,
        this, &StatusPanel::OnDataFrame);
```

### 何时使用 SignalBus vs 直接信号

| 场景 | 推荐机制 |
|------|----------|
| 父子组件间通信 | 直接信号槽 |
| 1 对 1 的简单通知 | 直接信号槽 |
| 1 对 N 的广播（数据到达、日志） | SignalBus |
| 跨模块通信（插件 ↔ Core） | SignalBus |
| N 对 N 的松耦合 | SignalBus |

### 跨线程信号安全

```cpp
// 当发送对象在 WorkerThread，接收对象在主线程时：
connect(worker, &Worker::DataReady,
        this, &MainWindow::OnData,
        Qt::QueuedConnection);  // 显式指定队列连接

// 高频数据（如 100Hz 传感器数据）避免使用信号：
// 使用 QObject::invokeMethod 或回调队列批量投递
```

> 详见 [references/signal-slot-patterns.md](references/signal-slot-patterns.md)

---

## 多线程规范

### 线程角色划分

```
主线程 (GUI Thread)
  └── 所有 QWidget 操作、用户交互、QTimer
       ↓ 通过信号 / invokeMethod 通信
工作线程 1: 设备 I/O (QTcpSocket, QSerialPort)
工作线程 2: 数据库写入 (QSqlDatabase per thread)
工作线程 3: 数据解析 (CPU 密集型)
QThreadPool: 零散异步任务
```

### Worker 对象模式

```cpp
// Worker：在独立线程中运行的 QObject
class DeviceWorker : public QObject {
    Q_OBJECT
public:
    explicit DeviceWorker(QObject* parent = nullptr);

public slots:
    void ConnectToDevice(QString address, int port);
    void SendCommand(QByteArray data);

signals:
    void Connected();
    void DataReceived(QByteArray raw);
    void ErrorOccurred(QString message);

private:
    QTcpSocket* socket_ = nullptr;
};

// 启动
auto* thread = new QThread(this);
auto* worker = new DeviceWorker();  // 无 parent，由 moveToThread 管理
worker->moveToThread(thread);

connect(thread, &QThread::started, worker, [worker, addr, port]() {
    worker->ConnectToDevice(addr, port);
});
connect(thread, &QThread::finished, worker, &QObject::deleteLater);
thread->start();
```

### 铁律

1. **GUI 线程不做 I/O**：网络、文件、数据库操作必须在工作线程
2. **跨线程只发信号**：工作线程永远不直接调用 UI 对象的方法
3. **QSqlDatabase 线程隔离**：每个线程创建自己的连接，使用 `"conn_" + thread_name` 命名
4. **Mutex 粒度要细**：锁定时间应 < 1ms，长时间操作放到工作线程而非持锁

> 详见 [references/threading-patterns.md](references/threading-patterns.md)

---

## Model-View 模式

### 三层 MVC 在 Qt 中的落地

| 传统 MVC | Qt 实现 | 示例 |
|----------|---------|------|
| Model | `QAbstractItemModel` / `QAbstractTableModel` | `DeviceListModel`, `LogTableModel` |
| View | `QTableView`, `QListView`, `QTreeView` | 直接使用标准 View |
| Controller | Delegate + 信号槽 | `LogLevelDelegate`, `DeviceActionDelegate` |

### 自定义 Model 模板

```cpp
class DeviceListModel : public QAbstractTableModel {
    Q_OBJECT
public:
    enum Column { kName = 0, kStatus, kAddress, kColumnCount };

    explicit DeviceListModel(QObject* parent = nullptr);

    // 必须实现的虚函数
    int rowCount(const QModelIndex& parent = QModelIndex{}) const override;
    int columnCount(const QModelIndex& parent = QModelIndex{}) const override;
    QVariant data(const QModelIndex& index, int role = Qt::DisplayRole) const override;
    QVariant headerData(int section, Qt::Orientation, int role) const override;

    // 数据更新接口 (逻辑层调用)
    void SetDevices(QList<DeviceInfo> devices);
    void UpdateDeviceStatus(DeviceId id, bool online);

private:
    QList<DeviceInfo> devices_;
};
```

### Model-View 使用原则

1. **永远不要直接操作 View 的数据**——通过 Model 的 `setData()` / 自定义方法
2. **Model 放在 `core/` 或 `data/` 目录**——它是数据适配层，不属于 UI
3. **大批量数据更新使用 `beginResetModel()` / `endResetModel()`**——比逐行 `beginInsertRows` 快 10×
4. **自定义 Delegate 用于绘制和编辑**——不要把绘制逻辑写在 View 里

> 详见 [references/model-view-patterns.md](references/model-view-patterns.md)

---

## 插件架构规范

当项目需要动态加载功能模块时，使用 Qt 插件系统：

### 接口定义

```cpp
// 放在 src/plugins/interfaces/ 目录
class IPlugin {
public:
    virtual ~IPlugin() = default;
    virtual QString PluginId() const = 0;
    virtual QString Version() const = 0;
    virtual bool Initialize() = 0;
    virtual void Shutdown() = 0;
};

Q_DECLARE_INTERFACE(IPlugin, "com.myapp.IPlugin/1.0")
```

### 插件目录结构

```
src/plugins/
├── interfaces/             # 接口头文件 (插件和 Core 共享)
│   ├── iplugin.h
│   ├── idevice_plugin.h
│   └── iui_plugin.h
└── builtin/                # 内置插件实现
    ├── tcp_device/
    │   ├── tcp_device_plugin.h / .cpp
    │   └── tcp_device.json  # Qt 插件元数据
    └── status_panel/
        ├── status_panel_plugin.h / .cpp
        └── status_panel.json
```

### 插件加载

```cpp
// PluginManager：放在 src/core/managers/
class PluginManager {
public:
    void ScanDirectory(const QString& dir);
    bool LoadPlugin(const QString& pluginId);
    void UnloadPlugin(const QString& pluginId);

private:
    QHash<QString, QPluginLoader*> loaders_;
    QHash<QString, IPlugin*> instances_;
};
```

**关键约束**：插件只能通过接口头文件 + SignalBus 与 Core 通信，不能直接 include Core 的实现头文件。

> 详见 [references/plugin-patterns.md](references/plugin-patterns.md)

---

## 错误处理与日志

### 错误处理分层

```cpp
// 数据层：返回错误码或 std::optional/std::expected (C++23)
std::expected<DeviceConfig, ParseError> ParseConfig(const QByteArray& json);

// 逻辑层：捕获、转换、通过信号上报
try {
    auto result = ParseConfig(raw);
    if (!result) emit ConfigParseFailed(result.error());
} catch (const std::exception& e) {
    emit InternalError(QString::fromStdString(e.what()));
}

// UI 层：展示错误给用户，提供重试选项
void OnConfigParseFailed(ParseError error) {
    QMessageBox::warning(this, "配置错误",
        QString("无法解析设备配置: %1\n是否重新加载?").arg(error.Message()));
}
```

### 日志规范

| 级别 | 使用场景 | 保留策略 |
|------|----------|----------|
| Debug | 开发调试、详细数据流 | 不写入持久化日志 |
| Info | 关键事件（连接/断开/启动/停止） | 保留 30 天 |
| Warning | 可恢复的异常（超时、重试） | 保留 30 天 |
| Error | 功能失败（指令失败、解析错误） | 永久保留 |
| Fatal | 应用程序即将退出 | 永久保留 |

建议使用 `spdlog` 或封装 `qDebug()` 系列宏，确保日志宏在 Release 下可配置保留级别。

---

## 单元测试规范

### 测试目录结构

```
tests/
├── CMakeLists.txt
├── core/
│   ├── tst_device_manager.cpp
│   ├── tst_command_dispatcher.cpp
│   └── tst_signal_bus.cpp
├── data/
│   ├── tst_device_dao.cpp
│   └── tst_config_parser.cpp
└── ui/
    └── tst_device_list_model.cpp
```

### 测试模板

```cpp
#include <QtTest>

class TestDeviceManager : public QObject {
    Q_OBJECT
private slots:
    void initTestCase();     // 整个测试套件开始前
    void init();             // 每个测试函数开始前
    void TestAddDevice();    // 测试用例
    void TestRemoveDevice();
    void TestConnectDevice_data();  // 数据驱动测试的数据提供
    void TestConnectDevice();       // 数据驱动测试
    void cleanup();          // 每个测试函数结束后
    void cleanupTestCase();  // 整个测试套件结束后
};

void TestDeviceManager::TestAddDevice()
{
    DeviceManager mgr;
    DeviceConfig cfg{.id = "test-001", .address = "192.168.1.1"};
    QVERIFY(mgr.AddDevice(cfg));
    QCOMPARE(mgr.DeviceCount(), 1);
}

QTEST_MAIN(TestDeviceManager)
#include "tst_device_manager.moc"
```

### 测试原则

1. **核心业务逻辑必须有测试**——Manager、Service、DAO 类
2. **UI 层可以不测试**——通过将业务逻辑从 UI 剥离到 Core 来保证可测试性
3. **数据库测试使用 `:memory:` SQLite**——速度快且隔离环境
4. **Mock 外部依赖**（网络、串口）——测试中不应该真正联网

---

## 实施检查清单

新建或审查 Qt Widget 项目时，按以下清单逐项检查：

- [ ] 目录结构遵循 `src/app/` `src/core/` `src/ui/` `src/data/` 分层
- [ ] `src/core/` 没有任何 `#include` UI 头文件的语句
- [ ] CMake 使用 `qt_add_executable` 且 `target_include_directories` 根为 `src/`
- [ ] 类命名遵循规范：Manager/Service/Widget/Dialog/Dao
- [ ] 成员变量使用 `snake_case_` 尾下划线
- [ ] 信号使用已发生时态命名 (DeviceConnected, DataUpdated)
- [ ] 跨模块通信使用 SignalBus 或接口，而非直接依赖
- [ ] 网络/文件/数据库 I/O 不在 GUI 线程执行
- [ ] 数据表使用 `QAbstractTableModel` 而非直接操作 `QTableWidget`
- [ ] 插件通过接口 + 元数据 json 定义，不直接 include 实现
- [ ] 核心 Manager 和 DAO 类有对应的单元测试
- [ ] 日志分级使用，Error 以上有持久化记录

---

## 参考资源

当需要更深入的细节时，阅读对应的参考文件：

| 主题 | 参考文件 |
|------|----------|
| 分层架构详解 | [references/layered-architecture.md](references/layered-architecture.md) |
| 目录结构详解 | [references/directory-structure.md](references/directory-structure.md) |
| 命名规范详解 | [references/naming-conventions.md](references/naming-conventions.md) |
| CMake 构建模式 | [references/cmake-patterns.md](references/cmake-patterns.md) |
| 信号槽模式 | [references/signal-slot-patterns.md](references/signal-slot-patterns.md) |
| 多线程模式 | [references/threading-patterns.md](references/threading-patterns.md) |
| Model-View 模式 | [references/model-view-patterns.md](references/model-view-patterns.md) |
| 插件架构 | [references/plugin-patterns.md](references/plugin-patterns.md) |
