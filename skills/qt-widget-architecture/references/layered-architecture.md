# 分层架构详解 (Layered Architecture)

## 为什么Qt项目需要分层

Qt Widget 项目最常见的退化模式是"MVC变MainWindow"——所有代码逐渐塞进 `MainWindow` 类，最终成为一个几千行、无法测试、无法重构的巨型类。分层架构是防止这种退化的系统性约束。

### 典型反模式

```cpp
// ❌ 反模式：MainWindow 知道一切
class MainWindow : public QMainWindow {
    void OnDataReceived(QByteArray raw) {
        // 1. 解析 JSON (数据层职责)
        auto doc = QJsonDocument::fromJson(raw);
        // 2. 更新数据库 (数据层职责)
        QSqlQuery query;
        query.exec("INSERT INTO status VALUES(...)");
        // 3. 业务判断 (逻辑层职责)
        if (doc["speed"].toDouble() > 120) {
            // 4. 发送告警 (逻辑层职责)
            SendAlert();
        }
        // 5. 更新UI (UI层职责)
        speedLabel_->setText(doc["speed"].toString());
    }
};
```

这个函数什么都做了，但当需求变更时——换一种数据库、换一套告警规则、换一个UI框架——修改范围无法控制。

## 三层定义

### 1. UI 层 (Presentation)

**目录位置**：`src/ui/`, `src/app/`

**职责**：
- QMainWindow, QDialog, QDockWidget 布局
- 自定义绘制控件 (QPainter-based Widget)
- 用户交互处理 (按钮、菜单、快捷键)
- 数据格式化显示 (数字格式、颜色映射)
- 动画与过渡效果

**硬约束**：
- 可以 `#include` Core 层的头文件
- 可以 `#include` Common 层的头文件
- **禁止** 直接访问数据库 (QSqlQuery)
- **禁止** 直接操作 socket/file
- **禁止** 包含业务规则

```cpp
// ✅ 正确的 UI 层代码
void StatusPanel::OnDataUpdated(DeviceId id, const SensorData& data) {
    // 只做展示相关的事
    speedGauge_->SetValue(data.speed);
    batteryBar_->SetValue(data.batteryPercent);
    UpdateAlarmIndicator(data.HasAlarm());
    // 数值格式化是 UI 层的事
    speedLabel_->setText(QString::number(data.speed, 'f', 1) + " km/h");
}
```

### 2. 逻辑层 (Business Logic / Core)

**目录位置**：`src/core/`

**职责**：
- 业务规则与流程编排
- 数据校验、转换、聚合
- 插件生命周期管理
- 命令分发与响应路由
- 模块间协调

**硬约束**：
- 可以 `#include` Data 层的头文件
- 可以 `#include` Common 层的头文件
- **禁止** `#include` UI 层任何头文件
- **禁止** 直接创建 QWidget / QDialog
- 与 UI 通信**仅通过信号**

```cpp
// ✅ 正确的逻辑层代码
class DeviceManager : public QObject {
    Q_OBJECT
public:
    void ProcessRawData(DeviceId id, QByteArray raw) {
        // 委托数据层解析
        auto result = formatPlugin_->Parse(raw);
        if (!result) {
            emit ErrorOccurred(id, "解析失败: " + result.error().Message());
            return;
        }
        // 业务规则
        if (result->speed > kSpeedLimit) {
            emit SpeedAlert(id, result->speed);
        }
        // 委托数据层存储
        statusDao_->Insert(id, *result);
        // 通知 UI
        emit DataUpdated(id, ToSensorData(*result));
    }

signals:
    void DataUpdated(DeviceId id, const SensorData& data);
    void SpeedAlert(DeviceId id, double speed);
    void ErrorOccurred(DeviceId id, QString message);
};
```

### 3. 数据层 (Data / Infrastructure)

**目录位置**：`src/data/`

**职责**：
- SQLite / SQL 数据库的 CRUD
- 网络连接的建立与数据收发
- 文件 I/O（录制文件、配置文件）
- 序列化 / 反序列化（JSON, Protobuf）

**硬约束**：
- 只能 `#include` Common 层的头文件
- **禁止** 包含任何业务规则
- **禁止** `#include` Core 层和 UI 层的头文件

```cpp
// ✅ 正确的数据层代码
class DeviceDao {
public:
    bool Insert(const DeviceConfig& config) {
        QSqlQuery query(db_);
        query.prepare("INSERT INTO devices (device_id, name, ...) VALUES (...)");
        query.bindValue(":device_id", config.id);
        // ... 纯数据操作，无业务逻辑
        return query.exec();
    }

    std::optional<DeviceConfig> FindById(DeviceId id) {
        // ... 查询并返回，不做任何判断
    }
};
```

## 依赖方向图

```
┌─────────────────────────────────────────────┐
│                  UI Layer                    │
│  src/app/  src/ui/                          │
│  (MainWindow, Widgets, Dialogs, Panels)      │
└──────────────────┬──────────────────────────┘
                   │ can depend on
                   ▼
┌─────────────────────────────────────────────┐
│                Core Layer                    │
│  src/core/                                  │
│  (Managers, Services, SignalBus)            │
└──────────────────┬──────────────────────────┘
                   │ can depend on
                   ▼
┌─────────────────────────────────────────────┐
│                Data Layer                    │
│  src/data/                                  │
│  (DAO, Repository, Network)                 │
└──────────────────┬──────────────────────────┘
                   │ can depend on
                   ▼
┌─────────────────────────────────────────────┐
│              Common Layer                    │
│  src/common/                                │
│  (Types, Enums, Constants, pure Utils)      │
└─────────────────────────────────────────────┘
```

依赖是**单向且向下**的。Common 层在最底部，是唯一被所有层共享的。

## 如何验证分层是否正确

运行以下命令检查：

```bash
# 检查 core/ 是否引用了 ui/ (应该为空)
grep -r '#include.*ui/' src/core/

# 检查 core/ 是否直接访问数据库 (应该通过 data/)
grep -r 'QSqlQuery' src/core/

# 检查 core/ 是否创建 QWidget (应该为空)
grep -r 'QWidget\|QDialog\|QMainWindow' src/core/
```

如果任何一条有输出，说明分层被破坏。
