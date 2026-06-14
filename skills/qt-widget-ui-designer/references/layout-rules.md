# QWidget 布局规则体系

## 1. 布局选择规则

### 原则：根据内容特征选择布局，不要"万能布局"

| 内容特征 | 推荐布局 | 不推荐 |
|---------|---------|--------|
| 标签-输入对 | QFormLayout | QGridLayout（过度设计） |
| 垂直排列的异构控件 | QVBoxLayout | QGridLayout（列宽不一致） |
| 水平排列的同构控件 | QHBoxLayout | 手动 setGeometry |
| 规整的二维表格 | QGridLayout | 嵌套 QVBoxLayout+QHBoxLayout |
| 侧边栏+内容 | QSplitter | 手动 QHBoxLayout+setStretch |

### QFormLayout 的正确使用

```cpp
// ✅ 正确：QFormLayout 自动处理标签对齐和输入框宽度
auto* formLayout = new QFormLayout();
formLayout->addRow(tr("Name:"), nameEdit_);
formLayout->addRow(tr("Email:"), emailEdit_);
formLayout->addRow(tr("Phone:"), phoneEdit_);

// ❌ 错误：用 QGridLayout 做表单，需要手动管理列宽和对齐
auto* gridLayout = new QGridLayout();
gridLayout->addWidget(new QLabel(tr("Name:")), 0, 0, Qt::AlignRight);
gridLayout->addWidget(nameEdit_, 0, 1);
// ... 每行都要手动设置对齐
```

### QSplitter vs QHBoxLayout

```cpp
// ✅ 正确：QSplitter 允许用户拖拽调整比例
auto* splitter = new QSplitter(Qt::Horizontal);
splitter->addWidget(navTree_);
splitter->addWidget(contentStack_);
splitter->setStretchFactor(0, 0);  // 导航栏不拉伸
splitter->setStretchFactor(1, 1);  // 内容区弹性拉伸
splitter->setSizes({200, 600});    // 初始比例

// ❌ 错误：QHBoxLayout 无法拖拽调整
auto* layout = new QHBoxLayout();
layout->addWidget(navTree_);
layout->addWidget(contentStack_);
layout->setStretch(0, 0);
layout->setStretch(1, 1);
```

## 2. 嵌套深度规则

### 原则：布局嵌套不超过 3 层

```
✅ 合理嵌套（2层）：
QVBoxLayout (主布局)
  ├── QFormLayout (表单区域)
  └── QHBoxLayout (按钮组)

✅ 合理嵌套（3层）：
QVBoxLayout (主布局)
  ├── QFormLayout (表单区域)
  ├── QGroupBox → QVBoxLayout (分组内的垂直列表)
  └── QHBoxLayout (按钮组)

❌ 过深嵌套（4层+）：
QVBoxLayout (主布局)
  ├── QHBoxLayout (水平分割)
  │   ├── QVBoxLayout (左侧)
  │   │   ├── QFormLayout (表单)
  │   │   └── QHBoxLayout (内部按钮)  ← 第4层，应拆分
  │   └── QVBoxLayout (右侧)
  └── QHBoxLayout (底部按钮)
```

### 拆分方法：提取自定义 Widget

```cpp
// 当嵌套超过 3 层时，将内部结构提取为独立 Widget

// 提取前：4层嵌套
// mainLayout → hLayout → leftLayout → formLayout

// 提取后：2层嵌套
class UserFormPanel : public QWidget {  // 封装 leftLayout + formLayout
    // ...
};

// mainLayout → hLayout → userFormPanel (1个Widget，内部自行管理)
auto* mainLayout = new QVBoxLayout(this);
auto* hLayout = new QHBoxLayout();
hLayout->addWidget(new UserFormPanel());  // 内部嵌套对外不可见
hLayout->addWidget(detailPanel_);
mainLayout->addLayout(hLayout);
```

## 3. 间距规范

### 标准间距值

| 场景 | 值 | 设置方式 |
|------|-----|---------|
| 同组控件间 | 8px | `layout->setSpacing(8)` |
| 不同分组间 | 16px | 在分组间 `addSpacing(16)` 或 `addStretch()` |
| 窗口内边距 | 12px | `layout->setContentsMargins(12,12,12,12)` |
| 对话框内边距 | 12px | 同上 |
| 分组框内边距 | 8px | QGroupBox 内部布局的 contentsMargins |
| 按钮间间距 | 8px | 按钮所在 QHBoxLayout 的 spacing |

### 间距设置示例

```cpp
void SettingsDialog::setupUi() {
    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(12, 12, 12, 12);
    mainLayout->setSpacing(16);  // 分组间用 16px

    // 表单分组
    auto* formGroup = new QGroupBox(tr("General"));
    auto* formLayout = new QFormLayout(formGroup);
    formLayout->setSpacing(8);  // 同组控件间 8px
    formLayout->setContentsMargins(8, 8, 8, 8);
    formLayout->addRow(tr("Language:"), languageCombo_);
    formLayout->addRow(tr("Theme:"), themeCombo_);
    mainLayout->addWidget(formGroup);

    // 按钮组
    auto* buttonLayout = new QHBoxLayout();
    buttonLayout->setSpacing(8);
    buttonLayout->addStretch();
    buttonLayout->addWidget(okButton_);
    buttonLayout->addWidget(cancelButton_);
    mainLayout->addLayout(buttonLayout);
}
```

## 4. 拉伸策略

### 原则：每个布局都必须有明确的 stretch 分配

```cpp
// ✅ 正确：弹性区域 stretch=1，固定区域 stretch=0
auto* layout = new QHBoxLayout();
layout->addWidget(sidebar_, 0);      // 侧边栏固定宽度
layout->addWidget(content_, 1);      // 内容区弹性拉伸

// ✅ 正确：多弹性区域按比例分配
auto* layout = new QHBoxLayout();
layout->addWidget(leftPanel_, 1);    // 占 1/3
layout->addWidget(centerPanel_, 2);  // 占 2/3

// ❌ 错误：没有 stretch，控件可能挤在一起或分布不均
auto* layout = new QHBoxLayout();
layout->addWidget(sidebar_);
layout->addWidget(content_);
```

### 常见 stretch 模式

| 场景 | stretch 分配 |
|------|-------------|
| 侧边栏+内容 | sidebar=0, content=1 |
| 三栏布局 | left=1, center=2, right=1 |
| 工具栏+内容 | toolbar=0, content=1 |
| 表单+按钮 | form=1, buttons=0 |
| 多个等宽面板 | 各 stretch=1 |

## 5. 尺寸约束

### 最小尺寸规范

| 控件类型 | 最小宽度 | 最小高度 | 说明 |
|---------|---------|---------|------|
| QLineEdit | 200px | — | 保证可输入合理长度文本 |
| QTextEdit | 300px | 150px | 保证可编辑多行文本 |
| QComboBox | 150px | — | 保证下拉项可读 |
| QPushButton | 80px | — | 保证按钮文字可见 |
| QListWidget | 150px | 150px | 保证列表可滚动浏览 |
| QTableWidget | 300px | 200px | 保证表格可读 |
| QTreeWidget | 200px | 150px | 保证树形结构可浏览 |
| QTabWidget | 300px | 200px | 保证选项卡内容可读 |

### 设置方式

```cpp
// ✅ 正确：用 minimumSize + stretch，窗口可弹性缩放
nameEdit_->setMinimumWidth(200);
contentLayout->setStretchFactor(nameEdit_, 1);

// ❌ 错误：用固定尺寸，窗口无法弹性缩放
nameEdit_->setFixedWidth(200);

// ❌ 错误：不设最小尺寸，控件可能被压缩到不可用
// nameEdit_ 无任何尺寸约束
```

### SizePolicy 使用

```cpp
// 输入框：水平扩展，垂直固定
nameEdit_->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);

// 按钮：水平和垂直都固定
okButton_->setSizePolicy(QSizePolicy::Fixed, QSizePolicy::Fixed);

// 列表：双向扩展
listWidget_->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Expanding);

// 标签：水平和垂直都固定
label_->setSizePolicy(QSizePolicy::Fixed, QSizePolicy::Fixed);
```

## 6. 对齐规则

### 标签对齐

```cpp
// QFormLayout 自动处理标签对齐
auto* formLayout = new QFormLayout();
formLayout->setLabelAlignment(Qt::AlignRight | Qt::AlignVCenter);
```

### 按钮组对齐

```cpp
// ✅ 右对齐（标准做法）
auto* buttonLayout = new QHBoxLayout();
buttonLayout->addStretch();  // 弹性空间推按钮到右边
buttonLayout->addWidget(okButton_);
buttonLayout->addWidget(cancelButton_);

// ✅ 居中对齐（向导/步骤界面）
auto* buttonLayout = new QHBoxLayout();
buttonLayout->addStretch();
buttonLayout->addWidget(backButton_);
buttonLayout->addWidget(nextButton_);
buttonLayout->addWidget(finishButton_);
buttonLayout->addStretch();
```

### 控件在布局中的对齐

```cpp
// 垂直布局中水平居中
mainLayout->addWidget(titleLabel_, 0, Qt::AlignHCenter);

// 垂直布局中左对齐（默认）
mainLayout->addWidget(helpLabel_, 0, Qt::AlignLeft);
```

## 7. QScrollArea 使用规则

### 原则：内容可能超出可视区域时，必须用 QScrollArea 包裹

```cpp
// ✅ 正确：表单内容可能很长，用 QScrollArea 包裹
auto* scrollArea = new QScrollArea();
scrollArea->setWidgetResizable(true);  // 关键：允许内部 widget 跟随调整大小
scrollArea->setFrameShape(QFrame::NoFrame);  // 去掉默认边框

auto* contentWidget = new QWidget();
auto* formLayout = new QFormLayout(contentWidget);
// ... 添加大量表单项
scrollArea->setWidget(contentWidget);

mainLayout->addWidget(scrollArea);

// ❌ 错误：不用 QScrollArea，窗口缩小时控件被压缩
auto* formLayout = new QFormLayout(this);
// ... 添加大量表单项，窗口缩小时控件挤在一起
```

### QScrollArea 的常见场景

| 场景 | 是否需要 ScrollArea |
|------|-------------------|
| 设置对话框（选项可能很多） | 是 |
| 日志面板 | 是 |
| 简单登录对话框（3-5个控件） | 否 |
| 属性面板（字段数量不确定） | 是 |
| 固定布局的工具栏 | 否 |

---

## 8. 布局性能规则

### 原则：布局是 QWidget 性能的基础，错误的布局选择会导致窗口卡顿

### 8.1 布局激活开销

每次控件显示/隐藏、尺寸变化、内容更新，布局管理器都会重新计算。减少不必要的布局激活：

```cpp
// ✅ 正确：批量操作时暂停布局计算
void RebuildList(const QList<Item>& items) {
    setUpdatesEnabled(false);     // 暂停所有更新
    listWidget_->clear();
    for (const auto& item : items) {
        listWidget_->addItem(item.name);
    }
    setUpdatesEnabled(true);      // 恢复更新，只触发一次布局计算
}

// ❌ 错误：每次操作都触发布局计算
void RebuildList(const QList<Item>& items) {
    listWidget_->clear();         // 触发布局计算
    for (const auto& item : items) {
        listWidget_->addItem(item.name);  // 每次都触发布局计算
    }
}
```

### 8.2 控件显隐性能

```cpp
// ✅ 正确：隐藏不用的控件，减少布局计算
void ShowEditMode(bool editing) {
    editWidget_->setVisible(editing);
    viewWidget_->setVisible(!editing);
    // 布局只计算可见控件
}

// ❌ 错误：用透明度模拟显隐，布局仍计算隐藏控件
void ShowEditMode(bool editing) {
    editWidget_->setStyleSheet(
        editing ? "opacity: 1;" : "opacity: 0;");  // QSS 不支持 opacity！
}
```

### 8.3 QSplitter vs QHBoxLayout 性能对比

| 特性 | QSplitter | QHBoxLayout |
|------|-----------|-------------|
| 用户可拖拽调整 | 是 | 否 |
| 初始尺寸设置 | `setSizes({200, 600})` | `setStretch(0, 1)` |
| 性能开销 | 略高（拖拽手柄） | 更低 |
| 适用场景 | 需要用户调整比例 | 固定比例 |

> **原则**：需要用户交互调整用 QSplitter，固定比例用 QHBoxLayout + stretch

### 8.4 QScrollArea 性能陷阱

```cpp
// ✅ 正确：setWidgetResizable(true)，内容跟随滚动区域大小
auto* scrollArea = new QScrollArea();
scrollArea->setWidgetResizable(true);
scrollArea->setWidget(contentWidget_);

// ❌ 错误：忘记 setWidgetResizable(true)，内容不跟随调整
auto* scrollArea = new QScrollArea();
scrollArea->setWidget(contentWidget_);  // 内容保持原始大小，不跟随

// ✅ 正确：去掉默认边框，避免视觉干扰
scrollArea->setFrameShape(QFrame::NoFrame);
```

### 8.5 大量控件的布局优化

当面板包含大量控件（如设置页面 50+ 表单项）时：

```cpp
// ✅ 正确：用 QTabWidget 分组，避免一次计算所有控件
auto* tabWidget = new QTabWidget();
tabWidget->addTab(createBasicTab(), tr("Basic"));    // 10 个控件
tabWidget->addTab(createAdvancedTab(), tr("Advanced"));  // 20 个控件
tabWidget->addTab(createExpertTab(), tr("Expert"));    // 20 个控件
// 只计算当前 Tab 的控件

// ❌ 错误：所有控件放在一个 QScrollArea 中
auto* scrollArea = new QScrollArea();
auto* form = new QFormLayout();
// ... 50 个 addRow，每次窗口调整都计算 50 个控件
```

### 8.6 布局嵌套性能

每层布局都有计算开销，嵌套越深，一次布局激活的级联计算越多：

```
✅ 2 层嵌套：1 次激活 → 2 次计算
QVBoxLayout
  ├── QFormLayout
  └── QHBoxLayout

⚠️ 3 层嵌套：1 次激活 → 3 次计算
QVBoxLayout
  ├── QHBoxLayout
  │   ├── QVBoxLayout
  │   └── QVBoxLayout
  └── QHBoxLayout

❌ 4 层嵌套：1 次激活 → 4 次计算（必须拆分）
QVBoxLayout
  ├── QHBoxLayout
  │   ├── QVBoxLayout
  │   │   ├── QFormLayout  ← 第 4 层
  │   │   └── QHBoxLayout  ← 第 4 层
  │   └── QVBoxLayout
  └── QHBoxLayout
```

> **拆分方法**：将第 3-4 层的内部结构提取为独立 QWidget，对外只暴露 1 个控件接口。
