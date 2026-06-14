# CMake 构建模式 (CMake Patterns)

## 首选构建系统：CMake

Qt 6 官方推荐 CMake，qmake 已进入维护模式。新项目一律使用 CMake。

## 最小可工作 CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.25)
project(MyApp VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Qt6 自动处理：MOC, RCC, UIC
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets)

qt_add_executable(${PROJECT_NAME}
    src/main.cpp
    src/app/mainwindow.h src/app/mainwindow.cpp
)

target_include_directories(${PROJECT_NAME} PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

target_link_libraries(${PROJECT_NAME} PRIVATE
    Qt6::Core Qt6::Gui Qt6::Widgets
)
```

## 多模块/多可执行文件结构

```cmake
# 根 CMakeLists.txt
cmake_minimum_required(VERSION 3.25)
project(MyApp VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets Network Sql)

# ── 子目录 ──
add_subdirectory(src)
add_subdirectory(tests)
```

```cmake
# src/CMakeLists.txt
set(SOURCES
    main.cpp
    app/mainwindow.h app/mainwindow.cpp
    core/managers/device_manager.h core/managers/device_manager.cpp
    core/services/recorder_service.h core/services/recorder_service.cpp
    # ...
)

qt_add_executable(${PROJECT_NAME} ${SOURCES})

target_include_directories(${PROJECT_NAME} PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}  # 使 #include "core/..." 生效
)

target_link_libraries(${PROJECT_NAME} PRIVATE
    Qt6::Core Qt6::Gui Qt6::Widgets Qt6::Network Qt6::Sql
)
```

## 静态库模块（Core Library）

当项目变大，将 `core/` 提取为独立静态库：

```cmake
# src/core/CMakeLists.txt
set(CORE_SOURCES
    managers/device_manager.h managers/device_manager.cpp
    managers/plugin_manager.h managers/plugin_manager.cpp
    services/recorder_service.h services/recorder_service.cpp
)

qt_add_library(myapp_core STATIC ${CORE_SOURCES})

target_include_directories(myapp_core PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/..
)

target_link_libraries(myapp_core PUBLIC
    Qt6::Core Qt6::Network Qt6::Sql
)
```

```cmake
# src/CMakeLists.txt (主可执行文件)
add_subdirectory(core)

qt_add_executable(${PROJECT_NAME} main.cpp app/mainwindow.cpp ...)

target_link_libraries(${PROJECT_NAME} PRIVATE
    myapp_core Qt6::Widgets
)
```

**关键点**：Core 库链接 `Qt6::Core` 但不链接 `Qt6::Widgets`——这是编译期保证 Core 不依赖 UI 的最强约束。

## 编译警告配置

```cmake
# cmake/CompilerWarnings.cmake
function(set_compiler_warnings TARGET)
    if(MSVC)
        target_compile_options(${TARGET} PRIVATE
            /W4 /permissive- /w14242 /w14254 /w14263 /w14265 /w14287
            /we4289 /w14296 /w14311 /w14545 /w14546 /w14547 /w14549
            /w14555 /w14619 /w14640 /w14826 /w14905 /w14906 /w14928
        )
    else()
        target_compile_options(${TARGET} PRIVATE
            -Wall -Wextra -Wpedantic -Wshadow -Wconversion
            -Wsign-conversion -Wnull-dereference -Wdouble-promotion
            -Wformat=2 -Wimplicit-fallthrough
        )
    endif()
endfunction()
```

## Qt 资源编译

```cmake
# 不需要显式处理 .qrc 文件，CMAKE_AUTORCC 会自动编译它
qt_add_resources(${PROJECT_NAME} "app_resources"
    PREFIX "/"
    FILES
        resources/resources.qrc
)
```

## 翻译文件编译

```cmake
qt_add_translations(${PROJECT_NAME}
    TS_FILES
        resources/translations/app_zh_CN.ts
        resources/translations/app_en_US.ts
)
```

## Qt 插件编译

```cmake
# 插件是共享库，不是可执行文件
qt_add_plugin(tcp_device_plugin SHARED
    plugins/builtin/tcp_device/tcp_device_plugin.h
    plugins/builtin/tcp_device/tcp_device_plugin.cpp
)

target_link_libraries(tcp_device_plugin PRIVATE
    myapp_core  # 访问接口定义
    Qt6::Core Qt6::Network
)

# 编译后复制到运行时插件目录
add_custom_command(TARGET tcp_device_plugin POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy
        $<TARGET_FILE:tcp_device_plugin>
        ${CMAKE_BINARY_DIR}/plugins/protocols/
)
```

## 测试编译

```cmake
# tests/CMakeLists.txt
find_package(Qt6 REQUIRED COMPONENTS Test)

enable_testing()

function(add_qt_test TEST_NAME TEST_SOURCE)
    qt_add_executable(${TEST_NAME} ${TEST_SOURCE})
    target_link_libraries(${TEST_NAME} PRIVATE
        Qt6::Test
        myapp_core  # 链接被测模块
    )
    target_include_directories(${TEST_NAME} PRIVATE
        ${CMAKE_SOURCE_DIR}/src
    )
    add_test(NAME ${TEST_NAME} COMMAND ${TEST_NAME})
endfunction()

add_qt_test(test_device_manager core/tst_device_manager.cpp)
add_qt_test(test_device_dao data/tst_device_dao.cpp)
```

## Windows 部署 (windeployqt)

```cmake
# CMake 安装规则
install(TARGETS ${PROJECT_NAME}
    BUNDLE DESTINATION .
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)

# 部署脚本作为自定义目标
add_custom_target(deploy
    COMMAND windeployqt --qmldir ${CMAKE_SOURCE_DIR}/resources/qml
        $<TARGET_FILE:${PROJECT_NAME}>
    DEPENDS ${PROJECT_NAME}
)
```

## 常见陷阱

### ❌ 使用 file(GLOB) 收集源文件

```cmake
# ❌ 不推荐
file(GLOB_RECURSE SOURCES src/*.cpp src/*.h)

# ✅ 推荐：显式列出
set(SOURCES
    src/main.cpp
    src/app/mainwindow.h src/app/mainwindow.cpp
    # ...
)
```

**原因**：新增源文件后 GLOB 不会自动刷新，除非手动重新运行 CMake。这导致"明明加了文件为什么 link 报错"的经典困惑。

### ❌ 使用 include_directories (全局)

```cmake
# ❌ 污染所有 target 的 include 路径
include_directories(src)

# ✅ 限定到单个 target
target_include_directories(${PROJECT_NAME} PRIVATE src)
```

### ❌ 忘记 CMAKE_AUTOMOC 导致链接错误

```cmake
# Qt 项目几乎总是需要这三行
set(CMAKE_AUTOMOC ON)   # 自动 moc
set(CMAKE_AUTORCC ON)   # 自动编译 .qrc
set(CMAKE_AUTOUIC ON)   # 自动编译 .ui → ui_*.h
```

### ❌ MOC 与 C++20 的冲突

如果类包含 `Q_OBJECT` 宏，**不要**将其放在 C++20 module 中。MOC 目前不支持 module。Concept 可以安全使用，因为 concept 不影响 MOC 解析。

## CMake 版本选择

| Qt 版本 | 最低 CMake | 推荐 CMake |
|---------|------------|------------|
| Qt 6.0-6.2 | 3.16 | 3.21 |
| Qt 6.3-6.5 | 3.16 | 3.25 |
| Qt 6.6+ | 3.16 | 3.28+ |

项目中始终使用 `cmake_minimum_required(VERSION 3.25)` 或更高，以获取 `qt_add_executable`、`qt_standard_project_setup` 等便利函数。
