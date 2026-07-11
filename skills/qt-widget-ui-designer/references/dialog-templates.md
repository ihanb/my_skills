# 对话框代码模板

## 1. 表单对话框

适用模式：**模式1-表单模式**

### .h 模板

```cpp
#pragma once
#include <QDialog>
#include <QLineEdit>
#include <QComboBox>
#include <QTextEdit>
#include <QDialogButtonBox>

class {ClassName} : public QDialog {
    Q_OBJECT
public:
    explicit {ClassName}(QWidget* parent = nullptr);

    void SetName(const QString& name);
    void SetType(int type);

signals:
    void DataSubmitted(const QVariantMap& data);

private:
    void setupUi();
    void connectSignals();

    QLineEdit* nameEdit_ = nullptr;
    QComboBox* typeCombo_ = nullptr;
    QTextEdit* descEdit_ = nullptr;
    QDialogButtonBox* buttonBox_ = nullptr;
};
```

### .cpp 模板

```cpp
#include "{ClassName}.h"
#include <QFormLayout>
#include <QVBoxLayout>
#include <QVariantMap>

{ClassName}::{ClassName}(QWidget* parent)
    : QDialog(parent)
{
    setupUi();
    connectSignals();
}

void {ClassName}::setupUi() {
    setWindowTitle(tr("{DialogTitle}"));
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

    buttonBox_ = new QDialogButtonBox(
        QDialogButtonBox::Ok | QDialogButtonBox::Cancel);
    mainLayout->addWidget(buttonBox_);
}

void {ClassName}::connectSignals() {
    connect(buttonBox_, &QDialogButtonBox::accepted, this, [this]() {
        QVariantMap data;
        data["name"] = nameEdit_->text();
        data["type"] = typeCombo_->currentIndex();
        data["description"] = descEdit_->toPlainText();
        emit DataSubmitted(data);
        accept();
    });
    connect(buttonBox_, &QDialogButtonBox::rejected, this, &QDialog::reject);
}

void {ClassName}::SetName(const QString& name) {
    nameEdit_->setText(name);
}

void {ClassName}::SetType(int type) {
    typeCombo_->setCurrentIndex(type);
}
```

## 2. 可滚动表单对话框

表单项多时，用 QScrollArea 包裹表单区域。

### .cpp 关键差异

```cpp
void {ClassName}::setupUi() {
    setWindowTitle(tr("{DialogTitle}"));
    setMinimumSize(500, 400);

    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(0, 0, 0, 0);
    mainLayout->setSpacing(0);

    // 可滚动表单区域
    auto* scrollArea = new QScrollArea();
    scrollArea->setWidgetResizable(true);
    scrollArea->setFrameShape(QFrame::NoFrame);

    auto* contentWidget = new QWidget();
    auto* formLayout = new QFormLayout(contentWidget);
    formLayout->setContentsMargins(12, 12, 12, 12);
    formLayout->setSpacing(8);
    formLayout->setLabelAlignment(Qt::AlignRight | Qt::AlignVCenter);

    // ... 添加大量表单项

    scrollArea->setWidget(contentWidget);
    mainLayout->addWidget(scrollArea, 1);

    // 按钮区域（不随滚动）
    auto* buttonLayout = new QHBoxLayout();
    buttonLayout->setContentsMargins(12, 8, 12, 8);
    buttonLayout->addStretch();
    auto* okBtn = new QPushButton(tr("OK"));
    okBtn->setMinimumWidth(80);
    auto* cancelBtn = new QPushButton(tr("Cancel"));
    cancelBtn->setMinimumWidth(80);
    buttonLayout->addWidget(okBtn);
    buttonLayout->addWidget(cancelBtn);
    mainLayout->addLayout(buttonLayout);
}
```

## 3. 分组表单对话框

用 QGroupBox 将表单分为多个区域。

### .cpp 关键差异

```cpp
void {ClassName}::setupUi() {
    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(12, 12, 12, 12);
    mainLayout->setSpacing(16);

    // 基本信息分组
    auto* basicGroup = new QGroupBox(tr("Basic Info"));
    auto* basicLayout = new QFormLayout(basicGroup);
    basicLayout->setSpacing(8);
    basicLayout->addRow(tr("Name:"), nameEdit_);
    basicLayout->addRow(tr("Type:"), typeCombo_);
    mainLayout->addWidget(basicGroup);

    // 高级设置分组
    auto* advancedGroup = new QGroupBox(tr("Advanced"));
    auto* advancedLayout = new QFormLayout(advancedGroup);
    advancedLayout->setSpacing(8);
    advancedLayout->addRow(tr("Timeout:"), timeoutSpin_);
    advancedLayout->addRow(tr("Retry:"), retryCheck_);
    mainLayout->addWidget(advancedGroup);

    auto* buttonBox = new QDialogButtonBox(
        QDialogButtonBox::Ok | QDialogButtonBox::Cancel);
    mainLayout->addWidget(buttonBox);
}
```

## 4. 向导对话框

适用模式：**模式6-向导模式**

### .h 模板

```cpp
#pragma once
#include <QDialog>
#include <QStackedWidget>
#include <QLabel>
#include <QPushButton>

class {ClassName} : public QDialog {
    Q_OBJECT
public:
    explicit {ClassName}(QWidget* parent = nullptr);

signals:
    void WizardCompleted(const QVariantMap& data);

private:
    void setupUi();
    void connectSignals();
    void UpdateNavigation();
    QWidget* CreateStep1();
    QWidget* CreateStep2();
    QWidget* CreateStep3();

    QStackedWidget* stepStack_ = nullptr;
    QLabel* stepLabel_ = nullptr;
    QPushButton* backButton_ = nullptr;
    QPushButton* nextButton_ = nullptr;
    QPushButton* finishButton_ = nullptr;
    int currentStep_ = 0;
    static constexpr int kTotalSteps = 3;
};
```

### .cpp 模板

```cpp
void {ClassName}::setupUi() {
    setWindowTitle(tr("{DialogTitle}"));
    setMinimumSize(600, 400);

    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(12, 12, 12, 12);
    mainLayout->setSpacing(16);

    stepLabel_ = new QLabel();
    stepLabel_->setAlignment(Qt::AlignCenter);
    mainLayout->addWidget(stepLabel_);

    stepStack_ = new QStackedWidget();
    stepStack_->addWidget(CreateStep1());
    stepStack_->addWidget(CreateStep2());
    stepStack_->addWidget(CreateStep3());
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

void {ClassName}::connectSignals() {
    connect(backButton_, &QPushButton::clicked, this, [this]() {
        if (currentStep_ > 0) {
            currentStep_--;
            stepStack_->setCurrentIndex(currentStep_);
            UpdateNavigation();
        }
    });
    connect(nextButton_, &QPushButton::clicked, this, [this]() {
        if (currentStep_ < kTotalSteps - 1) {
            currentStep_++;
            stepStack_->setCurrentIndex(currentStep_);
            UpdateNavigation();
        }
    });
    connect(finishButton_, &QPushButton::clicked, this, [this]() {
        emit WizardCompleted(QVariantMap{});
        accept();
    });
}

void {ClassName}::UpdateNavigation() {
    stepLabel_->setText(tr("Step %1 of %2").arg(currentStep_ + 1).arg(kTotalSteps));
    backButton_->setEnabled(currentStep_ > 0);
    nextButton_->setVisible(currentStep_ < kTotalSteps - 1);
    finishButton_->setVisible(currentStep_ == kTotalSteps - 1);
}

QWidget* {ClassName}::CreateStep1() {
    auto* widget = new QWidget();
    auto* layout = new QVBoxLayout(widget);
    layout->setContentsMargins(12, 12, 12, 12);
    // ... 步骤1的控件
    layout->addStretch();
    return widget;
}
```

## 5. 确认对话框

简单的确认/询问对话框，不需要自定义类，直接使用 QMessageBox：

```cpp
auto result = QMessageBox::question(
    this,
    tr("Confirm"),
    tr("Are you sure you want to delete this item?"),
    QMessageBox::Yes | QMessageBox::No,
    QMessageBox::No
);
if (result == QMessageBox::Yes) {
    // 执行删除
}
```
