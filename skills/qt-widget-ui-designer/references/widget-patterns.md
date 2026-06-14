# QWidget UI 设计模式库

8 种核心 UI 模式，覆盖常见桌面应用场景。每种模式包含布局结构、代码骨架和变体说明。

---

## 模式 1：表单模式

**适用场景**：设置对话框、属性编辑、登录/注册、数据录入

**布局结构**：
```
┌─────────────────────────────┐
│  QFormLayout                │
│    Label1:  [Input1      ]  │
│    Label2:  [Input2      ]  │
│    Label3:  [ComboBox   ]  │
│                             │
│  ─────── 分隔线 ───────     │
│                             │
│         [OK]  [Cancel]     │
└─────────────────────────────┘
```

**代码骨架**：
```cpp
class XxxDialog : public QDialog {
    Q_OBJECT
public:
    explicit XxxDialog(QWidget* parent = nullptr);

signals:
    void DataSubmitted(const QVariantMap& data);

private:
    void SetupUi();
    void ConnectSignals();

    QLineEdit* nameEdit_ = nullptr;
    QComboBox* typeCombo_ = nullptr;
    QTextEdit* descEdit_ = nullptr;
    QPushButton* okButton_ = nullptr;
    QPushButton* cancelButton_ = nullptr;
};
```

```cpp
void XxxDialog::SetupUi() {
    setWindowTitle(tr("Xxx Dialog"));
    setMinimumWidth(400);

    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(12, 12, 12, 12);
    mainLayout->setSpacing(16);

    auto* formLayout = new QFormLayout();
    formLayout->setSpacing(8);
    formLayout->setLabelAlignment(Qt::AlignRight | Qt::AlignVCenter);

    nameEdit_ = new QLineEdit();
    nameEdit_->setMinimumWidth(200);
    formLayout->addRow(tr("Name:"), nameEdit_);

    typeCombo_ = new QComboBox();
    formLayout->addRow(tr("Type:"), typeCombo_);

    descEdit_ = new QTextEdit();
    descEdit_->setMinimumHeight(80);
    formLayout->addRow(tr("Description:"), descEdit_);

    mainLayout->addLayout(formLayout);

    auto* buttonLayout = new QHBoxLayout();
    buttonLayout->setSpacing(8);
    buttonLayout->addStretch();
    okButton_ = new QPushButton(tr("OK"));
    okButton_->setMinimumWidth(80);
    cancelButton_ = new QPushButton(tr("Cancel"));
    cancelButton_->setMinimumWidth(80);
    buttonLayout->addWidget(okButton_);
    buttonLayout->addWidget(cancelButton_);
    mainLayout->addLayout(buttonLayout);
}
```

**变体**：
- **可滚动表单**：表单项多时，用 QScrollArea 包裹 formLayout
- **分组表单**：用 QGroupBox 将表单分为多个区域
- **多列表单**：QFormLayout 支持 addRow(label, layout) 嵌入多控件行

---

## 模式 2：列表+详情模式

**适用场景**：主从浏览、邮件客户端、文件管理器、设备列表

**布局结构**：
```
┌──────────────┬───────────────────────┐
│  QListWidget │  详情区域              │
│  ┌──────────┐│  ┌─────────────────┐  │
│  │ Item 1   ││  │ 标题             │  │
│  │ Item 2 ◄─││  │ 属性1: 值1      │  │
│  │ Item 3   ││  │ 属性2: 值2      │  │
│  │ Item 4   ││  │ 描述...          │  │
│  └──────────┘│  └─────────────────┘  │
└──────────────┴───────────────────────┘
         QSplitter(Qt::Horizontal)
```

**代码骨架**：
```cpp
class XxxPanel : public QWidget {
    Q_OBJECT
public:
    explicit XxxPanel(QWidget* parent = nullptr);

private:
    void SetupUi();
    void ConnectSignals();

    QSplitter* splitter_ = nullptr;
    QListWidget* listWidget_ = nullptr;
    QWidget* detailWidget_ = nullptr;
};
```

```cpp
void XxxPanel::SetupUi() {
    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(0, 0, 0, 0);

    splitter_ = new QSplitter(Qt::Horizontal);

    listWidget_ = new QListWidget();
    listWidget_->setMinimumWidth(150);
    splitter_->addWidget(listWidget_);

    detailWidget_ = new QWidget();
    auto* detailLayout = new QVBoxLayout(detailWidget_);
    detailLayout->setContentsMargins(12, 12, 12, 12);
    // ... 添加详情控件
    splitter_->addWidget(detailWidget_);

    splitter_->setStretchFactor(0, 0);
    splitter_->setStretchFactor(1, 1);
    splitter_->setSizes({200, 600});

    mainLayout->addWidget(splitter_);
}
```

**变体**：
- **树形列表**：QListWidget 换为 QTreeWidget
- **表格列表**：QListWidget 换为 QTableView + 自定义 Model
- **搜索+列表**：列表上方添加 QLineEdit + QSortFilterProxyModel

---

## 模式 3：工具栏+内容模式

**适用场景**：编辑器、查看器、管理工具

**布局结构**：
```
┌─────────────────────────────────┐
│  QToolBar                       │
│  [New] [Open] [Save] | [Undo]  │
├─────────────────────────────────┤
│                                 │
│  QStackedWidget                 │
│  (根据工具栏选择切换内容页)      │
│                                 │
└─────────────────────────────────┘
```

**代码骨架**：
```cpp
class XxxView : public QWidget {
    Q_OBJECT
public:
    explicit XxxView(QWidget* parent = nullptr);

private:
    void SetupUi();
    void ConnectSignals();

    QToolBar* toolbar_ = nullptr;
    QStackedWidget* stackedWidget_ = nullptr;
};
```

```cpp
void XxxView::SetupUi() {
    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(0, 0, 0, 0);
    mainLayout->setSpacing(0);

    toolbar_ = new QToolBar();
    toolbar_->setMovable(false);
    toolbar_->addAction(QIcon::fromTheme("document-new"), tr("New"), this, &XxxView::onNew);
    toolbar_->addAction(QIcon::fromTheme("document-open"), tr("Open"), this, &XxxView::onOpen);
    toolbar_->addSeparator();
    mainLayout->addWidget(toolbar_);

    stackedWidget_ = new QStackedWidget();
    mainLayout->addWidget(stackedWidget_, 1);
}
```

**变体**：
- **侧边工具栏**：QToolBar 设为 Qt::Vertical，放在 QSplitter 左侧
- **双工具栏**：上方主工具栏 + 下方状态栏

---

## 模式 4：选项卡模式

**适用场景**：多功能面板、设置中心、属性面板

**布局结构**：
```
┌─────────────────────────────────┐
│  [Tab1] [Tab2] [Tab3]          │
├─────────────────────────────────┤
│                                 │
│  当前选项卡内容                  │
│                                 │
└─────────────────────────────────┘
```

**代码骨架**：
```cpp
void XxxPanel::SetupUi() {
    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(0, 0, 0, 0);

    auto* tabWidget = new QTabWidget();
    tabWidget->addTab(createGeneralTab(), tr("General"));
    tabWidget->addTab(createAdvancedTab(), tr("Advanced"));
    tabWidget->addTab(createAboutTab(), tr("About"));
    mainLayout->addWidget(tabWidget);
}

QWidget* XxxPanel::createGeneralTab() {
    auto* widget = new QWidget();
    auto* layout = new QVBoxLayout(widget);
    layout->setContentsMargins(12, 12, 12, 12);
    // ... 添加控件
    layout->addStretch();
    return widget;
}
```

**变体**：
- **可关闭选项卡**：`tabWidget->setTabsClosable(true)`
- **侧边选项卡**：`tabWidget->setTabPosition(QTabWidget::West)`

---

## 模式 5：树形导航+内容模式

**适用场景**：项目管理、资源浏览器、设置中心

**布局结构**：
```
┌──────────────┬───────────────────────┐
│  QTreeView   │  内容区域              │
│  ├─ 项目1    │  根据选中节点切换内容   │
│  │  ├─ 子项1 │                       │
│  │  └─ 子项2 │                       │
│  └─ 项目2    │                       │
└──────────────┴───────────────────────┘
         QSplitter(Qt::Horizontal)
```

**代码骨架**：
```cpp
void XxxWindow::SetupUi() {
    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(0, 0, 0, 0);

    splitter_ = new QSplitter(Qt::Horizontal);

    navTree_ = new QTreeView();
    navTree_->setMinimumWidth(180);
    navTree_->setHeaderHidden(true);
    splitter_->addWidget(navTree_);

    contentStack_ = new QStackedWidget();
    splitter_->addWidget(contentStack_);

    splitter_->setStretchFactor(0, 0);
    splitter_->setStretchFactor(1, 1);
    splitter_->setSizes({220, 580});

    mainLayout->addWidget(splitter_);
}
```

**变体**：
- **带搜索的树**：树上方添加搜索框 + QSortFilterProxyModel
- **带工具栏的树**：树上方添加增删改按钮

---

## 模式 6：向导模式

**适用场景**：安装向导、配置向导、导入导出向导

**布局结构**：
```
┌─────────────────────────────────┐
│  步骤指示器                      │
│  ① ── ② ── ③ ── ④            │
├─────────────────────────────────┤
│                                 │
│  QStackedWidget (当前步骤内容)   │
│                                 │
├─────────────────────────────────┤
│         [Back] [Next] [Finish]  │
└─────────────────────────────────┘
```

**代码骨架**：
```cpp
class XxxWizard : public QDialog {
    Q_OBJECT
public:
    explicit XxxWizard(QWidget* parent = nullptr);

signals:
    void WizardCompleted(const QVariantMap& data);

private:
    void SetupUi();
    void ConnectSignals();
    void UpdateNavigation();
    QWidget* createStep1();
    QWidget* createStep2();
    QWidget* createStep3();

    QStackedWidget* stepStack_ = nullptr;
    QLabel* stepLabel_ = nullptr;
    QPushButton* backButton_ = nullptr;
    QPushButton* nextButton_ = nullptr;
    QPushButton* finishButton_ = nullptr;
    int currentStep_ = 0;
    static constexpr int kTotalSteps = 3;
};
```

```cpp
void XxxWizard::SetupUi() {
    setWindowTitle(tr("Xxx Wizard"));
    setMinimumSize(600, 400);

    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(12, 12, 12, 12);
    mainLayout->setSpacing(16);

    stepLabel_ = new QLabel();
    stepLabel_->setAlignment(Qt::AlignCenter);
    mainLayout->addWidget(stepLabel_);

    stepStack_ = new QStackedWidget();
    stepStack_->addWidget(createStep1());
    stepStack_->addWidget(createStep2());
    stepStack_->addWidget(createStep3());
    mainLayout->addWidget(stepStack_, 1);

    auto* navLayout = new QHBoxLayout();
    navLayout->setSpacing(8);
    navLayout->addStretch();
    backButton_ = new QPushButton(tr("Back"));
    nextButton_ = new QPushButton(tr("Next"));
    finishButton_ = new QPushButton(tr("Finish"));
    navLayout->addWidget(backButton_);
    navLayout->addWidget(nextButton_);
    navLayout->addWidget(finishButton_);
    mainLayout->addLayout(navLayout);

    UpdateNavigation();
}

void XxxWizard::UpdateNavigation() {
    stepLabel_->setText(tr("Step %1 of %2").arg(currentStep_ + 1).arg(kTotalSteps));
    backButton_->setEnabled(currentStep_ > 0);
    nextButton_->setVisible(currentStep_ < kTotalSteps - 1);
    finishButton_->setVisible(currentStep_ == kTotalSteps - 1);
}
```

---

## 模式 7：状态面板模式

**适用场景**：仪表盘、监控面板、实时数据展示

**布局结构**：
```
┌──────────┬──────────┬──────────┐
│  卡片1   │  卡片2   │  卡片3   │
│  CPU: 45%│  MEM: 60%│  DISK:30%│
├──────────┴──────────┴──────────┤
│          图表区域               │
├──────────┬──────────┬──────────┤
│  卡片4   │  卡片5   │  卡片6   │
│  NET: 1G │  IO: 120 │  CONN: 8 │
└──────────┴──────────┴──────────┘
```

**代码骨架**：
```cpp
void XxxDashboard::SetupUi() {
    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(12, 12, 12, 12);
    mainLayout->setSpacing(12);

    // 顶部卡片行
    auto* topRow = new QHBoxLayout();
    topRow->setSpacing(12);
    topRow->addWidget(createStatusCard(tr("CPU"), "45%"));
    topRow->addWidget(createStatusCard(tr("Memory"), "60%"));
    topRow->addWidget(createStatusCard(tr("Disk"), "30%"));
    mainLayout->addLayout(topRow);

    // 图表区域
    auto* chartGroup = new QGroupBox(tr("Trends"));
    auto* chartLayout = new QVBoxLayout(chartGroup);
    mainLayout->addWidget(chartGroup, 1);

    // 底部卡片行
    auto* bottomRow = new QHBoxLayout();
    bottomRow->setSpacing(12);
    bottomRow->addWidget(createStatusCard(tr("Network"), "1 Gbps"));
    bottomRow->addWidget(createStatusCard(tr("I/O"), "120/s"));
    bottomRow->addWidget(createStatusCard(tr("Connections"), "8"));
    mainLayout->addLayout(bottomRow);
}

QGroupBox* XxxDashboard::createStatusCard(const QString& title, const QString& value) {
    auto* card = new QGroupBox(title);
    auto* layout = new QVBoxLayout(card);
    auto* valueLabel = new QLabel(value);
    valueLabel->setAlignment(Qt::AlignCenter);
    layout->addWidget(valueLabel);
    return card;
}
```

---

## 模式 8：停靠窗口模式

**适用场景**：IDE、调试器、复杂工具应用

**布局结构**：
```
┌──────────────────────────────────────┐
│  QToolBar                            │
├────────┬─────────────────┬───────────┤
│ Dock:L │                 │  Dock:R   │
│ 项目树  │   中央内容区域   │  属性面板  │
├────────┤                 ├───────────┤
│ Dock:B │                 │           │
│ 输出    │                 │           │
└────────┴─────────────────┴───────────┘
        QMainWindow + QDockWidget
```

**代码骨架**：
```cpp
class XxxMainWindow : public QMainWindow {
    Q_OBJECT
public:
    explicit XxxMainWindow(QWidget* parent = nullptr);

private:
    void SetupUi();
    void ConnectSignals();

    QDockWidget* navDock_ = nullptr;
    QDockWidget* propDock_ = nullptr;
    QDockWidget* outputDock_ = nullptr;
    QTreeView* navTree_ = nullptr;
    QWidget* centralWidget_ = nullptr;
};
```

```cpp
void XxxMainWindow::SetupUi() {
    centralWidget_ = new QWidget();
    setCentralWidget(centralWidget_);

    navDock_ = new QDockWidget(tr("Navigator"), this);
    navDock_->setWidget(new QTreeView());
    navDock_->setMinimumWidth(180);
    addDockWidget(Qt::LeftDockWidgetArea, navDock_);

    propDock_ = new QDockWidget(tr("Properties"), this);
    propDock_->setWidget(new QWidget());
    propDock_->setMinimumWidth(220);
    addDockWidget(Qt::RightDockWidgetArea, propDock_);

    outputDock_ = new QDockWidget(tr("Output"), this);
    outputDock_->setWidget(new QTextEdit());
    outputDock_->setMinimumHeight(120);
    addDockWidget(Qt::BottomDockWidgetArea, outputDock_);

    auto* toolbar = addToolBar(tr("Main"));
    toolbar->setMovable(false);
}
```

**变体**：
- **可嵌套停靠**：`setDockNestingEnabled(true)` 允许停靠窗口嵌套
- **保存/恢复布局**：`saveState()` / `restoreState()`
