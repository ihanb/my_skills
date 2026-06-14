# 插件架构模式 (Plugin Architecture Patterns)

## 何时使用插件架构

插件架构是有成本的（接口维护、版本兼容、动态加载调试），只在这些场景使用：

- **需求明确要求运行时扩展**：第三方开发者需要添加新功能模块
- **功能模块种类多且不确定**：设备协议、数据格式持续增加
- **需要独立部署和更新**：单个模块的升级不能影响整个应用
- **团队独立开发**：不同团队负责不同模块，需要清晰的接口边界

如果你的项目只有固定的几种功能，直接编译进可执行文件更简单。

## 插件系统三要素

```
┌──────────────────────────────────────────────────┐
│                1. 接口定义 (Contract)              │
│   src/plugins/interfaces/                        │
│   纯虚类 (.h)                                    │
│   Core 和 Plugin 共同依赖这层                     │
└──────────────────────┬───────────────────────────┘
                       │ 实现
┌──────────────────────▼───────────────────────────┐
│              2. 插件实现 (Implementation)          │
│   src/plugins/builtin/xxx_plugin/                │
│   实现接口的 QObject 子类 + 元数据 JSON             │
└──────────────────────┬───────────────────────────┘
                       │ 加载
┌──────────────────────▼───────────────────────────┐
│              3. 插件管理 (Runtime)                │
│   src/core/managers/plugin_manager.cpp           │
│   QPluginLoader 加载、生命周期管理、依赖检查        │
└──────────────────────────────────────────────────┘
```

## 接口定义

接口是整个插件系统最重要的部分——一旦发布就必须向后兼容。

```cpp
// src/plugins/interfaces/iplugin.h
#pragma once
#include <QtPlugin>
#include <QString>

// 所有插件的基础接口
class IPlugin {
public:
    virtual ~IPlugin() = default;

    virtual QString PluginId() const = 0;       // "com.example.tcp_device"
    virtual QString PluginName() const = 0;     // "TCP Device Protocol"
    virtual QString Version() const = 0;        // "1.2.0"

    virtual bool Initialize() = 0;
    virtual void Shutdown() = 0;
    virtual bool IsInitialized() const = 0;
};

Q_DECLARE_INTERFACE(IPlugin, "com.myapp.IPlugin/1.0")
```

```cpp
// src/plugins/interfaces/idevice_plugin.h
#pragma once
#include "iplugin.h"
#include <QObject>

// 设备协议插件的专用接口
class IDevicePlugin : public QObject, public IPlugin {
    Q_OBJECT
public:
    virtual bool Connect(const QString& address, int port) = 0;
    virtual void Disconnect() = 0;
    virtual bool IsConnected() const = 0;
    virtual void SendData(const QByteArray& data) = 0;

signals:
    void Connected();
    void Disconnected();
    void DataReceived(QByteArray data);
    void ErrorOccurred(QString message);
};

Q_DECLARE_INTERFACE(IDevicePlugin, "com.myapp.IDevicePlugin/1.0")
```

**接口设计原则**：
1. **最小化**：只暴露必需的方法，内部实现完全隐藏
2. **返回状态**：每个可能失败的方法返回 bool 或 std::expected
3. **异步通知用信号**：不阻塞调用线程
4. **Version 用语义化版本**：方便插件管理器做兼容性检查
5. **接口 IID 包含版本号**：`"com.myapp.IDevicePlugin/1.0"`——接口变更时递增版本

## 插件实现

```cpp
// src/plugins/builtin/tcp_device/tcp_device_plugin.h
#pragma once
#include "plugins/interfaces/idevice_plugin.h"
#include <QTcpSocket>

class TcpDevicePlugin : public IDevicePlugin {
    Q_OBJECT
    Q_PLUGIN_METADATA(IID "com.myapp.IDevicePlugin" FILE "tcp_device.json")
    Q_INTERFACES(IDevicePlugin)

public:
    TcpDevicePlugin(QObject* parent = nullptr);
    ~TcpDevicePlugin() override;

    // IPlugin
    QString PluginId() const override { return "com.example.tcp_device"; }
    QString PluginName() const override { return "TCP Device Protocol"; }
    QString Version() const override { return "1.0.0"; }
    bool Initialize() override;
    void Shutdown() override;
    bool IsInitialized() const override { return initialized_; }

    // IDevicePlugin
    bool Connect(const QString& address, int port) override;
    void Disconnect() override;
    bool IsConnected() const override;
    void SendData(const QByteArray& data) override;

private slots:
    void OnSocketConnected();
    void OnSocketReadyRead();
    void OnSocketError(QAbstractSocket::SocketError error);

private:
    QTcpSocket* socket_ = nullptr;
    bool initialized_ = false;
};
```

### 插件元数据 JSON

```json
{
    "id": "com.example.tcp_device",
    "name": "TCP Device Protocol",
    "version": "1.0.0",
    "api_version": "1.0",
    "type": "device_protocol",
    "description": "Generic TCP device protocol plugin",
    "author": "Your Team",
    "dependencies": [],
    "platforms": ["linux", "windows"]
}
```

## 插件管理器

```cpp
// src/core/managers/plugin_manager.h
class PluginManager : public QObject {
    Q_OBJECT
public:
    explicit PluginManager(QObject* parent = nullptr);
    ~PluginManager();

    // 扫描插件目录
    void ScanDirectory(const QString& dir);

    // 加载/卸载
    template<typename T>
    T* LoadPlugin(const QString& pluginId);

    bool UnloadPlugin(const QString& pluginId);
    bool IsLoaded(const QString& pluginId) const;

    // 查询
    QList<QString> AvailablePlugins() const;
    QList<QString> LoadedPlugins() const;
    QStringList PluginsOfType(const QString& type) const;

    template<typename T>
    QList<T*> GetLoadedPlugins() const;

signals:
    void PluginLoaded(QString pluginId);
    void PluginUnloaded(QString pluginId);
    void PluginLoadFailed(QString pluginId, QString error);

private:
    struct PluginEntry {
        QString path;           // .so/.dll 文件路径
        QString jsonPath;       // 元数据 JSON 路径
        QVariantMap metadata;   // 解析后的 JSON
        QPluginLoader* loader = nullptr;
        QObject* instance = nullptr;
    };

    QHash<QString, PluginEntry> plugins_;

    QVariantMap ParseMetadata(const QString& jsonPath);
    bool CheckDependencies(const QVariantMap& metadata);
    bool CheckApiVersion(const QVariantMap& metadata);
};
```

## 插件通信约束

```
✅ 允许的通信路径：
  Plugin → Core::SignalBus → Other Plugin
  Plugin → Core::SignalBus → Core::Service
  Core → Plugin::public_method  (通过接口)

❌ 禁止的通信路径：
  Plugin → Plugin 直接调用
  Plugin → 直接操作数据库
  Plugin → 直接创建 QMainWindow/Dialog (UI 插件除外)
```

## 插件目录布局

```
# 开发时 (源码)
src/plugins/
├── interfaces/               # 接口
│   ├── iplugin.h
│   ├── idevice_plugin.h
│   └── iui_plugin.h
└── builtin/                  # 内置插件
    ├── tcp_device/
    │   ├── tcp_device_plugin.h / .cpp
    │   └── tcp_device.json
    └── status_panel/
        ├── status_panel_plugin.h / .cpp
        └── status_panel.json

# 运行时 (编译产物)
build/plugins/
├── devices/                  # 按类型分目录
│   ├── tcp_device_plugin.dll + tcp_device.json
│   └── serial_device_plugin.dll + serial_device.json
├── formats/
│   ├── json_format_plugin.dll + json_format.json
│   └── protobuf_format_plugin.dll + protobuf_format.json
└── ui/
    ├── status_panel_plugin.dll + status_panel.json
    └── log_panel_plugin.dll + log_panel.json
```

## 版本兼容性策略

```cpp
bool PluginManager::CheckApiVersion(const QVariantMap& metadata) {
    QString apiVersion = metadata["api_version"].toString();

    // 语义化版本检查
    auto [major, minor] = ParseVersion(apiVersion);

    if (major != kCurrentApiMajor) {
        // 主版本不匹配 → 拒绝加载
        qWarning() << "Plugin" << metadata["id"].toString()
                   << "API version" << apiVersion
                   << "incompatible with current" << kCurrentApiVersion;
        return false;
    }

    if (minor > kCurrentApiMinor) {
        // 插件要求更高的次版本 → 拒绝（可能使用了新 API）
        qWarning() << "Plugin requires newer API version:" << apiVersion;
        return false;
    }

    return true;  // 向后兼容
}
```

## 常见陷阱

### ❌ 插件和 Core 编译时互相依赖

```
# ❌ 循环依赖
myapp_core → 链接 tcp_device_plugin (为了内置)
tcp_device_plugin → 链接 myapp_core (为了接口)

# ✅ 正确
myapp_core → 不链接任何插件
tcp_device_plugin → 链接 plugin_interfaces (只有接口头文件)
```

解决：接口头文件编译为一个独立的 header-only 目标，或放在 `src/plugins/interfaces/` 由 Core 和插件各自 include。

### ❌ 插件实例化后不检查接口

```cpp
// ❌ 假设 plugin 一定是正确类型
auto* plugin = qobject_cast<IDevicePlugin*>(loader->instance());
plugin->Connect(addr, port); // 如果 qobject_cast 返回 nullptr → 崩溃

// ✅ 总是检查
auto* plugin = qobject_cast<IDevicePlugin*>(loader->instance());
if (!plugin) {
    qCritical() << "Plugin" << pluginId << "does not implement IDevicePlugin";
    loader->unload();
    return nullptr;
}
```

### ❌ 插件卸载时信号槽残留

```cpp
// ❌ 直接卸载 → 其他对象可能有悬空连接
loader->unload();

// ✅ 先断开所有连接
void PluginManager::UnloadPlugin(const QString& pluginId) {
    auto& entry = plugins_[pluginId];
    if (entry.instance) {
        entry.instance->disconnect();  // 断开所有信号槽
        entry.instance->Shutdown();    // 插件自行清理资源
    }
    entry.loader->unload();
    delete entry.loader;
    plugins_.remove(pluginId);
}
```
