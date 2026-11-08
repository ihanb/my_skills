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
    toggleButton_->setObjectName("panelToggleButton");  // 样式由根容器集中设置
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

    // ✅ 根容器一次性设置，#objectName 选择器，不在子控件上单独 setStyleSheet()
    setObjectName("collapsiblePanel");
    setStyleSheet(QStringLiteral(
        "#panelToggleButton { border: none; font-weight: bold; }"
    ));
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
    enum class Status { Normal, Warning, Critical };  // 必须先于 SetStatus 声明，否则参数类型不可见

    explicit StatusCard(const QString& title, QWidget* parent = nullptr);

    void SetValue(const QString& value);
    void SetValue(int value);
    void SetUnit(const QString& unit);
    void SetStatus(Status status);

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
#include "status_card.h"
#include "ui/style/theme_manager.h"
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
    valueLabel_->setObjectName("statusCardValue");
    valueLabel_->setAlignment(Qt::AlignCenter);
    layout->addWidget(valueLabel_);

    unitLabel_ = new QLabel();
    unitLabel_->setObjectName("statusCardUnit");
    unitLabel_->setAlignment(Qt::AlignCenter);
    layout->addWidget(unitLabel_);

    // ✅ 样式集中在根容器一次性设置：#objectName 选择器 + ThemeManager 色值
    auto* tm = ThemeManager::Instance();
    static const QString kStyle = QStringLiteral(R"(
        #statusCardValue { font-size: 28px; font-weight: bold; color: %1; }
        #statusCardUnit  { font-size: 12px; color: %2; }
        #statusCardValue[status="warning"]  { color: %3; }
        #statusCardValue[status="critical"] { color: %4; }
    )");
    setStyleSheet(kStyle.arg(tm->ThemeColor(QStringLiteral("on_background")).name(),
                             tm->ThemeColor(QStringLiteral("on_surface_secondary")).name(),
                             tm->ThemeColor(QStringLiteral("warning")).name(),
                             tm->ThemeColor(QStringLiteral("error")).name()));
    valueLabel_->setProperty("status", "normal");
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
    // ✅ 运行时只切动态属性，不重建样式表；颜色由 setupUi() 里的 QSS 规则决定
    const char* state = "normal";
    switch (status) {
    case Status::Normal:   state = "normal";   break;
    case Status::Warning:  state = "warning";  break;
    case Status::Critical: state = "critical"; break;
    }
    valueLabel_->setProperty("status", state);
    valueLabel_->style()->unpolish(valueLabel_);
    valueLabel_->style()->polish(valueLabel_);
}

void StatusCard::mousePressEvent(QMouseEvent* event) {
    emit Clicked();
    QGroupBox::mousePressEvent(event);
}
```
