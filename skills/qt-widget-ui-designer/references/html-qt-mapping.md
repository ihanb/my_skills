# HTML → Qt 映射规范

AI 从 HTML 视觉原型提取布局结构，转换为 QWidget C++ 代码时的映射规则。核心原则：**在还原视觉样式的同时，兼顾 QWidget 的最佳开发实践和运行性能。**

## 1. 布局映射

### Flexbox → QBoxLayout

| HTML/CSS | Qt 布局 | 转换规则 |
|----------|---------|---------|
| `display: flex; flex-direction: column` | QVBoxLayout | 垂直排列子控件 |
| `display: flex; flex-direction: row` | QHBoxLayout | 水平排列子控件 |
| `flex-direction: column-reverse` | QVBoxLayout | 子控件顺序反转 |
| `flex-direction: row-reverse` | QHBoxLayout | 子控件顺序反转 |

### Flex 属性 → Stretch/SizePolicy

| CSS Flex | Qt 属性 | 转换规则 |
|----------|---------|---------|
| `flex: 1` | `stretch=1` | `layout->addWidget(widget, 1)` |
| `flex: 2` | `stretch=2` | `layout->addWidget(widget, 2)` |
| `flex: 0` 或未设置 | `stretch=0` | `layout->addWidget(widget, 0)` |
| `flex-grow: 1` | `setSizePolicy(Expanding, ...)` | 水平扩展 |
| `align-self: stretch` | `setSizePolicy(Expanding, Expanding)` | 双向扩展 |
| `flex-shrink: 0` | `setMinimumWidth/setMinimumHeight` | 不缩小 |

### Grid → QGridLayout

| HTML/CSS | Qt 布局 | 转换规则 |
|----------|---------|---------|
| `display: grid` | QGridLayout | 二维网格 |
| `grid-template-columns: 1fr 2fr` | 列 stretch 1:2 | `layout->setColumnStretch(0, 1); layout->setColumnStretch(1, 2)` |
| `grid-column: span 2` | `columnSpan=2` | `layout->addWidget(widget, row, col, 1, 2)` |
| `grid-row: span 2` | `rowSpan=2` | `layout->addWidget(widget, row, col, 2, 1)` |
| `gap: 8px` | `setSpacing(8)` | 间距 |

### Form → QFormLayout

| HTML | Qt 布局 | 转换规则 |
|------|---------|---------|
| `<form>` | QFormLayout | 表单布局 |
| `<label> + <input>` 对 | `addRow(label, input)` | 标签-输入行 |

## 2. 间距映射

| CSS | Qt | 转换规则 |
|-----|-----|---------|
| `gap: 8px` | `layout->setSpacing(8)` | 布局内控件间距 |
| `padding: 12px` | `layout->setContentsMargins(12,12,12,12)` | 布局内边距 |
| `padding: 8px 12px` | `setContentsMargins(12,8,12,8)` | 上下8 左右12 |
| `margin: 16px` | 外层 addSpacing(16) 或 QGroupBox margins | 分组间距 |
| `justify-content: space-between` | `addStretch()` 在控件之间 | 弹性空间 |

## 3. 控件映射

### 语义化标签 → Qt 控件

| HTML 标签 | Qt 控件 | 说明 |
|-----------|---------|------|
| `<input type="text">` | QLineEdit | 单行文本输入 |
| `<input type="password">` | QLineEdit | `setEchoMode(QLineEdit::Password)` |
| `<input type="number">` | QSpinBox | 数值输入 |
| `<input type="range">` | QSlider | 滑块 |
| `<input type="checkbox">` | QCheckBox | 复选框 |
| `<input type="radio">` | QRadioButton | 单选按钮 |
| `<input type="file">` | QLineEdit + QPushButton | 文件选择（自定义组合） |
| `<textarea>` | QTextEdit | 多行文本 |
| `<select>` | QComboBox | 下拉选择 |
| `<button>` | QPushButton | 按钮 |
| `<label>` | QLabel | 标签 |
| `<h1>-<h6>` | QLabel | 标题（设置字号和粗体） |
| `<p>` | QLabel | 段落文本 |
| `<img>` | QLabel | `setPixmap()` 显示图片 |
| `<table>` | QTableWidget | 表格 |
| `<ul>/<ol>` | QListWidget | 列表 |
| `<progress>` | QProgressBar | 进度条 |
| `<hr>` | QFrame | `setFrameShape(QFrame::HLine)` 水平线 |

### 容器标签 → Qt 容器

| HTML 标签 | Qt 控件 | 说明 |
|-----------|---------|------|
| `<div class="card">` | QGroupBox | 分组框 |
| `<fieldset>` | QGroupBox | 字段集 |
| `<details>` | QGroupBox(checkable) | 可折叠区域 |
| `<dialog>` | QDialog | 对话框 |
| `<nav>` | QWidget (侧边栏) | 导航区域 |
| `<main>` | QWidget (内容区) | 主内容区域 |
| `<header>` | QWidget (顶部区域) | 头部区域 |
| `<footer>` | QWidget (底部区域) | 底部区域 |
| `<aside>` | QDockWidget | 侧边面板 |

## 4. 特殊控件标注

HTML 中没有自然对应的 Qt 控件，用 HTML 注释标注：

| 注释 | Qt 控件 | 用法示例 |
|------|---------|---------|
| `<!-- dock: left -->` | QDockWidget | `<aside><!-- dock: left -->导航</aside>` |
| `<!-- splitter -->` | QSplitter | `<div class="split"><!-- splitter -->...</div>` |
| `<!-- tab-container -->` | QTabWidget | `<div><!-- tab-container --><section>Tab1</section><section>Tab2</section></div>` |
| `<!-- stacked: page1, page2 -->` | QStackedWidget | `<div><!-- stacked: page1, page2 -->...</div>` |
| `<!-- toolbar -->` | QToolBar | `<header><!-- toolbar -->...</header>` |
| `<!-- statusbar -->` | QStatusBar | `<footer><!-- statusbar -->...</footer>` |
| `<!-- menubar -->` | QMenuBar | `<nav><!-- menubar -->...</nav>` |

## 5. 转换流程

### Step 1: 解析 HTML 结构树

```
HTML 元素树 → 布局嵌套关系
  - 识别 display:flex/grid → 布局类型
  - 识别 flex 值 → stretch factor
  - 识别 gap/padding/margin → 间距参数
  - 识别语义标签 → Qt 控件类型
  - 识别注释标注 → Qt 特殊控件
```

### Step 2: 生成 Qt 布局代码

按以下顺序生成：
1. 创建布局对象
2. 设置布局参数（spacing, margins）
3. 创建控件对象
4. 设置控件属性（minimumSize, sizePolicy）
5. 将控件添加到布局（带 stretch factor）
6. 处理特殊控件（QSplitter, QDockWidget 等）

### Step 3: 处理无法直接映射的情况

| 情况 | 处理方式 |
|------|---------|
| HTML 中无对应 Qt 控件 | 查看注释标注，使用对应 Qt 控件 |
| CSS 效果无法用布局实现 | 忽略视觉效果，保留布局结构，样式在 Step 7 中优化 |
| HTML 交互（JS） | 不转换，在 C++ 中用信号槽实现 |
| CSS 动画/过渡 | 不转换，用 QPropertyAnimation 实现 |

---

## 6. 样式映射（CSS → QSS）

HTML 原型中的 CSS 样式需要转换为 QSS，但必须注意两者差异和性能影响。

### 可直接映射的 CSS 属性

| CSS 属性 | QSS 属性 | 示例 |
|----------|---------|------|
| `background-color: #hex` | `background-color: #hex` | 直接映射 |
| `color: #hex` | `color: #hex` | 直接映射 |
| `border: 1px solid #hex` | `border: 1px solid #hex` | 直接映射 |
| `border-radius: 4px` | `border-radius: 4px` | 直接映射 |
| `padding: 8px` | `padding: 8px` | 直接映射 |
| `font-size: 14px` | `font-size: 14px` | 直接映射 |
| `font-weight: bold` | `font-weight: bold` | 直接映射 |

### 不可映射的 CSS 属性（必须替换方案）

| CSS 属性 | QSS 替代方案 | 性能说明 |
|----------|-------------|---------|
| `box-shadow` | 用 `border: 1px solid #darker_color` 模拟 | QSS 不支持阴影，用边框颜色差异模拟层次 |
| `text-shadow` | 无替代，去掉 | QSS 不支持文字阴影 |
| `linear-gradient` | 用纯色 `background-color` 替代 | QSS 渐变语法不同且性能差，纯色是最佳选择 |
| `:hover` 效果 | QSS `:hover` 伪类 | 可映射但需注意：QSS hover 会触发全局样式重算 |
| `opacity` | 用 `color: #lighter_hex` 模拟 | QSS 不支持 opacity，用更浅的颜色模拟 |
| `backdrop-filter: blur` | 无替代，去掉 | QSS 完全不支持 |

### QSS 性能优化规则

1. **选择器优先级**：
   ```cpp
   // ✅ 高性能：ID 选择器，直接匹配
   "#myButton { background-color: #3b82f6; }"

   // ❌ 低性能：类选择器，遍历所有控件
   "QPushButton { background-color: #3b82f6; }"

   // ❌ 最低性能：后代选择器，级联遍历
   "QWidget QPushButton { background-color: #3b82f6; }"
   ```

2. **样式表设置位置**：
   ```cpp
   // ✅ 高性能：在根容器设置，利用 CSS 继承
   this->setStyleSheet(
       "#cardLabel { color: #9ca3b0; font-size: 12px; }"
       "#cardValue { color: #ffffff; font-size: 20px; font-weight: bold; }"
   );

   // ❌ 低性能：每个子控件单独设置
   label1->setStyleSheet("color: #9ca3b0; font-size: 12px;");
   label2->setStyleSheet("color: #ffffff; font-size: 20px; font-weight: bold;");
   ```

3. **避免频繁 setStyleSheet**：
   ```cpp
   // ✅ 正确：只在 SetupUi() 中设置一次
   void SetupUi() {
       setStyleSheet("...");
   }

   // ❌ 错误：在运行时频繁调用
   void UpdateStatus(bool running) {
       label->setStyleSheet(running ?
           "color: #22c55e;" : "color: #ef4444;");  // 每次调用触发样式重算
   }

   // ✅ 正确：用 QSS 类选择器切换
   void UpdateStatus(bool running) {
       label->setProperty("status", running ? "running" : "stopped");
       label->style()->unpolish(label);
       label->style()->polish(label);  // 只刷新这一个控件
   }
   ```

---

## 7. 控件选择映射（性能导向）

HTML 原型中的元素需要选择最合适的 Qt 控件，在功能满足的前提下优先选择轻量级控件。

### 控件重量级对比

| 重量级 | 控件 | 适用场景 | 不适用场景 |
|--------|------|---------|-----------|
| 轻 | QLabel | 只读文本、数值显示 | 需要编辑的文本 |
| 轻 | QLineEdit | 单行文本输入 | 多行文本 |
| 轻 | QSpinBox | 数值输入 | 大范围数值（用 QSlider） |
| 轻 | QComboBox | 下拉选择 | 需要多列选择（用 QTableView 弹出） |
| 轻 | QPushButton | 按钮 | — |
| 轻 | QCheckBox | 复选框 | — |
| 中 | QListWidget | 静态列表 | 大数据量（用 QListView+Model） |
| 中 | QTableWidget | 静态表格 | 大数据量（用 QTableView+Model） |
| 中 | QTreeWidget | 静态树 | 大数据量（用 QTreeView+Model） |
| 重 | QTextEdit | 多行富文本编辑 | 只读文本（用 QLabel） |
| 重 | QWebView | Web 内容 | 任何非 Web 场景 |

### 常见错误选择及修正

| HTML 元素 | ❌ 错误 Qt 控件 | ✅ 正确 Qt 控件 | 原因 |
|-----------|----------------|----------------|------|
| `<p>` 只读文本 | QTextEdit | QLabel | QTextEdit 重量级，QLabel 轻量 |
| `<input type="number">` | QLineEdit + 验证 | QSpinBox | QSpinBox 内置验证和步进 |
| `<select>` 少量选项 | QListView + Model | QComboBox | 少量选项用 QComboBox 更轻量 |
| `<div>` 状态指示 | QFrame + 自绘 | QLabel + QSS | QLabel + QSS 圆角背景即可 |
| `<div>` 卡片容器 | QFrame | QGroupBox / QWidget | QGroupBox 有标题，QWidget 更轻量 |

---

## 8. 内存管理映射

HTML 中元素由浏览器自动管理，Qt 中需要显式管理控件生命周期。

### Parent-Child 机制

```cpp
// ✅ 正确：加入布局的控件自动设置 parent
auto* layout = new QVBoxLayout(this);  // this 是 parent
auto* label = new QLabel("Hello");     // 无需指定 parent
layout->addWidget(label);              // label 的 parent 自动设为 this

// ✅ 正确：手动指定 parent
auto* dialog = new QDialog(this);      // this 是 parent

// ❌ 错误：忘记指定 parent 或加入布局
auto* widget = new QWidget();          // 内存泄漏！没有 parent
```

### 对话框生命周期

```cpp
// ✅ 栈创建：自动销毁
void OnShowDialog() {
    MyDialog dialog(this);
    if (dialog.exec() == QDialog::Accepted) {
        // 处理结果
    }
}  // dialog 自动销毁

// ✅ 堆创建 + 自动删除
void OnShowDialog() {
    auto* dialog = new MyDialog(this);
    dialog->setAttribute(Qt::WA_DeleteOnClose);
    dialog->show();
}  // 关闭时自动删除

// ❌ 错误：堆创建不删除
void OnShowDialog() {
    auto* dialog = new MyDialog(this);
    dialog->show();
    // 没有设置 WA_DeleteOnClose，每次调用都泄漏
}
```

---

## 9. 信号槽映射

HTML 中的事件监听需要转换为 Qt 信号槽，注意避免性能陷阱。

### 事件 → 信号槽映射

| HTML 事件 | Qt 信号 | 说明 |
|-----------|---------|------|
| `onclick` | `clicked()` | 按钮点击 |
| `onchange` | `textChanged()` / `currentIndexChanged()` | 值变化 |
| `oninput` | `textEdited()` | 用户输入（区别于程序设置） |
| `onsubmit` | `accepted()` | 对话框确认 |
| `onfocus` | 无直接映射 | Qt 中较少使用 |

### 信号槽性能注意

```cpp
// ✅ 正确：批量更新时阻塞信号
void UpdateAllFields(const Config& config) {
    blockSignals(true);  // 防止每个 set 都触发信号
    nameEdit_->setText(config.name);
    portSpin_->setValue(config.port);
    intervalSpin_->setValue(config.interval);
    blockSignals(false);
    emit configChanged();  // 只发一次信号
}

// ❌ 错误：每次 set 都触发信号
void UpdateAllFields(const Config& config) {
    nameEdit_->setText(config.name);      // 触发 textChanged
    portSpin_->setValue(config.port);     // 触发 valueChanged
    intervalSpin_->setValue(config.interval);  // 触发 valueChanged
    // 3 次信号 → 3 次处理 → 性能浪费
}

// ✅ 正确：高频更新用 QueuedConnection
connect(dataSource_, &DataSource::dataUpdated,
        this, &Panel::onDataUpdated,
        Qt::QueuedConnection);  // 不阻塞数据源线程
```

---

## 10. 复合控件子组件映射

HTML 原型中的复合 UI 模式（如筛选栏、消息气泡、卡片列表等），其内部每个子元素都必须单独创建 Qt 控件并设置样式。**不能只映射外层容器而忽略内部子组件。**

### 10.1 QComboBox 子组件

| HTML 元素 | Qt 子组件 | 必须设置的 QSS |
|-----------|----------|---------------|
| `<select>` 本体 | QComboBox | `background-color`, `color`, `border`, `border-radius`, `padding` |
| 下拉箭头区域 | `::drop-down` | `border`, `width` |
| 下拉箭头图标 | `::down-arrow` | `image` 或 `border` 三角形 |
| 下拉弹出列表 | `QAbstractItemView` | `background-color`, `color`, `border`, `selection-background-color`, `selection-color`, `outline` |
| 下拉列表项 | `QAbstractItemView::item` | `padding`, `min-height` |
| 选中项 | `QAbstractItemView::item:selected` | `background-color`, `color` |

```cpp
// 完整的 QComboBox 样式映射
"#SourceCombo { background-color: #2d323c; color: #e0e4ec; border: 1px solid #3a3f4b;"
"              border-radius: 4px; padding: 4px 28px 4px 8px; min-width: 80px; }"
"#SourceCombo::drop-down { subcontrol-origin: padding; subcontrol-position: center right;"
"                          width: 20px; border-left: 1px solid #3a3f4b; border: none; }"
"#SourceCombo::down-arrow { width: 8px; height: 8px; }"
"#SourceCombo QAbstractItemView { background-color: #2d323c; color: #e0e4ec;"
"                                 border: 1px solid #3a3f4b; selection-background-color: #3b82f6;"
"                                 selection-color: #ffffff; outline: none; }"
```

### 10.2 QScrollBar 子组件

| HTML 元素 | Qt 子组件 | 必须设置的 QSS |
|-----------|----------|---------------|
| 滚动条轨道 | `QScrollBar:vertical` | `background`, `width`, `margin` |
| 滚动条滑块 | `::handle:vertical` | `background-color`, `border-radius`, `min-height` |
| 滑块悬停 | `::handle:vertical:hover` | `background-color` |
| 滑块按下 | `::handle:vertical:pressed` | `background-color` |
| 上箭头按钮 | `::add-line:vertical` | `height: 0`（隐藏） |
| 下箭头按钮 | `::sub-line:vertical` | `height: 0`（隐藏） |
| 翻页区域 | `::add-page:vertical` / `::sub-page:vertical` | `background: none` |

```cpp
// 完整的 QScrollBar 样式映射
"#ScrollArea QScrollBar:vertical { background-color: transparent; width: 8px; margin: 0; }"
"#ScrollArea QScrollBar::handle:vertical { background-color: #3a3f4b; border-radius: 4px;"
"                                          min-height: 30px; }"
"#ScrollArea QScrollBar::handle:vertical:hover { background-color: #4a4f5b; }"
"#ScrollArea QScrollBar::handle:vertical:pressed { background-color: #5a5f6b; }"
"#ScrollArea QScrollBar::add-line:vertical, #ScrollArea QScrollBar::sub-line:vertical { height: 0; }"
"#ScrollArea QScrollBar::add-page:vertical, #ScrollArea QScrollBar::sub-page:vertical { background: none; }"
```

### 10.3 QTabWidget 子组件

| HTML 元素 | Qt 子组件 | 必须设置的 QSS |
|-----------|----------|---------------|
| Tab 栏 | `QTabWidget::pane` | `border`, `background-color` |
| Tab 按钮 | `QTabBar::tab` | `background-color`, `color`, `border`, `padding`, `min-width` |
| Tab 选中态 | `QTabBar::tab:selected` | `background-color`, `color`, `border` |
| Tab 悬停态 | `QTabBar::tab:hover` | `background-color` |

### 10.4 QSpinBox 子组件

| HTML 元素 | Qt 子组件 | 必须设置的 QSS |
|-----------|----------|---------------|
| 输入框 | QSpinBox 本体 | `background-color`, `color`, `border`, `border-radius`, `padding` |
| 上按钮 | `::up-button` | `subcontrol-origin`, `width`, `border` |
| 下按钮 | `::down-button` | `subcontrol-origin`, `width`, `border` |
| 上箭头 | `::up-arrow` | `width`, `height`, `border`（三角形） |
| 下箭头 | `::down-arrow` | `width`, `height`, `border`（三角形） |

### 10.5 消息气泡子组件

| HTML 元素 | Qt 子组件 | 必须设置的属性 |
|-----------|----------|---------------|
| 气泡容器 | QFrame | `objectName`, QSS `background-color`, `border`, `border-radius`, `padding` |
| 来源标签 | QLabel | `objectName`, QSS `color`, `font-size`, `font-weight` |
| 时间标签 | QLabel | `objectName`, QSS `color`, `font-size` |
| 内容文本 | QLabel | `objectName`, QSS `color`, `font-size`, `font-family`(等宽) |

### 10.6 筛选栏子组件

| HTML 元素 | Qt 子组件 | 必须设置的属性 |
|-----------|----------|---------------|
| 筛选栏容器 | QWidget | `objectName`, QSS `background-color` |
| 来源下拉框 | QComboBox | 见 10.1 完整映射 |
| 时间下拉框 | QComboBox | 见 10.1 完整映射 |
| 搜索输入框 | QLineEdit | `objectName`, QSS `background-color`, `color`, `border`, `border-radius`, `padding` |
| 清除按钮 | QPushButton | `objectName`, QSS `background-color`, `color`, `border`, `padding` |
| 分隔线 | QFrame(HLine) | `objectName`, QSS `background-color`, `border: none`, `setFixedHeight(1)` |

### 10.7 状态栏子组件

| HTML 元素 | Qt 子组件 | 必须设置的属性 |
|-----------|----------|---------------|
| 状态栏容器 | QWidget | `objectName`, QSS `background-color` |
| 消息计数标签 | QLabel | `objectName`, QSS `color`, `font-size` |
| 自动滚动复选框 | QCheckBox | `objectName`, QSS `color`, `spacing` |
| 分隔线 | QFrame(HLine) | `objectName`, QSS `background-color`, `border: none`, `setFixedHeight(1)` |

---

## 11. QSS 陷阱与保真度规则

HTML → Qt 转换中最容易导致视觉差异的系统性陷阱。完整规则详见 `references/html-qt-fidelity.md`。

### 11.1 QSS padding 与 layout margins 冲突

**最常见问题**：有布局的 QWidget 同时设置 QSS `padding` 和 `setContentsMargins()`，两者叠加导致内边距翻倍。

```cpp
// ❌ 错误：双重叠加，实际内边距 = 24px
auto* layout = new QVBoxLayout(this);
layout->setContentsMargins(12, 10, 12, 10);
setStyleSheet("#card { padding: 10px 12px; }");

// ✅ 正确：只用 layout margins
auto* layout = new QVBoxLayout(this);
layout->setContentsMargins(12, 10, 12, 10);
// QSS 中不写 padding
```

**例外**：没有布局的 QLabel（如状态徽章），QSS `padding` 安全可用。

### 11.2 QSS `:hover` 需要 WA_Hover

自定义 QWidget/QFrame 子类使用 QSS `:hover`，必须设置 `setAttribute(Qt::WA_Hover)`：

```cpp
// ❌ 错误：:hover 不生效
setStyleSheet("#card:hover { border-color: #3b82f6; }");

// ✅ 正确
setAttribute(Qt::WA_Hover);
setStyleSheet("#card:hover { border-color: #3b82f6; }");
```

### 11.3 QSS 属性选择器需要 Q_PROPERTY

QSS `[selected=true]` 等属性选择器，必须在类中声明 `Q_PROPERTY`：

```cpp
// ✅ 正确
class SimDeviceCard : public QFrame {
    Q_OBJECT
    Q_PROPERTY(bool selected READ isSelected WRITE setSelected)
    // ...
};
```

### 11.4 QLabel 小元素需要 setFixedSize

状态点、徽章等小尺寸 QLabel，必须用 `setFixedSize()` 确保尺寸精确，否则布局可能拉伸导致背景不裁剪：

```cpp
// ✅ 正确
status_dot_->setFixedSize(6, 6);
status_dot_->setStyleSheet("background-color: #ef4444; border-radius: 3px;");
```

### 11.5 分隔线用 QFrame 不用 QSS border-bottom

```cpp
// ❌ 错误：QSS border-bottom 在 QWidget 上不可靠
header->setStyleSheet("#header { border-bottom: 1px solid #3a3f4b; }");

// ✅ 正确：独立 QFrame
auto* separator = new QFrame;
separator->setFrameShape(QFrame::HLine);
separator->setFixedHeight(1);
separator->setStyleSheet("background-color: #3a3f4b; border: none;");
```

### 11.6 每个 QWidget 显式设置背景色

Qt 中 QWidget 默认不绘制背景（透明），只设父控件背景色不够：

```cpp
// ❌ 错误：子控件可能显示系统默认色
main_widget->setStyleSheet("background-color: #22262e;");
auto* scroll_content = new QWidget;  // 透明！

// ✅ 正确：每个容器都设置
main_widget->setStyleSheet("background-color: #22262e;");
scroll_content->setStyleSheet("background-color: #22262e;");
```

### 11.7 颜色值必须与 ThemeManager 一致

HTML 原型和 Qt 代码必须使用 ThemeManager 的同一套色值，不能各自用不同的颜色。
