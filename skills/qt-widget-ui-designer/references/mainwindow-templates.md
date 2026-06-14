# 主窗口代码模板

## 1. 树形导航+内容主窗口

适用模式：**模式5-树形导航+内容模式**

### .h 模板

```cpp
#pragma once
#include <QMainWindow>
#include <QSplitter>
#include <QTreeView>
#include <QStackedWidget>
#include <QToolBar>
#include <QStatusBar>

class {ClassName} : public QMainWindow {
    Q_OBJECT
public:
    explicit {ClassName}(QWidget* parent = nullptr);

private:
    void SetupUi();
    void ConnectSignals();

    QToolBar* toolbar_ = nullptr;
    QSplitter* splitter_ = nullptr;
    QTreeView* navTree_ = nullptr;
    QStackedWidget* contentStack_ = nullptr;
    QStatusBar* statusBar_ = nullptr;
};
```

### .cpp 模板

```cpp
void {ClassName}::SetupUi() {
    setWindowTitle(tr("{WindowTitle}"));
    resize(1000, 700);

    // 工具栏
    toolbar_ = addToolBar(tr("Main"));
    toolbar_->setMovable(false);
    toolbar_->addAction(QIcon::fromTheme("document-new"), tr("New"), this, [this]() {
        // emit signal or call handler
    });
    toolbar_->addSeparator();

    // 中央区域：树形导航 + 内容
    splitter_ = new QSplitter(Qt::Horizontal);

    navTree_ = new QTreeView();
    navTree_->setMinimumWidth(180);
    navTree_->setHeaderHidden(true);
    splitter_->addWidget(navTree_);

    contentStack_ = new QStackedWidget();
    splitter_->addWidget(contentStack_);

    splitter_->setStretchFactor(0, 0);
    splitter_->setStretchFactor(1, 1);
    splitter_->setSizes({220, 780});

    setCentralWidget(splitter_);

    // 状态栏
    statusBar_ = statusBar();
    statusBar_->showMessage(tr("Ready"));
}
```

## 2. 停靠窗口主窗口

适用模式：**模式8-停靠窗口模式**

### .h 模板

```cpp
#pragma once
#include <QMainWindow>
#include <QDockWidget>
#include <QTreeView>
#include <QTextEdit>
#include <QToolBar>
#include <QStatusBar>

class {ClassName} : public QMainWindow {
    Q_OBJECT
public:
    explicit {ClassName}(QWidget* parent = nullptr);

private:
    void SetupUi();
    void ConnectSignals();

    QToolBar* toolbar_ = nullptr;
    QDockWidget* navDock_ = nullptr;
    QDockWidget* propDock_ = nullptr;
    QDockWidget* outputDock_ = nullptr;
    QTreeView* navTree_ = nullptr;
    QWidget* centralWidget_ = nullptr;
    QTextEdit* outputEdit_ = nullptr;
};
```

### .cpp 模板

```cpp
void {ClassName}::SetupUi() {
    setWindowTitle(tr("{WindowTitle}"));
    resize(1200, 800);

    // 中央内容
    centralWidget_ = new QWidget();
    setCentralWidget(centralWidget_);

    // 导航停靠窗口（左侧）
    navDock_ = new QDockWidget(tr("Navigator"), this);
    navTree_ = new QTreeView();
    navTree_->setMinimumWidth(180);
    navTree_->setHeaderHidden(true);
    navDock_->setWidget(navTree_);
    addDockWidget(Qt::LeftDockWidgetArea, navDock_);

    // 属性停靠窗口（右侧）
    propDock_ = new QDockWidget(tr("Properties"), this);
    auto* propWidget = new QWidget();
    auto* propLayout = new QVBoxLayout(propWidget);
    propLayout->setContentsMargins(8, 8, 8, 8);
    // ... 添加属性控件
    propLayout->addStretch();
    propDock_->setWidget(propWidget);
    propDock_->setMinimumWidth(220);
    addDockWidget(Qt::RightDockWidgetArea, propDock_);

    // 输出停靠窗口（底部）
    outputDock_ = new QDockWidget(tr("Output"), this);
    outputEdit_ = new QTextEdit();
    outputEdit_->setReadOnly(true);
    outputEdit_->setMinimumHeight(120);
    outputDock_->setWidget(outputEdit_);
    addDockWidget(Qt::BottomDockWidgetArea, outputDock_);

    // 工具栏
    toolbar_ = addToolBar(tr("Main"));
    toolbar_->setMovable(false);

    // 状态栏
    statusBar()->showMessage(tr("Ready"));
}
```

### 保存/恢复布局

```cpp
void {ClassName}::closeEvent(QCloseEvent* event) {
    QSettings settings("MyCompany", "MyApp");
    settings.setValue("mainwindow/state", saveState());
    settings.setValue("mainwindow/geometry", saveGeometry());
    QMainWindow::closeEvent(event);
}

void {ClassName}::RestoreLayout() {
    QSettings settings("MyCompany", "MyApp");
    restoreGeometry(settings.value("mainwindow/geometry").toByteArray());
    restoreState(settings.value("mainwindow/state").toByteArray());
}
```
