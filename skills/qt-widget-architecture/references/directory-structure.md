# 目录结构详解 (Directory Structure)

## 目录组织的首要原则

> **任何开发者打开项目，应能在 30 秒内找到任意源文件的位置。**

这要求目录按**功能模块**而非**文件类型**组织。

## 完整模板

```
ProjectName/
├── .clang-format                  # 代码格式化配置
├── .gitignore
├── CMakeLists.txt                 # 根构建脚本
├── LICENSE
├── README.md
│
├── cmake/                         # CMake 辅助模块
│   ├── CompilerWarnings.cmake     # 编译器警告统一配置
│   ├── Sanitizers.cmake           # ASan/TSan/UBSan 选项
│   ├── StaticAnalyzers.cmake      # clang-tidy 集成
│   └── InstallRules.cmake         # 安装规则
│
├── src/
│   ├── CMakeLists.txt             # 可选：子目录 CMake
│   ├── main.cpp                   # QApplication 入口
│   │
│   ├── app/                       # 应用层
│   │   ├── mainwindow.h
│   │   ├── mainwindow.cpp
│   │   ├── mainwindow.ui          # Qt Designer 表单（可选）
│   │   ├── application.h / .cpp   # 自定义 QApplication 子类
│   │   └── app_settings.h / .cpp  # QSettings 封装
│   │
│   ├── core/                      # 核心业务逻辑
│   │   ├── models/                # 纯数据模型 (POD struct)
│   │   │   ├── device_config.h
│   │   │   ├── sensor_data.h
│   │   │   ├── command_record.h
│   │   │   └── log_entry.h
│   │   ├── managers/              # 管理器类
│   │   │   ├── device_manager.h / .cpp
│   │   │   ├── plugin_manager.h / .cpp
│   │   │   └── task_scheduler.h / .cpp
│   │   ├── services/              # 服务类（长期运行）
│   │   │   ├── recorder_service.h / .cpp
│   │   │   ├── log_service.h / .cpp
│   │   │   └── alert_service.h / .cpp
│   │   ├── dispatchers/           # 分发器/路由器
│   │   │   └── command_dispatcher.h / .cpp
│   │   └── signal_bus.h / .cpp    # 全局信号总线
│   │
│   ├── ui/                        # 通用 UI 组件
│   │   ├── widgets/               # 自定义控件
│   │   │   ├── speedometer_widget.h / .cpp
│   │   │   ├── battery_gauge.h / .cpp
│   │   │   ├── led_indicator.h / .cpp
│   │   │   └── timeline_slider.h / .cpp
│   │   ├── dialogs/               # 对话框
│   │   │   ├── settings_dialog.h / .cpp
│   │   │   ├── about_dialog.h / .cpp
│   │   │   └── device_wizard.h / .cpp
│   │   ├── panels/                # 功能面板 (QDockWidget 内容)
│   │   │   ├── status_panel.h / .cpp
│   │   │   ├── log_panel.h / .cpp
│   │   │   └── command_panel.h / .cpp
│   │   ├── delegates/             # 自定义 View Delegate
│   │   │   ├── log_level_delegate.h / .cpp
│   │   │   └── status_delegate.h / .cpp
│   │   └── theme/                 # 主题与样式
│   │       ├── style_manager.h / .cpp
│   │       └── palette.h
│   │
│   ├── data/                      # 数据访问层
│   │   ├── dao/                   # Data Access Objects
│   │   │   ├── device_dao.h / .cpp
│   │   │   ├── status_dao.h / .cpp
│   │   │   ├── command_dao.h / .cpp
│   │   │   └── log_dao.h / .cpp
│   │   ├── database/              # 数据库基础设施
│   │   │   ├── database_manager.h / .cpp
│   │   │   ├── migration.h / .cpp
│   │   │   └── connection_pool.h / .cpp
│   │   └── repository/            # Repository 模式（可选）
│   │       └── device_repository.h / .cpp
│   │
│   ├── network/                   # 网络通信
│   │   ├── tcp_client.h / .cpp
│   │   ├── udp_receiver.h / .cpp
│   │   └── serial_port.h / .cpp
│   │
│   ├── plugins/                   # 插件系统
│   │   ├── interfaces/            # 纯虚接口（插件开发者和 Core 共享）
│   │   │   ├── iplugin.h
│   │   │   ├── idevice_plugin.h
│   │   │   └── iui_plugin.h
│   │   └── builtin/               # 内置插件实现
│   │       ├── tcp_device_plugin/
│   │       │   ├── tcp_device_plugin.h / .cpp
│   │       │   └── tcp_device_plugin.json
│   │       └── status_panel_plugin/
│   │           ├── status_panel_plugin.h / .cpp
│   │           └── status_panel_plugin.json
│   │
│   └── common/                    # 跨模块共享（最小化）
│       ├── types.h                # DeviceId, RecordingId 等类型别名
│       ├── constants.h            # constexpr 常量
│       ├── enums.h                # 枚举定义
│       └── utils/                 # 纯函数工具
│           ├── string_utils.h
│           ├── time_utils.h
│           └── crc_utils.h
│
├── tests/                         # 测试
│   ├── CMakeLists.txt
│   ├── main.cpp                   # Qt Test 入口
│   ├── core/
│   │   ├── tst_device_manager.cpp
│   │   ├── tst_command_dispatcher.cpp
│   │   └── tst_signal_bus.cpp
│   ├── data/
│   │   ├── tst_device_dao.cpp
│   │   └── tst_status_dao.cpp
│   └── ui/                        # UI 测试（较少）
│       └── tst_device_list_model.cpp
│
├── resources/                     # Qt 资源
│   ├── resources.qrc
│   ├── icons/                     # SVG/PNG 图标
│   │   ├── app_icon.svg
│   │   ├── device_online.svg
│   │   └── device_offline.svg
│   ├── styles/                    # QSS 样式表
│   │   ├── light_theme.qss
│   │   └── dark_theme.qss
│   └── translations/              # Qt Linguist 翻译
│       ├── app_zh_CN.ts
│       └── app_en_US.ts
│
├── docs/                          # 文档
│   ├── architecture.md
│   ├── plugin_development.md
│   └── api_reference.md
│
├── deploy/                        # 部署相关
│   ├── linux/
│   │   └── package.sh
│   └── windows/
│       └── installer.nsi
│
└── third_party/                   # 第三方依赖（非 vcpkg/conan 管理时）
    └── ...
```

## 目录规模决策

| 项目规模 | 目录策略 |
|----------|----------|
| 单窗口工具 (< 10 文件) | `src/app/` + `src/core/` 两层即可，数据层可简化为 `src/core/` 内的 helper |
| 中小型项目 (10-50 文件) | 完整四层 (`app/`, `core/`, `ui/`, `data/`)，无需 `managers/` vs `services/` 细分 |
| 大型项目 (50-200 文件) | 完整模板，`core/` 内细分 `models/` `managers/` `services/` |
| 超大型项目 (> 200 文件) | 考虑将 `core/` 拆分为多个子模块（如 `device_core/`, `recording_core/`） |

## 目录反模式

### ❌ 按文件类型组织

```
src/
├── headers/          # 所有 .h 放一起
├── sources/          # 所有 .cpp 放一起
├── ui/               # 所有 .ui 放一起
└── resources/        # 所有资源放一起
```

**为什么不好**：修改一个功能需要跨越 4 个不相关的目录。

### ❌ 所有代码平铺在 src/

```
src/
├── main.cpp
├── mainwindow.h
├── mainwindow.cpp
├── device_manager.h
├── device_manager.cpp
├── status_panel.h
├── status_panel.cpp
├── device_dao.h
├── device_dao.cpp
├── ... (30+ 文件)
```

**为什么不好**：超过 20 个文件后，浏览困难，新人不知道从哪看起。

### ❌ UI 组件放在 Core 旁边

```
src/
├── core/
│   ├── device_manager.h
│   └── status_panel.h      # UI 实现在 core/ 目录
```

**为什么不好**：编译约束失效——`status_panel.h` 自然可以 include `device_manager.h`，反之也很容易发生。

## 迁移指南

如果现有项目已经混乱，按以下步骤渐进式重构：

1. **先分离 Common 层**：提取纯类型定义和常量——最安全，不改变行为
2. **再分离 Data 层**：提取数据库操作到独立的 DAO 类——改动小，收益大
3. **然后重构 Core 层**：从 MainWindow 中提取 Manager/Service 类——需要拆散庞大函数
4. **最后整理 UI 层**：这时候 MainWindow 应该已经瘦身到合理的尺寸——移走独立的 Panel/Widget 不再困难

每一步提交一次，确保编译通过后再进行下一步。
