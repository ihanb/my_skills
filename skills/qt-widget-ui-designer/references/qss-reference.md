# QSS (Qt StyleSheet) 完整参考

> 本文档为 QSS 语法参考。实际项目中，为获得最佳性能，请优先使用 `#objectName` 选择器，在根容器集中设置样式表，避免类选择器和后代选择器。

## 选择器

### 类型选择器
```css
QPushButton { /* 所有 QPushButton */ }
QLineEdit { /* 所有 QLineEdit */ }
```

### 类选择器
```css
.CustomButton { /* 所有 class 为 CustomButton 的控件 */ }
```

### ID 选择器
```css
QPushButton#okButton { /* ID 为 okButton 的按钮 */ }
```

### 属性选择器
```css
QPushButton[flat="true"] { /* flat 属性为 true 的按钮 */ }
QCheckBox:checked { /* 选中的复选框 */ }
```

### 后代选择器
```css
QDialog QPushButton { /* QDialog 内的所有按钮 */ }
```

### 子选择器
```css
QDialog > QPushButton { /* QDialog 的直接子按钮 */ }
```

## 通用属性

### 颜色和背景
```css
/* 背景色 */
background-color: #RRGGBB;
background-color: #RRGGBBAA;  /* 带透明度 */
background-color: rgb(255, 0, 0);
background-color: rgba(255, 0, 0, 128);
background-color: transparent;

/* 前景色（文字颜色） */
color: #FFFFFF;

/* 渐变背景 */
background: qlineargradient(
    x1: 0, y1: 0, x2: 0, y2: 1,
    stop: 0 #5c5c5c,
    stop: 1 #333333
);

background: qradialgradient(
    cx: 0.5, cy: 0.5, radius: 0.5,
    fx: 0.5, fy: 0.5,
    stop: 0 #FFFFFF,
    stop: 1 #000000
);
```

### 边框
```css
/* 边框样式 */
border: 2px solid #FFFFFF;
border: 1px dashed #CCCCCC;
border: none;

/* 分别设置 */
border-width: 1px 2px 3px 4px;  /* 上 右 下 左 */
border-style: solid;
border-color: #FFFFFF;

/* 圆角 */
border-radius: 4px;
border-radius: 4px 8px;  /* 水平 垂直 */
border-top-left-radius: 4px;
```

### 尺寸和间距
```css
/* 内边距 */
padding: 10px;
padding: 5px 10px;  /* 垂直 水平 */
padding-top: 5px;
padding-right: 10px;
padding-bottom: 5px;
padding-left: 10px;

/* 外边距 */
margin: 10px;
margin-top: 5px;

/* 最小/最大尺寸 */
min-width: 100px;
max-width: 500px;
min-height: 30px;
max-height: 600px;
```

### 字体
```css
font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
font-size: 12pt;
font-weight: bold;  /* normal, bold, 100-900 */
font-style: italic;  /* normal, italic, oblique */
```

## 控件特定样式

### QPushButton
```css
QPushButton {
    background-color: #6200EE;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #7C4DFF;
}

QPushButton:pressed {
    background-color: #3700B3;
}

QPushButton:disabled {
    background-color: #E0E0E0;
    color: #9E9E9E;
}

QPushButton:checked {
    background-color: #03DAC6;
}

/* 默认按钮 */
QPushButton:default {
    border: 2px solid #FFFFFF;
}

/* 扁平按钮 */
QPushButton:flat {
    background-color: transparent;
    border: none;
}

QPushButton:flat:hover {
    background-color: rgba(255, 255, 255, 0.1);
}
```

### QLineEdit / QTextEdit / QPlainTextEdit
```css
QLineEdit {
    background-color: #FFFFFF;
    color: #000000;
    border: 1px solid #CCCCCC;
    border-radius: 4px;
    padding: 6px 10px;
    selection-background-color: #BB86FC;
    selection-color: #000000;
}

QLineEdit:focus {
    border: 2px solid #6200EE;
}

QLineEdit:disabled {
    background-color: #F5F5F5;
    color: #9E9E9E;
}

/* 只读状态 */
QLineEdit:read-only {
    background-color: #F5F5F5;
}

/* 错误状态 */
QLineEdit[state="error"] {
    border: 2px solid #B00020;
}
```

### QComboBox
```css
QComboBox {
    background-color: #FFFFFF;
    color: #000000;
    border: 1px solid #CCCCCC;
    border-radius: 4px;
    padding: 6px 10px;
    min-width: 100px;
}

QComboBox:hover {
    border-color: #999999;
}

QComboBox:focus {
    border: 2px solid #6200EE;
}

/* 下拉按钮 */
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 30px;
    border-left: 1px solid #CCCCCC;
}

/* 下拉箭头 */
QComboBox::down-arrow {
    image: url(:/icons/down-arrow.png);
    width: 12px;
    height: 12px;
}

/* 下拉列表 */
QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    color: #000000;
    border: 1px solid #CCCCCC;
    selection-background-color: #E3F2FD;
    selection-color: #1976D2;
    outline: none;
}

QComboBox QAbstractItemView::item {
    padding: 8px 12px;
    min-height: 24px;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #F5F5F5;
}

QComboBox QAbstractItemView::item:selected {
    background-color: #E3F2FD;
}
```

### QCheckBox / QRadioButton
```css
QCheckBox {
    color: #000000;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #757575;
    border-radius: 2px;
    background-color: transparent;
}

QCheckBox::indicator:checked {
    background-color: #6200EE;
    border-color: #6200EE;
    image: url(:/icons/check-white.png);
}

QCheckBox::indicator:unchecked:hover {
    border-color: #6200EE;
}

QCheckBox::indicator:disabled {
    border-color: #BDBDBD;
}

QCheckBox::indicator:checked:disabled {
    background-color: #E0E0E0;
    border-color: #E0E0E0;
}

/* 三态复选框 */
QCheckBox::indicator:indeterminate {
    background-color: #6200EE;
    border-color: #6200EE;
    image: url(:/icons/indeterminate-white.png);
}

/* 单选按钮 */
QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #757575;
    border-radius: 9px;
    background-color: transparent;
}

QRadioButton::indicator:checked {
    background-color: #6200EE;
    border-color: #6200EE;
}
```

### QSlider
```css
QSlider::groove:horizontal {
    height: 4px;
    background: #E0E0E0;
    border-radius: 2px;
}

QSlider::sub-page:horizontal {
    background: #6200EE;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    width: 16px;
    height: 16px;
    margin: -6px 0;
    background: #6200EE;
    border: 2px solid #FFFFFF;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background: #7C4DFF;
    width: 20px;
    height: 20px;
    margin: -8px 0;
}

QSlider::handle:horizontal:pressed {
    background: #3700B3;
}
```

### QProgressBar
```css
QProgressBar {
    background-color: #E0E0E0;
    border-radius: 4px;
    text-align: center;
    color: #000000;
    height: 8px;
}

QProgressBar::chunk {
    background-color: #6200EE;
    border-radius: 4px;
}

/* 不确定状态 */
QProgressBar:indeterminate {
    background-color: #E0E0E0;
}

QProgressBar:indeterminate::chunk {
    background-color: #6200EE;
    width: 20px;
    margin-right: 2px;
}
```

### QScrollBar
```css
QScrollBar:vertical {
    background-color: transparent;
    width: 12px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #9E9E9E;
    border-radius: 6px;
    min-height: 30px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #757575;
}

QScrollBar::handle:vertical:pressed {
    background-color: #616161;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background-color: transparent;
}

/* 水平滚动条 */
QScrollBar:horizontal {
    background-color: transparent;
    height: 12px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background-color: #9E9E9E;
    border-radius: 6px;
    min-width: 30px;
    margin: 2px;
}
```

### QTabWidget / QTabBar
```css
QTabWidget::pane {
    border: 1px solid #E0E0E0;
    background-color: #FFFFFF;
    border-radius: 0 4px 4px 4px;
}

QTabBar::tab {
    background-color: #F5F5F5;
    color: #757575;
    padding: 10px 20px;
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: 2px;
}

QTabBar::tab:hover {
    background-color: #EEEEEE;
    color: #424242;
}

QTabBar::tab:selected {
    background-color: #FFFFFF;
    color: #6200EE;
    border-bottom: 2px solid #6200EE;
}

QTabBar::tab:!selected {
    margin-top: 2px;
}

/* 关闭按钮 */
QTabBar::close-button {
    image: url(:/icons/close.png);
    subcontrol-position: right;
}

QTabBar::close-button:hover {
    image: url(:/icons/close-hover.png);
}
```

### QTableWidget / QTableView
```css
QTableWidget, QTableView {
    background-color: #FFFFFF;
    color: #000000;
    gridline-color: #E0E0E0;
    border: none;
    selection-background-color: #E3F2FD;
    selection-color: #1976D2;
    alternate-background-color: #FAFAFA;
}

QTableWidget::item, QTableView::item {
    padding: 8px;
    border: none;
}

QTableWidget::item:selected, QTableView::item:selected {
    background-color: #E3F2FD;
    color: #1976D2;
}

QTableWidget::item:hover, QTableView::item:hover {
    background-color: #F5F5F5;
}

/* 表头 */
QHeaderView::section {
    background-color: #FAFAFA;
    color: #424242;
    padding: 10px;
    border: none;
    border-bottom: 2px solid #E0E0E0;
    font-weight: bold;
}

QHeaderView::section:hover {
    background-color: #EEEEEE;
}

QHeaderView::section:pressed {
    background-color: #E0E0E0;
}

/* 角落按钮 */
QTableCornerButton::section {
    background-color: #FAFAFA;
    border: none;
}
```

### QGroupBox
```css
QGroupBox {
    color: #424242;
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 8px;
    color: #6200EE;
}
```

### QMenu / QMenuBar
```css
QMenuBar {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E0E0E0;
}

QMenuBar::item {
    background-color: transparent;
    padding: 8px 16px;
    color: #424242;
}

QMenuBar::item:selected {
    background-color: #E3F2FD;
    color: #1976D2;
}

QMenu {
    background-color: #FFFFFF;
    border: 1px solid #E0E0E0;
    padding: 8px 0;
}

QMenu::item {
    padding: 8px 24px;
    color: #424242;
}

QMenu::item:selected {
    background-color: #E3F2FD;
    color: #1976D2;
}

QMenu::item:disabled {
    color: #BDBDBD;
}

QMenu::separator {
    height: 1px;
    background-color: #E0E0E0;
    margin: 8px 16px;
}

QMenu::icon {
    padding-left: 12px;
}

QMenu::indicator {
    width: 18px;
    height: 18px;
    padding-left: 8px;
}
```

### QToolBar
```css
QToolBar {
    background-color: #FAFAFA;
    border: none;
    padding: 4px;
    spacing: 4px;
}

QToolBar::separator {
    width: 1px;
    background-color: #E0E0E0;
    margin: 4px 8px;
}

QToolBar::handle {
    image: url(:/icons/toolbar-handle.png);
    width: 12px;
}

QToolButton {
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 6px;
}

QToolButton:hover {
    background-color: #E0E0E0;
}

QToolButton:pressed {
    background-color: #BDBDBD;
}

QToolButton:checked {
    background-color: #E3F2FD;
}
```

### QDockWidget
```css
QDockWidget {
    titlebar-close-icon: url(:/icons/close.png);
    titlebar-normal-icon: url(:/icons/float.png);
}

QDockWidget::title {
    background-color: #FAFAFA;
    padding: 8px;
    border-bottom: 1px solid #E0E0E0;
}

QDockWidget::close-button, QDockWidget::float-button {
    background-color: transparent;
    border-radius: 2px;
    padding: 2px;
}

QDockWidget::close-button:hover, QDockWidget::float-button:hover {
    background-color: #E0E0E0;
}
```

## 伪状态参考

| 状态 | 说明 |
|------|------|
| `:disabled` | 禁用状态 |
| `:enabled` | 启用状态 |
| `:focus` | 获得焦点 |
| `:hover` | 鼠标悬停 |
| `:pressed` | 鼠标按下 |
| `:checked` | 选中状态 |
| `:unchecked` | 未选中 |
| `:indeterminate` | 不确定状态 |
| `:open` | 展开状态 |
| `:closed` | 折叠状态 |
| `:on` | 开启状态 |
| `:off` | 关闭状态 |
| `:selected` | 选中 |
| `:default` | 默认按钮 |
| `:flat` | 扁平样式 |
| `:read-only` | 只读 |
| `:editable` | 可编辑 |
| `:active` | 活动窗口 |
| `:window` | 顶层窗口 |
| `:modal` | 模态对话框 |
| `:has-children` | 有子项 |
| `:has-siblings` | 有兄弟项 |
| `:top` | 顶部 |
| `:bottom` | 底部 |
| `:left` | 左侧 |
| `:right` | 右侧 |
| `:first` | 第一个 |
| `:last` | 最后一个 |
| `:middle` | 中间 |
| `:only-one` | 唯一 |
| `:previous-selected` | 前一个选中 |
| `:next-selected` | 下一个选中 |

## 子控件参考

| 子控件 | 说明 |
|--------|------|
| `::drop-down` | 下拉按钮 |
| `::down-arrow` | 向下箭头 |
| `::up-arrow` | 向上箭头 |
| `::menu-indicator` | 菜单指示器 |
| `::indicator` | 指示器 |
| `::item` | 列表项 |
| `::text` | 文本 |
| `::icon` | 图标 |
| `::title` | 标题 |
| `::handle` | 滑块手柄 |
| `::groove` | 滑块轨道 |
| `::chunk` | 进度条块 |
| `::branch` | 树形分支 |
| `::section` | 表头单元格 |
| `::tab` | 标签页 |
| `::tab-bar` | 标签栏 |
| `::tab-pane` | 标签面板 |
| `::close-button` | 关闭按钮 |
| `::float-button` | 浮动按钮 |
| `::separator` | 分隔线 |
| `::scroller` | 滚动器 |
