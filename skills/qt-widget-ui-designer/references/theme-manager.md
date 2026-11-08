# ThemeManager 与权威色板（单一事实源）

> **本文件是本 Skill 中颜色的唯一事实源。** `SKILL.md`、`html-prototype-guide.md`、
> `html-qt-mapping.md`、`qss-reference.md`、`themes/modern-*.qss` 中出现的所有色值，
> 都必须能在本文件的色板表中找到对应角色；示例里不得再出现第二套设计系统色值。
>
> `themes/modern-light.qss` / `modern-dark.qss` 是本色板的**静态展开快照**（可直接加载），
> 两者同源。修改色板时，先改本文件，再同步两份 qss 快照。

## 1. Step 2 前置条件的处理分支

生成 HTML 视觉原型前，必须先确定色值来源。按顺序判断：

| 情况 | 处理方式 |
|------|---------|
| 项目已有 ThemeManager（或等价色板定义） | 直接读取其 `LoadTheme()` / 色板表，逐 key 映射为 CSS 变量。**项目色板优先于本文件。** |
| 项目没有 ThemeManager（新项目 / 空目录） | 先用本文件第 3 节的实现 Bootstrap 一个 ThemeManager，再以其 `LoadTheme()` 为色值来源；不要在 HTML 原型里凭感觉写色值。 |
| 用户自带色板（品牌色 / 设计规范） | 以用户色板覆盖本文件色板表的同名 key，其余 key 沿用本表；写入 `LoadTheme()` 后再生成原型。 |

**禁止**：从 Material Design、Tailwind 或其他第三方设计系统临时抓一组色值填进原型；
禁止在 HTML、QSS、C++ 里写与 `ThemeManager::ThemeColor()` 不一致的字面量。
色板表是"默认值"而非"必须值"——项目有自己的定义时一切以项目为准。

## 2. 权威色板表

`key` 即 `ThemeManager::ThemeColor(key)` 的入参，也是 HTML 原型 CSS 变量名（去掉 `--` 前缀）。

| key | Light | Dark | 用途 / qss 对应 |
|-----|-------|------|----------------|
| `primary` | `#6200EE` | `#BB86FC` | 主色、主按钮背景、选中态；`*.qss:27` |
| `primary_hover` | `#7C4DFF` | `#D4A5FF` | primary 悬停；`*.qss:37` |
| `primary_variant` | `#3700B3` | `#9B5BCF` | primary 按下 / 深一档；`*.qss:41` |
| `secondary` | `#03DAC6` | `#03DAC6` | 强调色；`*.qss:50` |
| `secondary_variant` | `#00A896` | `#00A896` | secondary 按下 |
| `background` | `#FAFAFA` | `#121212` | 窗口 / 对话框底色；`*.qss:21` |
| `surface` | `#FFFFFF` | `#1E1E1E` | 卡片、输入框、面板；`light.qss:95` / `dark.qss:79` |
| `surface_variant` | `#F5F5F5` | `#2C2C2C` | 次级容器、禁用态、hover 底；`light.qss:110` / `dark.qss:45` |
| `on_background` | `#212121` | `#FFFFFF` | 窗口主文字；`*.qss:22` |
| `on_surface` | `#212121` | `#FFFFFF` | 容器内主文字；`light.qss:96` / `dark.qss:106` |
| `on_surface_secondary` | `#616161` | `#AAAAAA` | 次级文字、单位、说明 |
| `on_surface_muted` | `#9E9E9E` | `#666666` | 占位符、禁用文字；`*.qss:46` |
| `on_primary` | `#FFFFFF` | `#000000` | primary 之上的文字；`*.qss:28` |
| `border` | `#E0E0E0` | `#333333` | 控件边框；`light.qss:112` / `dark.qss:96` |
| `divider` | `#EEEEEE` | `#2C2C2C` | 分隔线、细分割 |
| `hover_overlay` | `#F5F5F5` | `#2C2C2C` | hover 覆盖底色（纯色，不用 rgba） |
| `selected_bg` | `#E8E0F0` | `#3A2F4A` | 选中行底色；qss 中 dark 用 `rgba(187,134,252,0.24)`，此处给出等效纯色 |
| `error` | `#B00020` | `#CF6679` | 错误状态（扩展角色，qss 快照未使用） |
| `success` | `#2E7D32` | `#66BB6A` | 成功状态（扩展角色） |
| `warning` | `#ED6C02` | `#FFA726` | 警告状态（扩展角色） |

`error` / `success` / `warning` 是 `StatusCard` 等状态控件需要的扩展角色，两份 qss 快照
未写入对应规则；若项目用到，在 qss 中补 `[status="error"]` 之类的属性选择器规则。

**qss 衍生色**：`themes/*.qss` 里还会出现 `#444444`、`#666666`、`#BDBDBD`、`#E8E0F0`、
`#F5F5F5`、`#252525`、`#424242` 等中间值，它们是 hover / 按下 / 边框的过渡色，属于上表
key 在具体控件上的展开，**不是 `ThemeColor()` 的 key**。HTML 原型不要直接引用这些衍生值，
一律用上表的 key；Qt 侧写组件局部 QSS 时同理。

**文档演示色**：`qss-reference.md` 等语法参考里出现的 `#1976D2`、`#E3F2FD`、`#CCCCCC`、
`#999999` 之类，只用于演示 QSS 属性写法，同样不是项目色板，落地时一律换成
`ThemeManager::ThemeColor(key).name()` 的结果。

## 3. ThemeManager 完整实现（Qt 6，兼容 Qt 5.6+）

### ui/style/theme_manager.h

```cpp
#pragma once
#include <QObject>
#include <QColor>
#include <QHash>
#include <QString>

class ThemeManager : public QObject {
    Q_OBJECT
public:
    enum class Theme { Light, Dark, System };
    Q_ENUM(Theme)

    static ThemeManager* Instance();

    void SetTheme(Theme theme);              // 传 System 表示跟随系统，并持续跟随
    Theme RequestedTheme() const { return requested_theme_; }
    Theme CurrentTheme() const { return current_theme_; }   // 已解析的 Light/Dark

    QColor ThemeColor(const QString& name) const;
    QColor PrimaryColor() const    { return ThemeColor(QStringLiteral("primary")); }
    QColor BackgroundColor() const { return ThemeColor(QStringLiteral("background")); }
    QColor SurfaceColor() const    { return ThemeColor(QStringLiteral("surface")); }

signals:
    void ThemeChanged(Theme theme);

private:
    explicit ThemeManager(QObject* parent = nullptr);
    Q_DISABLE_COPY(ThemeManager)   // Qt 5.6+ 可用；Q_DISABLE_COPY_MOVE 需 Qt 5.13+

    Theme ResolveSystemTheme() const;
    void LoadTheme(Theme theme);
    void ApplyStylesheet();
    QString LoadStylesheetTemplate(Theme theme) const;

    Theme requested_theme_ = Theme::System;
    Theme current_theme_   = Theme::Light;
    QHash<QString, QColor> colors_;
};
```

### ui/style/theme_manager.cpp

```cpp
#include "theme_manager.h"
#include <QApplication>
#include <QFile>
#include <QGuiApplication>
#include <QStyleHints>
#include <QPalette>
#include <QDebug>

namespace {
struct PaletteEntry { const char* key; const char* light; const char* dark; };

// 唯一色板定义 —— 必须与本文件第 2 节表格逐行一致
constexpr PaletteEntry kPalette[] = {
    {"primary",               "#6200EE", "#BB86FC"},
    {"primary_hover",         "#7C4DFF", "#D4A5FF"},
    {"primary_variant",       "#3700B3", "#9B5BCF"},
    {"secondary",             "#03DAC6", "#03DAC6"},
    {"secondary_variant",     "#00A896", "#00A896"},
    {"background",            "#FAFAFA", "#121212"},
    {"surface",               "#FFFFFF", "#1E1E1E"},
    {"surface_variant",       "#F5F5F5", "#2C2C2C"},
    {"on_background",         "#212121", "#FFFFFF"},
    {"on_surface",            "#212121", "#FFFFFF"},
    {"on_surface_secondary",  "#616161", "#AAAAAA"},
    {"on_surface_muted",      "#9E9E9E", "#666666"},
    {"on_primary",            "#FFFFFF", "#000000"},
    {"border",                "#E0E0E0", "#333333"},
    {"divider",               "#EEEEEE", "#2C2C2C"},
    {"hover_overlay",         "#F5F5F5", "#2C2C2C"},
    {"selected_bg",           "#E8E0F0", "#3A2F4A"},
    {"error",                 "#B00020", "#CF6679"},
    {"success",               "#2E7D32", "#66BB6A"},
    {"warning",               "#ED6C02", "#FFA726"},
};
}  // namespace

ThemeManager* ThemeManager::Instance() {
    // 进程级单例、不设 parent：避免 QApplication 析构后 QObject 二次释放
    static ThemeManager* instance = new ThemeManager;
    return instance;
}

ThemeManager::ThemeManager(QObject* parent) : QObject(parent) {
    current_theme_ = ResolveSystemTheme();
    LoadTheme(current_theme_);
    ApplyStylesheet();
#if QT_VERSION >= QT_VERSION_CHECK(6, 5, 0)
    connect(QGuiApplication::styleHints(), &QStyleHints::colorSchemeChanged,
            this, [this] { if (requested_theme_ == Theme::System) SetTheme(Theme::System); });
#endif
}

Theme ThemeManager::ResolveSystemTheme() const {
#if QT_VERSION >= QT_VERSION_CHECK(6, 5, 0)
    return QGuiApplication::styleHints()->colorScheme() == Qt::ColorScheme::Dark
               ? Theme::Dark : Theme::Light;
#else
    const QColor window = QApplication::palette().color(QPalette::Window);
    return window.lightness() < 128 ? Theme::Dark : Theme::Light;
#endif
}

void ThemeManager::LoadTheme(Theme theme) {
    colors_.clear();
    const bool dark = (theme == Theme::Dark);
    for (const auto& entry : kPalette) {
        colors_.insert(QString::fromLatin1(entry.key),
                       QColor(QString::fromLatin1(dark ? entry.dark : entry.light)));
    }
}

QColor ThemeManager::ThemeColor(const QString& name) const {
    auto it = colors_.constFind(name);
    if (it == colors_.constEnd()) {
        qWarning("ThemeManager: unknown color role '%s', falling back to on_background",
                 qPrintable(name));
        return colors_.value(QStringLiteral("on_background"));
    }
    return *it;
}

void ThemeManager::SetTheme(Theme theme) {
    const Theme resolved = (theme == Theme::System) ? ResolveSystemTheme() : theme;
    requested_theme_ = theme;
    if (resolved == current_theme_ && !colors_.isEmpty()) return;
    current_theme_ = resolved;
    LoadTheme(resolved);
    ApplyStylesheet();
    emit ThemeChanged(resolved);
}

QString ThemeManager::LoadStylesheetTemplate(Theme theme) const {
    const QString path = (theme == Theme::Dark)
        ? QStringLiteral(":/themes/modern-dark.qss")
        : QStringLiteral(":/themes/modern-light.qss");
    QFile file(path);
    if (!file.open(QIODevice::ReadOnly | QIODevice::Text)) {
        qWarning("ThemeManager: cannot open stylesheet '%s'", qPrintable(path));
        return {};
    }
    return QString::fromUtf8(file.readAll());
}

void ThemeManager::ApplyStylesheet() {
    QString qss = LoadStylesheetTemplate(current_theme_);
    if (qss.isEmpty()) return;   // 没有 qrc 资源时不覆盖项目已有样式表

    // 模板中用 %key% 占位；静态快照（themes/*.qss）无占位符时原样加载
    for (auto it = colors_.constBegin(); it != colors_.constEnd(); ++it) {
        const QString placeholder = QStringLiteral("%") + it.key() + QStringLiteral("%");
        qss.replace(placeholder, it.value().name());
    }
    qApp->setStyleSheet(qss);
}
```

### 两种加载模式

- **A. 静态快照（最省事）**：把 `themes/modern-light.qss` / `modern-dark.qss` 原样放进 qrc，
  `ApplyStylesheet()` 直接加载。色值来自快照，切换主题靠换文件，适用于不需要运行时改色的项目。
- **B. 动态注入（推荐）**：把 qss 中的色值替换为 `%key%` 占位符，例如
  `QPushButton { background-color: %primary%; color: %on_primary%; }`，
  `ApplyStylesheet()` 会用当前 `colors_` 逐项替换。改色只改 `kPalette` 一张表。

**注意**：`ApplyStylesheet()` 会调用 `qApp->setStyleSheet()` 覆盖全局样式表。若项目自己管理
全局样式，删掉该函数调用，只把 ThemeManager 当作色值查询源，并在 `ThemeChanged` 里自行刷新。

## 4. 与 HTML 原型的对接

生成原型时，从 `kPalette`（或项目自己的色板）逐 key 导出为 CSS 变量。**变量名 = key**，
值必须是当前主题的实际色值。下面以 Light 为例（Dark 值见第 2 节）：

```css
:root {
    --primary: #6200EE;              /* colors_["primary"] */
    --background: #FAFAFA;           /* colors_["background"] */
    --surface: #FFFFFF;              /* colors_["surface"] */
    --surface_variant: #F5F5F5;      /* colors_["surface_variant"] */
    --on_background: #212121;        /* colors_["on_background"] */
    --on_surface_secondary: #616161; /* colors_["on_surface_secondary"] */
    --on_surface_muted: #9E9E9E;     /* colors_["on_surface_muted"] */
    --error: #B00020;                /* colors_["error"] */
    --success: #2E7D32;              /* colors_["success"] */
    --warning: #ED6C02;              /* colors_["warning"] */
    --border: #E0E0E0;               /* colors_["border"] */
    --divider: #EEEEEE;              /* colors_["divider"] */
    --hover_overlay: #F5F5F5;        /* colors_["hover_overlay"] */
    --selected_bg: #E8E0F0;          /* colors_["selected_bg"] */
}
```

转换到 Qt 时 CSS 变量必须替换为 `ThemeManager::ThemeColor("key").name()` 的实际值，
QSS 不支持变量。原型与 Qt 代码的色值一致性由 Step 5.5 / `html-qt-fidelity.md` 第 8 条校验。

## 5. 运行时改色的正确姿势

```cpp
// ✅ 状态变化：只改动态属性，不重建样式表
label->setProperty("status", "error");
label->style()->unpolish(label);
label->style()->polish(label);

// ✅ 主题变化：由 ThemeManager 统一重建一次全局样式表
ThemeManager::Instance()->SetTheme(ThemeManager::Theme::Dark);
```

```cpp
// ❌ 禁止：在循环 / 状态回调里反复 setStyleSheet()，会触发全量样式重算
for (auto* row : rows) {
    row->setStyleSheet(QString("color: %1;").arg(color.name()));
}
```
