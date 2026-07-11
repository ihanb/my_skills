# HTML → Qt 视觉保真度规则

> 本文档在 `qt-widget-ui-designer` 的 Step 5.5（保真度校验）中使用。代码生成后，对照 HTML 原型逐项检查以下规则，确保 QWidget 实现与原型 1:1 视觉还原。

确保 HTML 原型与 QWidget 实现之间 1:1 视觉还原的关键规则。这些规则基于 CSS 和 QSS 的系统性渲染差异，每条规则都来自实际踩坑经验。

---

## 1. QSS padding 与 layout margins 冲突（最常见问题）

### 问题

当 QWidget 同时设置了 QSS `padding` 和布局 `setContentsMargins()`，两者会**叠加**，导致内边距比 HTML 原型大一倍。

```
CSS:  .card { padding: 12px; }  →  内边距 12px
Qt:   QSS padding: 12px + layout margins(12,12,12,12)  →  内边距 24px !!
```

### 原因

- CSS `padding` 定义内容区域与边框之间的空间，flexbox 子元素在 padding 区域内排列
- QSS `padding` 定义 QSS 内容区域，但 **QLayout 的 margins 是在 QSS padding 之外再添加的间距**
- 两者独立计算，互不覆盖

### 规则

**对于有布局的 QWidget，只使用 `setContentsMargins()` 设置内边距，QSS 中不写 `padding`。**

```cpp
// ✅ 正确：只用 layout margins
auto* layout = new QVBoxLayout(this);
layout->setContentsMargins(12, 10, 12, 10);
// QSS 中不写 padding

// ❌ 错误：双重叠加
auto* layout = new QVBoxLayout(this);
layout->setContentsMargins(12, 10, 12, 10);
setStyleSheet("#card { padding: 10px 12px; }");  // 实际内边距 = 22px/20px
```

### HTML 原型对应写法

```css
/* HTML 中正常写 padding，转换时映射到 layout margins */
.card { padding: 12px 10px; }
/* → layout->setContentsMargins(12, 10, 12, 10) */
```

### 例外

对于**没有布局**的控件（如 QLabel 用作状态徽章、计数标签），QSS `padding` 是安全的：

```cpp
// ✅ QLabel 无布局，QSS padding 正常工作
count_label_->setStyleSheet("padding: 1px 8px; border-radius: 10px;");
```

---

## 2. QSS `:hover` 需要 WA_Hover 属性

### 问题

QSS `:hover` 伪状态在自定义 QWidget/QFrame 子类上不生效，鼠标悬停无任何视觉变化。

### 原因

QWidget 默认不追踪鼠标进入/离开事件（出于性能考虑），QSS `:hover` 依赖 `WA_Hover` 属性来触发样式重算。QPushButton 等内置控件默认启用，但自定义 QFrame/QWidget 子类不启用。

### 规则

**任何使用 QSS `:hover` 的自定义 QWidget/QFrame 子类，必须在构造函数中设置 `setAttribute(Qt::WA_Hover)`。**

```cpp
// ✅ 正确
SimDeviceCard::SimDeviceCard(...) : QFrame(parent) {
    setObjectName("SimDeviceCard");
    setStyleSheet("#SimDeviceCard:hover { border-color: #3b82f6; }");
    setAttribute(Qt::WA_Hover);  // 必须！否则 :hover 不生效
}

// ❌ 错误：缺少 WA_Hover
SimDeviceCard::SimDeviceCard(...) : QFrame(parent) {
    setObjectName("SimDeviceCard");
    setStyleSheet("#SimDeviceCard:hover { border-color: #3b82f6; }");
    // :hover 永远不会触发
}
```

### HTML 原型对应写法

```css
/* HTML 中正常写 :hover，转换时记得加 WA_Hover */
.card:hover { border-color: #3b82f6; }
/* → setAttribute(Qt::WA_Hover) + QSS :hover */
```

---

## 3. QSS 属性选择器 `[prop=value]` 需要 Q_PROPERTY

### 问题

QSS 属性选择器如 `[selected=true]` 不稳定，有时生效有时不生效。

### 原因

QSS 属性选择器依赖 Qt 的属性系统。`setProperty("selected", true)` 可以动态设置属性，但如果没有 `Q_PROPERTY` 声明，QSS 引擎可能无法正确检测属性变化。

### 规则

**如果使用 QSS 属性选择器匹配自定义属性，必须在类声明中用 `Q_PROPERTY` 注册该属性。**

```cpp
// ✅ 正确：声明 Q_PROPERTY
class SimDeviceCard : public QFrame {
    Q_OBJECT
    Q_PROPERTY(bool selected READ isSelected WRITE setSelected)

public:
    bool isSelected() const { return selected_; }
    void setSelected(bool s) {
        selected_ = s;
        style()->unpolish(this);
        style()->polish(this);
    }

private:
    bool selected_ = false;
};

// QSS 可以稳定匹配
// #SimDeviceCard[selected=true] { border-color: #3b82f6; }
```

```cpp
// ❌ 错误：只用 setProperty，没有 Q_PROPERTY
void setSelected(bool s) {
    setProperty("selected", s);       // 属性设置了
    style()->unpolish(this);
    style()->polish(this);
}
// QSS [selected=true] 可能不生效，因为属性未注册
```

---

## 4. QLabel 的 background-color + border-radius 渲染差异

### 问题

HTML 中小元素（状态点、标签、徽章）用 `border-radius` + `background-color` 渲染为圆形/圆角矩形，但 Qt 中 QLabel 的 QSS `border-radius` 在某些情况下不裁剪背景。

### 规则

**对于小尺寸 QLabel（如状态点、徽章），必须同时设置 `setFixedSize()` 确保尺寸精确。**

```cpp
// ✅ 正确：状态圆点
status_dot_ = new QLabel;
status_dot_->setFixedSize(6, 6);  // 精确尺寸
status_dot_->setStyleSheet("background-color: #ef4444; border-radius: 3px;");

// ✅ 正确：计数徽章
count_label_ = new QLabel("3");
count_label_->setStyleSheet(
    "background-color: #3b82f6; color: white; border-radius: 10px;"
    "padding: 1px 8px; font-size: 10px; font-weight: bold;");

// ❌ 错误：缺少 setFixedSize，QLabel 可能被布局拉伸
status_dot_ = new QLabel;
status_dot_->setStyleSheet("background-color: #ef4444; border-radius: 3px;");
// 布局可能给 6x6 的 QLabel 分配更大空间，背景不裁剪
```

### HTML 原型对应写法

```css
/* HTML 中小元素用固定尺寸 */
.status-dot { width: 6px; height: 6px; border-radius: 3px; background-color: #ef4444; }
/* → QLabel + setFixedSize(6,6) + QSS border-radius:3px */
```

---

## 5. QSS 样式继承与覆盖问题

### 问题

在父控件上设置的 QSS 样式会向下继承，子控件单独 `setStyleSheet()` 可能无法覆盖继承的样式，或者覆盖后产生意外效果。

### 规则

**5.1 子控件样式表会完全覆盖父控件对同一属性的设置**

```cpp
// 父控件设置了 color
main_widget->setStyleSheet("#main { color: #e0e4ec; }");

// 子控件单独设置 color 会覆盖，但其他继承属性（如 font-size）丢失
name_label_->setStyleSheet("color: #e0e4ec; font-weight: bold;");
// font-size 不再继承自父控件！需要显式设置
```

**5.2 解决方案：在根容器集中管理所有子控件样式**

```cpp
// ✅ 正确：根容器集中管理
main_widget->setStyleSheet(R"(
    #main { background-color: #22262e; }
    #nameLabel { font-size: 13px; font-weight: bold; color: #e0e4ec; }
    #metaLabel { font-size: 11px; color: #6b7280; }
    #statusDot { background-color: #ef4444; border-radius: 3px; }
)");

// ❌ 错误：每个子控件单独设置，样式继承断裂
name_label_->setStyleSheet("font-size: 13px; font-weight: bold; color: #e0e4ec;");
meta_label_->setStyleSheet("font-size: 11px; color: #6b7280;");
```

**5.3 但对于卡片等独立组件，可以在组件自身设置样式表**

```cpp
// ✅ 正确：卡片作为独立组件，自身管理样式
SimDeviceCard::setupUi() {
    setObjectName("SimDeviceCard");
    setStyleSheet(ThemeManager::Instance()->CardStyle());  // 卡片级样式
    // 子控件样式也集中在此
}
```

---

## 6. setFixedHeight vs setMinimumHeight 的选择

### 问题

HTML 中 `height: 76px` 是建议高度，内容溢出时会自动扩展。Qt 中 `setFixedHeight(76)` 是绝对固定，内容溢出会被截断。

### 规则

| 场景 | 使用 | 原因 |
|------|------|------|
| 卡片、列表项 | `setFixedHeight()` | 固定行高，列表滚动时不会跳动 |
| 输入框、按钮 | `setMinimumHeight()` | 允许布局拉伸 |
| 内容区域 | `setMinimumHeight()` + stretch | 弹性填充 |
| 对话框 | `setMinimumSize()` | 允许用户拉伸窗口 |

```cpp
// ✅ 卡片固定高度
setFixedHeight(76);

// ✅ 输入框最小高度
name_edit_->setMinimumHeight(32);

// ❌ 内容区域固定高度（无法弹性填充）
content_widget_->setFixedHeight(400);
```

---

## 7. QFrame 分隔线 vs CSS `<hr>` / border-bottom

### 问题

HTML 中用 `border-bottom: 1px solid #color` 或 `<hr>` 做分隔线很自然，但 Qt 中实现方式不同。

### 规则

**7.1 用 QFrame 做水平分隔线**

```cpp
auto* separator = new QFrame;
separator->setFrameShape(QFrame::HLine);
separator->setFixedHeight(1);
separator->setStyleSheet("background-color: #3a3f4b; border: none;");
```

**7.2 不要用 QSS `border-bottom` 做分隔线**

```cpp
// ❌ 错误：QSS border-bottom 在 QWidget 上不可靠
header_widget->setStyleSheet("#header { border-bottom: 1px solid #3a3f4b; }");
// QWidget 的 border-bottom 可能被布局覆盖或渲染不正确

// ✅ 正确：用独立的 QFrame 分隔线
auto* separator = new QFrame;
separator->setFrameShape(QFrame::HLine);
separator->setFixedHeight(1);
separator->setStyleSheet("background-color: #3a3f4b; border: none;");
main_layout->addWidget(separator);
```

**7.3 QSS `border-bottom` 只在 QPushButton、QTabBar::tab 等内置控件上可靠**

---

## 8. 颜色值必须与 ThemeManager 完全一致

### 问题

HTML 原型使用了一套颜色，Qt 代码使用 ThemeManager 的另一套颜色，导致视觉不一致。

### 规则

**8.1 HTML 原型必须使用 ThemeManager 的实际色值作为 CSS 变量**

```css
/* ✅ 正确：使用项目 ThemeManager 的深色主题色值 */
:root {
  --primary: #3b82f6;
  --background: #1a1d23;
  --surface: #22262e;
  --surface_variant: #2d323c;
  --on_background: #e0e4ec;
  --on_surface_secondary: #9ca3b0;
  --on_surface_muted: #6b7280;
  --error: #ef4444;
  --success: #22c55e;
  --warning: #eab308;
  --border: #3a3f4b;
  --divider: #2d323c;
  --hover_overlay: #363c48;
  --selected_bg: #2a3040;
}

/* ❌ 错误：使用通用色值，与 ThemeManager 不一致 */
:root {
  --bg: #1e1e1e;      /* ThemeManager 是 #1a1d23 */
  --surface: #2d2d2d;  /* ThemeManager 是 #22262e */
  --text: #ffffff;      /* ThemeManager 是 #e0e4ec */
}
```

**8.2 生成 HTML 原型前，必须先读取 ThemeManager::LoadTheme() 中的色值定义**

---

## 9. QWidget 背景色必须显式设置

### 问题

HTML 中子元素默认透明，父元素的 `background-color` 自然显示。Qt 中 QWidget 默认不绘制背景（透明），如果只设置了父控件背景色，子控件区域可能显示为系统默认色（白色/灰色）。

### 规则

**9.1 每个可见的 QWidget 都必须显式设置背景色**

```cpp
// ✅ 正确：每个容器都设置背景色
auto* main_widget = new QWidget(this);
main_widget->setStyleSheet("background-color: #22262e;");

auto* scroll_content = new QWidget;
scroll_content->setStyleSheet("background-color: #22262e;");

// ❌ 错误：只设父控件，子控件可能显示默认色
auto* main_widget = new QWidget(this);
main_widget->setStyleSheet("background-color: #22262e;");
auto* scroll_content = new QWidget;  // 可能显示为白色！
```

**9.2 QScrollArea 的 viewport 也需要设置背景色**

```cpp
scroll_->setStyleSheet("QScrollArea { background-color: #1a1d23; border: none; }");
// scroll content widget 也要设置
scroll_content->setStyleSheet("background-color: #22262e;");
```

---

## 10. 字体渲染差异

### 问题

同一字体在浏览器和 Qt 中的渲染效果不同，尤其是小字号（10px-12px）。

### 规则

**10.1 Qt 中小字号（≤11px）可能比 HTML 看起来更小更模糊，适当增大 1px**

| HTML 字号 | Qt 建议字号 | 说明 |
|-----------|------------|------|
| 10px | 10px 或 11px | 状态文字、标签，Qt 可能偏小 |
| 11px | 11px 或 12px | 次要信息，Qt 可能偏小 |
| 12px | 12px | 正常文本，基本一致 |
| 13px | 13px | 标题，基本一致 |
| 14px+ | 14px+ | 大字号，差异不大 |

**10.2 Qt 中 `font-weight: bold` 比 CSS 更粗，必要时用 `font-weight: 600` 代替**

QSS 不支持 `font-weight: 600`，但可以通过 `QFont::setWeight(QFont::DemiBold)` 在代码中设置。

---

## 11. 复合控件子组件样式必须全面映射

### 问题

HTML 原型中复合控件（筛选栏、消息气泡、卡片等）的子元素样式在 Qt 代码中被遗漏，只映射了外层容器，导致子组件显示为系统默认样式（白色背景、黑色文字、默认边框等），与原型严重不一致。

### 规则

**11.1 每个视觉元素必须有对应的 Qt 控件 + objectName + QSS 规则**

```cpp
// ❌ 错误：只映射了外层，子组件无样式
filter_bar_ = new QWidget;
filter_bar_->setObjectName("MessageFilterBar");
filter_bar_->setStyleSheet("#MessageFilterBar { background-color: #22262e; }");
// 内部的 QComboBox、QLineEdit、QPushButton 都是系统默认样式！

// ✅ 正确：每个子组件都设置 objectName 和 QSS
filter_bar_ = new QWidget;
filter_bar_->setObjectName("MessageFilterBar");
filter_bar_->setStyleSheet(R"(
    #MessageFilterBar { background-color: #22262e; }
    #SourceCombo { background-color: #2d323c; color: #e0e4ec; border: 1px solid #3a3f4b;
                   border-radius: 4px; padding: 4px 8px; min-width: 80px; }
    #SourceCombo::drop-down { border: none; width: 20px; }
    #SearchInput { background-color: #2d323c; color: #e0e4ec; border: 1px solid #3a3f4b;
                   border-radius: 4px; padding: 4px 8px; }
    #ClearBtn { background-color: transparent; color: #9ca3b0; border: none;
                padding: 4px 8px; }
    #ClearBtn:hover { color: #e0e4ec; }
)");
```

**11.2 复合控件子组件映射清单**

| 复合控件 | 必须映射的子组件 | 常见遗漏 |
|---------|----------------|---------|
| QComboBox | 下拉框本体、下拉箭头(`::drop-down`)、下拉列表(`QComboBox QAbstractItemView`)、选中项高亮 | 下拉箭头和列表未设样式 |
| QScrollBar | 滑块(`::handle`)、上下箭头(`::add-line`/`::sub-line`)、翻页区域(`::add-page`/`::sub-page`) | 完全未设样式，显示系统默认 |
| QTabWidget | Tab 栏(`QTabBar::tab`)、选中态(`::tab:selected`)、内容区 | Tab 栏未设样式 |
| QSpinBox | 输入框、上下按钮(`::up-button`/`::down-button`)、箭头(`::up-arrow`/`::down-arrow`) | 上下按钮未设样式 |
| 消息气泡 | 来源标签、时间标签、内容文本、气泡背景 | 时间标签颜色/字号未设 |
| 筛选栏 | 所有输入控件、按钮、分隔线 | 按钮和分隔线未设样式 |
| 状态栏 | 文本标签、图标、分隔线 | 分隔线未设样式 |

**11.3 QComboBox 下拉列表必须单独设置**

QComboBox 的下拉弹出列表（`QAbstractItemView`）默认使用系统样式，必须显式设置：

```cpp
// ✅ 正确：下拉列表样式
#SourceCombo QAbstractItemView {
    background-color: #2d323c;
    color: #e0e4ec;
    border: 1px solid #3a3f4b;
    selection-background-color: #3b82f6;
    selection-color: #ffffff;
    outline: none;
}
```

**11.4 QScrollBar 必须显式设置**

深色主题下，未设置样式的滚动条会显示为系统默认的白色/灰色，严重破坏视觉效果：

```cpp
// ✅ 正确：完整的滚动条样式
#MsgScrollArea QScrollBar:vertical {
    background-color: transparent; width: 8px; margin: 0;
}
#MsgScrollArea QScrollBar::handle:vertical {
    background-color: #3a3f4b; border-radius: 4px; min-height: 30px;
}
#MsgScrollArea QScrollBar::handle:vertical:hover { background-color: #4a4f5b; }
#MsgScrollArea QScrollBar::handle:vertical:pressed { background-color: #5a5f6b; }
#MsgScrollArea QScrollBar::add-line:vertical,
#MsgScrollArea QScrollBar::sub-line:vertical { height: 0; }
#MsgScrollArea QScrollBar::add-page:vertical,
#MsgScrollArea QScrollBar::sub-page:vertical { background: none; }
```

---

## 12. QFrame 容器边框与子控件配合

### 问题

QFrame 容器设置了 `border` 和 `border-radius`，但子控件贴边放置覆盖了边框线，或子控件的直角覆盖了外层圆角。

### 规则

**12.1 有 border 的容器，布局 margins 必须留出边框空间**

```cpp
// ✅ 正确：1px 边框 + 1px margins
auto* layout = new QVBoxLayout(this);
layout->setContentsMargins(1, 1, 1, 1);  // 为 1px border 留空间
setStyleSheet("#widget { border: 1px solid #4a4f5b; border-radius: 6px; }");

// ❌ 错误：子控件贴边覆盖边框
layout->setContentsMargins(0, 0, 0, 0);
```

**12.2 圆角容器的首尾子控件必须配合圆角**

```cpp
// ✅ 正确：顶部子控件配合顶部圆角，底部子控件配合底部圆角
#Container { border-radius: 6px; }
#TopChild { border-top-left-radius: 6px; border-top-right-radius: 6px; }
#BottomChild { border-bottom-left-radius: 6px; border-bottom-right-radius: 6px; }

// ❌ 错误：子控件直角覆盖外层圆角
#TopChild { border-radius: 0; }  // 直角会超出圆角区域
```

**12.3 边框四边颜色必须一致**

Qt 中不同边框颜色渲染不一致，四边必须使用相同颜色：

```cpp
// ✅ 正确
#widget { border: 1px solid #4a4f5b; border-radius: 6px; }

// ❌ 错误：四边不同色，Qt 渲染不一致
#widget { border-top: 1px solid #5a5f6b; border-left: 1px solid #4a4f5b;
          border-right: 1px solid #3a3f4b; border-bottom: 1px solid #2a2e36; }
```

---

## 快速对照表：HTML → Qt 保真度检查

| HTML 效果 | Qt 实现方式 | 常见错误 |
|-----------|------------|---------|
| `padding: 12px` | `layout->setContentsMargins(12,12,12,12)` | QSS padding + layout margins 双重叠加 |
| `:hover` 变色 | `setAttribute(Qt::WA_Hover)` + QSS `:hover` | 忘记 WA_Hover |
| `[selected=true]` 匹配 | `Q_PROPERTY(bool selected ...)` + `setProperty` | 没有 Q_PROPERTY 声明 |
| 小圆点/徽章 | `QLabel` + `setFixedSize()` + QSS | 缺少 setFixedSize |
| `border-bottom` 分隔线 | 独立 `QFrame(HLine)` | 用 QSS border-bottom 不可靠 |
| `background-color` | 每个 QWidget 显式设置 | 只设父控件，子控件透明 |
| `height: 76px` | `setFixedHeight(76)` | 用 setMinimumHeight 导致高度不固定 |
| 颜色值 | ThemeManager 色值 | HTML 和 Qt 用不同色值 |
| `gap: 8px` | `layout->setSpacing(8)` | 正确映射，无问题 |
| `flex: 1` | `addWidget(widget, 1)` stretch | 正确映射，无问题 |
| 复合控件子元素 | 每个子组件 objectName + QSS | 只映射外层容器，子组件遗漏 |
| QComboBox 下拉列表 | `QAbstractItemView` QSS | 下拉列表未设样式，显示系统默认 |
| QScrollBar | `::handle`/`::add-line`/`::sub-line` QSS | 完全未设样式，深色主题下显示白色 |
| 容器 border | `setContentsMargins(1,1,1,1)` + QSS border | 子控件贴边覆盖边框 |
| 圆角容器子控件 | 子控件配合 `border-top-left-radius` 等 | 子控件直角覆盖外层圆角 |
