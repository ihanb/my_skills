# 面板代码模板

## 1. 列表+详情面板

适用模式：**模式2-列表+详情模式**

### .h 模板

```cpp
#pragma once
#include <QWidget>
#include <QSplitter>
#include <QListWidget>
#include <QLabel>
#include <QLineEdit>

class {ClassName} : public QWidget {
    Q_OBJECT
public:
    explicit {ClassName}(QWidget* parent = nullptr);

signals:
    void ItemSelected(int id);

private:
    void setupUi();
    void connectSignals();

    QSplitter* splitter_ = nullptr;
    QListWidget* listWidget_ = nullptr;
    QWidget* detailWidget_ = nullptr;
    QLabel* titleLabel_ = nullptr;
    QLineEdit* nameEdit_ = nullptr;
};
```

### .cpp 模板

```cpp
void {ClassName}::setupUi() {
    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(0, 0, 0, 0);

    splitter_ = new QSplitter(Qt::Horizontal);

    listWidget_ = new QListWidget();
    listWidget_->setMinimumWidth(150);
    splitter_->addWidget(listWidget_);

    detailWidget_ = new QWidget();
    auto* detailLayout = new QVBoxLayout(detailWidget_);
    detailLayout->setContentsMargins(12, 12, 12, 12);
    detailLayout->setSpacing(8);

    titleLabel_ = new QLabel();
    detailLayout->addWidget(titleLabel_);

    auto* formLayout = new QFormLayout();
    formLayout->setSpacing(8);
    nameEdit_ = new QLineEdit();
    nameEdit_->setMinimumWidth(200);
    formLayout->addRow(tr("Name:"), nameEdit_);
    detailLayout->addLayout(formLayout);
    detailLayout->addStretch();

    splitter_->addWidget(detailWidget_);
    splitter_->setStretchFactor(0, 0);
    splitter_->setStretchFactor(1, 1);
    splitter_->setSizes({200, 600});

    mainLayout->addWidget(splitter_);
}
```

## 2. 工具栏+内容面板

适用模式：**模式3-工具栏+内容模式**

### .h 模板

```cpp
#pragma once
#include <QWidget>
#include <QToolBar>
#include <QStackedWidget>

class {ClassName} : public QWidget {
    Q_OBJECT
public:
    explicit {ClassName}(QWidget* parent = nullptr);

private:
    void setupUi();
    void connectSignals();

    QToolBar* toolbar_ = nullptr;
    QStackedWidget* stackedWidget_ = nullptr;
};
```

### .cpp 模板

```cpp
void {ClassName}::setupUi() {
    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(0, 0, 0, 0);
    mainLayout->setSpacing(0);

    toolbar_ = new QToolBar();
    toolbar_->setMovable(false);
    toolbar_->addAction(QIcon::fromTheme("document-new"), tr("New"), this, [this]() {
        // emit signal or call handler
    });
    toolbar_->addSeparator();
    mainLayout->addWidget(toolbar_);

    stackedWidget_ = new QStackedWidget();
    mainLayout->addWidget(stackedWidget_, 1);
}
```

## 3. 选项卡面板

适用模式：**模式4-选项卡模式**

### .h 模板

```cpp
#pragma once
#include <QWidget>
#include <QTabWidget>

class {ClassName} : public QWidget {
    Q_OBJECT
public:
    explicit {ClassName}(QWidget* parent = nullptr);

private:
    void setupUi();
    void connectSignals();
    QWidget* CreateGeneralTab();
    QWidget* CreateAdvancedTab();

    QTabWidget* tabWidget_ = nullptr;
};
```

### .cpp 模板

```cpp
void {ClassName}::setupUi() {
    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(0, 0, 0, 0);

    tabWidget_ = new QTabWidget();
    tabWidget_->addTab(CreateGeneralTab(), tr("General"));
    tabWidget_->addTab(CreateAdvancedTab(), tr("Advanced"));
    mainLayout->addWidget(tabWidget_);
}

QWidget* {ClassName}::CreateGeneralTab() {
    auto* widget = new QWidget();
    auto* layout = new QVBoxLayout(widget);
    layout->setContentsMargins(12, 12, 12, 12);
    layout->setSpacing(8);

    auto* formLayout = new QFormLayout();
    formLayout->setSpacing(8);
    // ... 添加控件
    layout->addLayout(formLayout);
    layout->addStretch();

    return widget;
}

QWidget* {ClassName}::CreateAdvancedTab() {
    auto* widget = new QWidget();
    auto* layout = new QVBoxLayout(widget);
    layout->setContentsMargins(12, 12, 12, 12);
    layout->setSpacing(8);
    // ... 添加控件
    layout->addStretch();

    return widget;
}
```

## 4. 状态面板

适用模式：**模式7-状态面板模式**

### .h 模板

```cpp
#pragma once
#include <QWidget>
#include <QGroupBox>
#include <QLabel>

class {ClassName} : public QWidget {
    Q_OBJECT
public:
    explicit {ClassName}(QWidget* parent = nullptr);

private:
    void setupUi();
    void connectSignals();
    QGroupBox* CreateStatusCard(const QString& title, const QString& value);
};
```

### .cpp 模板

```cpp
void {ClassName}::setupUi() {
    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(12, 12, 12, 12);
    mainLayout->setSpacing(12);

    // 顶部卡片行
    auto* topRow = new QHBoxLayout();
    topRow->setSpacing(12);
    topRow->addWidget(CreateStatusCard(tr("CPU"), "45%"));
    topRow->addWidget(CreateStatusCard(tr("Memory"), "60%"));
    topRow->addWidget(CreateStatusCard(tr("Disk"), "30%"));
    mainLayout->addLayout(topRow);

    // 图表区域
    auto* chartGroup = new QGroupBox(tr("Trends"));
    auto* chartLayout = new QVBoxLayout(chartGroup);
    mainLayout->addWidget(chartGroup, 1);

    // 底部卡片行
    auto* bottomRow = new QHBoxLayout();
    bottomRow->setSpacing(12);
    bottomRow->addWidget(CreateStatusCard(tr("Network"), "1 Gbps"));
    bottomRow->addWidget(CreateStatusCard(tr("I/O"), "120/s"));
    bottomRow->addWidget(CreateStatusCard(tr("Connections"), "8"));
    mainLayout->addLayout(bottomRow);
}

QGroupBox* {ClassName}::CreateStatusCard(const QString& title, const QString& value) {
    auto* card = new QGroupBox(title);
    auto* layout = new QVBoxLayout(card);
    auto* valueLabel = new QLabel(value);
    valueLabel->setAlignment(Qt::AlignCenter);
    layout->addWidget(valueLabel);
    return card;
}
```
