# 自定义控件代码模板

## 1. 基础自定义控件

### .h 模板

```cpp
#pragma once
#include <QWidget>

class {ClassName} : public QWidget {
    Q_OBJECT
public:
    explicit {ClassName}(QWidget* parent = nullptr);

    // 公开接口
    QString Value() const;
    void SetValue(const QString& value);

signals:
    void ValueChanged(const QString& value);

private:
    void setupUi();
    void connectSignals();

    // 内部控件
    // ...
};
```

### .cpp 模板

```cpp
#include "{ClassName}.h"

{ClassName}::{ClassName}(QWidget* parent)
    : QWidget(parent)
{
    setupUi();
    connectSignals();
}

void {ClassName}::setupUi() {
    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(0, 0, 0, 0);
    mainLayout->setSpacing(0);
    // ... 添加内部控件
}

void {ClassName}::connectSignals() {
    // ... 连接内部信号槽
}

QString {ClassName}::Value() const {
    // 返回当前值
    return {};
}

void {ClassName}::SetValue(const QString& value) {
    // 设置当前值
    emit ValueChanged(value);
}
```

## 2. 可折叠面板控件

```cpp
#pragma once
#include <QWidget>
#include <QToolButton>
#include <QFrame>

class CollapsiblePanel : public QWidget {
    Q_OBJECT
public:
    explicit CollapsiblePanel(const QString& title, QWidget* parent = nullptr);

    void SetContentWidget(QWidget* content);
    void SetExpanded(bool expanded);
    bool IsExpanded() const;

signals:
    void Toggled(bool expanded);

private:
    void setupUi();
    void connectSignals();

    QToolButton* toggleButton_ = nullptr;
    QFrame* contentFrame_ = nullptr;
    QWidget* contentWidget_ = nullptr;
};
```

```cpp
#include "CollapsiblePanel.h"
#include <QVBoxLayout>
#include <QPropertyAnimation>
#include <QParallelAnimationGroup>

CollapsiblePanel::CollapsiblePanel(const QString& title, QWidget* parent)
    : QWidget(parent)
{
    setupUi();
    toggleButton_->setText(title);
    connectSignals();
}

void CollapsiblePanel::setupUi() {
    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(0, 0, 0, 0);
    mainLayout->setSpacing(0);

    toggleButton_ = new QToolButton();
    toggleButton_->setStyleSheet("QToolButton { border: none; font-weight: bold; }");
    toggleButton_->setToolButtonStyle(Qt::ToolButtonTextBesideIcon);
    toggleButton_->setArrowType(Qt::DownArrow);
    toggleButton_->setCheckable(true);
    toggleButton_->setChecked(true);
    mainLayout->addWidget(toggleButton_);

    contentFrame_ = new QFrame();
    auto* frameLayout = new QVBoxLayout(contentFrame_);
    frameLayout->setContentsMargins(8, 8, 8, 8);
    frameLayout->setSpacing(8);
    mainLayout->addWidget(contentFrame_);
}

void CollapsiblePanel::connectSignals() {
    connect(toggleButton_, &QToolButton::toggled, this, [this](bool checked) {
        toggleButton_->setArrowType(checked ? Qt::DownArrow : Qt::RightArrow);
        contentFrame_->setVisible(checked);
        emit Toggled(checked);
    });
}

void CollapsiblePanel::SetContentWidget(QWidget* content) {
    contentWidget_ = content;
    auto* layout = contentFrame_->layout();
    layout->addWidget(contentWidget_);
}

void CollapsiblePanel::SetExpanded(bool expanded) {
    toggleButton_->setChecked(expanded);
}

bool CollapsiblePanel::IsExpanded() const {
    return toggleButton_->isChecked();
}
```

## 3. 搜索框控件

```cpp
#pragma once
#include <QWidget>
#include <QLineEdit>
#include <QToolButton>

class SearchBox : public QWidget {
    Q_OBJECT
public:
    explicit SearchBox(QWidget* parent = nullptr);

    QString Text() const;
    void SetPlaceholderText(const QString& text);

signals:
    void TextChanged(const QString& text);
    void SearchRequested(const QString& text);
    void Cleared();

private:
    void setupUi();
    void connectSignals();

    QLineEdit* lineEdit_ = nullptr;
    QToolButton* clearButton_ = nullptr;
    QToolButton* searchButton_ = nullptr;
};
```

```cpp
#include "SearchBox.h"
#include <QHBoxLayout>

SearchBox::SearchBox(QWidget* parent)
    : QWidget(parent)
{
    setupUi();
    connectSignals();
}

void SearchBox::setupUi() {
    auto* layout = new QHBoxLayout(this);
    layout->setContentsMargins(0, 0, 0, 0);
    layout->setSpacing(0);

    lineEdit_ = new QLineEdit();
    lineEdit_->setPlaceholderText(tr("Search..."));
    lineEdit_->setMinimumWidth(200);
    layout->addWidget(lineEdit_);

    clearButton_ = new QToolButton();
    clearButton_->setText("×");  /* U+00D7 乘号，避免 emoji 跨系统渲染差异 */
    clearButton_->setVisible(false);
    layout->addWidget(clearButton_);

    searchButton_ = new QToolButton();
    searchButton_->setText("⌕");  /* U+2315 电话记录机符号，作为搜索图标 */
    layout->addWidget(searchButton_);
}

void SearchBox::connectSignals() {
    connect(lineEdit_, &QLineEdit::textChanged, this, [this](const QString& text) {
        clearButton_->setVisible(!text.isEmpty());
        emit TextChanged(text);
    });
    connect(lineEdit_, &QLineEdit::returnPressed, this, [this]() {
        emit SearchRequested(lineEdit_->text());
    });
    connect(clearButton_, &QToolButton::clicked, this, [this]() {
        lineEdit_->clear();
        emit Cleared();
    });
    connect(searchButton_, &QToolButton::clicked, this, [this]() {
        emit SearchRequested(lineEdit_->text());
    });
}

QString SearchBox::Text() const {
    return lineEdit_->text();
}

void SearchBox::SetPlaceholderText(const QString& text) {
    lineEdit_->setPlaceholderText(text);
}
```

## 4. 状态卡片控件

适用于仪表盘模式中的单个状态指标展示。

```cpp
#pragma once
#include <QGroupBox>
#include <QLabel>

class StatusCard : public QGroupBox {
    Q_OBJECT
public:
    explicit StatusCard(const QString& title, QWidget* parent = nullptr);

    void SetValue(const QString& value);
    void SetValue(int value);
    void SetUnit(const QString& unit);
    void SetStatus(StatusCard::Status status);

    enum class Status { Normal, Warning, Critical };

signals:
    void Clicked();

protected:
    void mousePressEvent(QMouseEvent* event) override;

private:
    void setupUi();
    QLabel* valueLabel_ = nullptr;
    QLabel* unitLabel_ = nullptr;
};
```

```cpp
#include "StatusCard.h"
#include "ui/style/ThemeManager.h"
#include <QVBoxLayout>
#include <QMouseEvent>

StatusCard::StatusCard(const QString& title, QWidget* parent)
    : QGroupBox(title, parent)
{
    setupUi();
}

void StatusCard::setupUi() {
    auto* layout = new QVBoxLayout(this);
    layout->setAlignment(Qt::AlignCenter);

    valueLabel_ = new QLabel("--");
    valueLabel_->setAlignment(Qt::AlignCenter);
    valueLabel_->setStyleSheet("font-size: 28px; font-weight: bold;");
    layout->addWidget(valueLabel_);

    unitLabel_ = new QLabel();
    unitLabel_->setAlignment(Qt::AlignCenter);
    unitLabel_->setStyleSheet(QString("font-size: 12px; color: %1;")
                              .arg(ThemeManager::Instance()->ThemeColor("on_surface_secondary").name()));
    layout->addWidget(unitLabel_);
}

void StatusCard::SetValue(const QString& value) {
    valueLabel_->setText(value);
}

void StatusCard::SetValue(int value) {
    valueLabel_->setText(QString::number(value));
}

void StatusCard::SetUnit(const QString& unit) {
    unitLabel_->setText(unit);
}

void StatusCard::SetStatus(Status status) {
    QColor color;
    switch (status) {
    case Status::Normal:  color = ThemeManager::Instance()->ThemeColor("success"); break;
    case Status::Warning: color = ThemeManager::Instance()->ThemeColor("warning"); break;
    case Status::Critical: color = ThemeManager::Instance()->ThemeColor("error"); break;
    }
    valueLabel_->setStyleSheet(QString("font-size: 28px; font-weight: bold; color: %1;").arg(color.name()));
}

void StatusCard::mousePressEvent(QMouseEvent* event) {
    emit Clicked();
    QGroupBox::mousePressEvent(event);
}
```
