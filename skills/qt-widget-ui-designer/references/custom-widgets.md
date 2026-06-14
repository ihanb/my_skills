# 自定义控件样式指南

## 1. 卡片控件 (CardWidget)

### 效果预览
Material Design 风格的卡片，带阴影效果，支持不同高度层级。

### 实现代码

```cpp
// ui/widgets/CardWidget.h
#pragma once
#include <QFrame>
#include <QPropertyAnimation>

class CardWidget : public QFrame {
    Q_OBJECT
    Q_PROPERTY(int elevation READ Elevation WRITE SetElevation NOTIFY ElevationChanged)
    Q_PROPERTY(qreal radius READ Radius WRITE SetRadius)
    
public:
    explicit CardWidget(QWidget* parent = nullptr);
    ~CardWidget();
    
    int Elevation() const { return elevation_; }
    void SetElevation(int elevation);
    
    qreal Radius() const { return radius_; }
    void SetRadius(qreal radius);
    
    void SetHeaderWidget(QWidget* widget);
    void SetContentWidget(QWidget* widget);
    void SetFooterWidget(QWidget* widget);

signals:
    void ElevationChanged(int elevation);

protected:
    void paintEvent(QPaintEvent* event) override;
    void enterEvent(QEnterEvent* event) override;
    void leaveEvent(QEvent* event) override;
    void mousePressEvent(QMouseEvent* event) override;
    void mouseReleaseEvent(QMouseEvent* event) override;

private:
    void UpdateShadow();
    void AnimateElevation(int target);
    
    int elevation_ = 1;
    qreal radius_ = 8.0;
    bool hovered_ = false;
    bool pressed_ = false;
    
    QWidget* header_ = nullptr;
    QWidget* content_ = nullptr;
    QWidget* footer_ = nullptr;
    
    QPropertyAnimation* elevation_animation_ = nullptr;
};
```

```cpp
// ui/widgets/CardWidget.cpp
#include "CardWidget.h"
#include <QPainter>
#include <QVBoxLayout>
#include <QGraphicsDropShadowEffect>

CardWidget::CardWidget(QWidget* parent) 
    : QFrame(parent) {
    setFrameShape(QFrame::NoFrame);
    setAttribute(Qt::WA_TranslucentBackground);
    
    auto* layout = new QVBoxLayout(this);
    layout->setContentsMargins(16, 16, 16, 16);
    layout->setSpacing(12);
    
    UpdateShadow();
}

CardWidget::~CardWidget() = default;

void CardWidget::SetElevation(int elevation) {
    elevation = qBound(0, elevation, 24);
    if (elevation_ != elevation) {
        elevation_ = elevation;
        UpdateShadow();
        emit ElevationChanged(elevation);
    }
}

void CardWidget::SetRadius(qreal radius) {
    radius_ = radius;
    update();
}

void CardWidget::SetHeaderWidget(QWidget* widget) {
    if (header_) {
        layout()->removeWidget(header_);
        delete header_;
    }
    header_ = widget;
    if (widget) {
        static_cast<QVBoxLayout*>(layout())->insertWidget(0, widget);
    }
}

void CardWidget::SetContentWidget(QWidget* widget) {
    if (content_) {
        layout()->removeWidget(content_);
        delete content_;
    }
    content_ = widget;
    if (widget) {
        int index = header_ ? 1 : 0;
        static_cast<QVBoxLayout*>(layout())->insertWidget(index, widget, 1);
    }
}

void CardWidget::SetFooterWidget(QWidget* widget) {
    if (footer_) {
        layout()->removeWidget(footer_);
        delete footer_;
    }
    footer_ = widget;
    if (widget) {
        static_cast<QVBoxLayout*>(layout())->addWidget(widget);
    }
}

void CardWidget::paintEvent(QPaintEvent* event) {
    QPainter painter(this);
    painter.setRenderHint(QPainter::Antialiasing);
    
    // 绘制背景
    QRectF rect = this->rect().adjusted(1, 1, -1, -1);
    painter.setPen(Qt::NoPen);
    painter.setBrush(QColor("#FFFFFF"));
    painter.drawRoundedRect(rect, radius_, radius_);
    
    // 绘制边框（可选）
    if (elevation_ == 0) {
        painter.setPen(QPen(QColor("#E0E0E0"), 1));
        painter.setBrush(Qt::NoBrush);
        painter.drawRoundedRect(rect, radius_, radius_);
    }
    
    QFrame::paintEvent(event);
}

void CardWidget::UpdateShadow() {
    auto* effect = graphicsEffect();
    if (!effect) {
        effect = new QGraphicsDropShadowEffect(this);
        setGraphicsEffect(effect);
    }
    
    auto* shadow = static_cast<QGraphicsDropShadowEffect*>(effect);
    
    // Material Design 阴影参数
    static const QMap<int, QPair<int, qreal>> shadowParams = {
        {0, {0, 0.0}},
        {1, {2, 0.14}},
        {2, {4, 0.14}},
        {3, {6, 0.14}},
        {4, {8, 0.14}},
        {6, {10, 0.14}},
        {8, {12, 0.14}},
        {12, {16, 0.14}},
        {16, {20, 0.14}},
        {24, {24, 0.14}}
    };
    
    auto params = shadowParams.value(elevation_, qMakePair(2, 0.14));
    shadow->setBlurRadius(params.first * 2);
    shadow->setColor(QColor(0, 0, 0, static_cast<int>(params.second * 255)));
    shadow->setOffset(0, params.first / 2);
}

void CardWidget::enterEvent(QEnterEvent* event) {
    hovered_ = true;
    if (elevation_ < 8) {
        AnimateElevation(elevation_ + 2);
    }
    QFrame::enterEvent(event);
}

void CardWidget::leaveEvent(QEvent* event) {
    hovered_ = false;
    if (!pressed_) {
        AnimateElevation(elevation_ > 2 ? elevation_ - 2 : 1);
    }
    QFrame::leaveEvent(event);
}

void CardWidget::mousePressEvent(QMouseEvent* event) {
    pressed_ = true;
    AnimateElevation(8);
    QFrame::mousePressEvent(event);
}

void CardWidget::mouseReleaseEvent(QMouseEvent* event) {
    pressed_ = false;
    if (!hovered_) {
        AnimateElevation(elevation_ > 2 ? elevation_ - 2 : 1);
    }
    QFrame::mouseReleaseEvent(event);
}

void CardWidget::AnimateElevation(int target) {
    if (!elevation_animation_) {
        elevation_animation_ = new QPropertyAnimation(this, "elevation", this);
        elevation_animation_->setDuration(150);
        elevation_animation_->setEasingCurve(QEasingCurve::OutCubic);
    }
    
    elevation_animation_->stop();
    elevation_animation_->setStartValue(elevation_);
    elevation_animation_->setEndValue(target);
    elevation_animation_->start();
}
```

### 使用示例

```cpp
auto* card = new CardWidget(this);
card->SetElevation(2);
card->SetRadius(12);

auto* title = new QLabel("Card Title");
title->setStyleSheet("font-size: 20px; font-weight: 500; color: #212121;");

auto* content = new QLabel("This is the card content.");
content->setWordWrap(true);

auto* button = new QPushButton("Action");
button->setFlat(true);

auto* footer = new QWidget;
auto* footerLayout = new QHBoxLayout(footer);
footerLayout->addStretch();
footerLayout->addWidget(button);

card->SetHeaderWidget(title);
card->SetContentWidget(content);
card->SetFooterWidget(footer);
```

---

## 2. 浮动操作按钮 (FloatingActionButton)

```cpp
// ui/widgets/FloatingActionButton.h
#pragma once
#include <QPushButton>
#include <QPropertyAnimation>

class FloatingActionButton : public QPushButton {
    Q_OBJECT
    Q_PROPERTY(qreal scale READ Scale WRITE SetScale)
    
public:
    enum class Size { Mini, Normal, Extended };
    
    explicit FloatingActionButton(const QIcon& icon, QWidget* parent = nullptr);
    explicit FloatingActionButton(const QString& text, const QIcon& icon, QWidget* parent = nullptr);
    
    void SetSize(Size size);
    void SetColor(const QColor& color);
    void SetRippleEnabled(bool enabled);

protected:
    void paintEvent(QPaintEvent* event) override;
    void enterEvent(QEnterEvent* event) override;
    void leaveEvent(QEvent* event) override;
    void mousePressEvent(QMouseEvent* event) override;

private:
    void Init();
    void AnimateScale(qreal target);
    void DrawRipple(QPainter& painter);
    
    Size size_ = Size::Normal;
    QColor color_ = QColor("#6200EE");
    qreal scale_ = 1.0;
    bool ripple_enabled_ = true;
    QPoint ripple_center_;
    qreal ripple_radius_ = 0.0;
    
    QPropertyAnimation* scale_animation_ = nullptr;
    QPropertyAnimation* ripple_animation_ = nullptr;
};
```

---

## 3. 开关按钮 (SwitchButton)

```cpp
// ui/widgets/SwitchButton.h
#pragma once
#include <QAbstractButton>

class SwitchButton : public QAbstractButton {
    Q_OBJECT
    Q_PROPERTY(int offset READ Offset WRITE SetOffset)
    
public:
    explicit SwitchButton(QWidget* parent = nullptr);
    
    QSize sizeHint() const override;
    
protected:
    void paintEvent(QPaintEvent* event) override;
    void mouseReleaseEvent(QMouseEvent* event) override;
    void enterEvent(QEnterEvent* event) override;
    void leaveEvent(QEvent* event) override;
    
    int Offset() const { return offset_; }
    void SetOffset(int offset);

private:
    void AnimateToggle();
    
    int offset_ = 0;
    int radius_ = 12;
    bool hovered_ = false;
    QColor active_color_ = QColor("#6200EE");
    QColor inactive_color_ = QColor("#9E9E9E");
};
```

```cpp
// ui/widgets/SwitchButton.cpp
#include "SwitchButton.h"
#include <QPainter>
#include <QPropertyAnimation>

SwitchButton::SwitchButton(QWidget* parent)
    : QAbstractButton(parent) {
    setCheckable(true);
    setCursor(Qt::PointingHandCursor);
}

QSize SwitchButton::sizeHint() const {
    return QSize(48, 28);
}

void SwitchButton::paintEvent(QPaintEvent* event) {
    QPainter painter(this);
    painter.setRenderHint(QPainter::Antialiasing);
    
    bool checked = isChecked();
    
    // 绘制轨道
    QRectF trackRect = rect().adjusted(2, 6, -2, -6);
    painter.setPen(Qt::NoPen);
    painter.setBrush(checked ? active_color_ : inactive_color_);
    if (!checked && hovered_) {
        painter.setBrush(QColor("#BDBDBD"));
    }
    painter.drawRoundedRect(trackRect, trackRect.height() / 2, trackRect.height() / 2);
    
    // 绘制滑块
    int diameter = height() - 8;
    QRectF thumbRect(offset_ + 4, 4, diameter, diameter);
    painter.setBrush(Qt::white);
    painter.setPen(QPen(QColor(0, 0, 0, 12), 1));
    painter.drawEllipse(thumbRect);
}

void SwitchButton::mouseReleaseEvent(QMouseEvent* event) {
    if (event->button() == Qt::LeftButton) {
        setChecked(!isChecked());
        AnimateToggle();
        emit toggled(isChecked());
    }
    QAbstractButton::mouseReleaseEvent(event);
}

void SwitchButton::enterEvent(QEnterEvent* event) {
    hovered_ = true;
    update();
    QAbstractButton::enterEvent(event);
}

void SwitchButton::leaveEvent(QEvent* event) {
    hovered_ = false;
    update();
    QAbstractButton::leaveEvent(event);
}

void SwitchButton::SetOffset(int offset) {
    offset_ = offset;
    update();
}

void SwitchButton::AnimateToggle() {
    auto* animation = new QPropertyAnimation(this, "offset", this);
    animation->setDuration(150);
    animation->setEasingCurve(QEasingCurve::InOutCubic);
    
    int targetOffset = isChecked() ? width() - height() + 4 : 0;
    animation->setStartValue(offset_);
    animation->setEndValue(targetOffset);
    animation->start(QAbstractAnimation::DeleteWhenStopped);
}
```

---

## 4. 加载指示器 (CircularProgress)

```cpp
// ui/widgets/CircularProgress.h
#pragma once
#include <QWidget>

class CircularProgress : public QWidget {
    Q_OBJECT
    Q_PROPERTY(int value READ Value WRITE SetValue)
    Q_PROPERTY(int thickness READ Thickness WRITE SetThickness)
    
public:
    explicit CircularProgress(QWidget* parent = nullptr);
    
    int Value() const { return value_; }
    void SetValue(int value);
    
    int Thickness() const { return thickness_; }
    void SetThickness(int thickness);
    
    void SetIndeterminate(bool indeterminate);
    void SetColor(const QColor& color);

protected:
    void paintEvent(QPaintEvent* event) override;
    void showEvent(QShowEvent* event) override;
    void hideEvent(QHideEvent* event) override;

private:
    void StartAnimation();
    void StopAnimation();
    
    int value_ = 0;
    int thickness_ = 4;
    bool indeterminate_ = true;
    QColor color_ = QColor("#6200EE");
    qreal angle_ = 0;
    
    int animation_id_ = -1;
};
```

---

## 5. 徽章控件 (Badge)

```cpp
// ui/widgets/Badge.h
#pragma once
#include <QLabel>

class Badge : public QLabel {
    Q_OBJECT
public:
    enum class Style { Dot, Number, Text };
    
    explicit Badge(QWidget* parent = nullptr);
    
    void SetBadgeStyle(Style style);
    void SetCount(int count);
    void SetText(const QString& text);
    void SetColor(const QColor& color);
    
    void AttachTo(QWidget* widget, Qt::Corner corner = Qt::TopRightCorner);

protected:
    void paintEvent(QPaintEvent* event) override;
    void resizeEvent(QResizeEvent* event) override;

private:
    void UpdateSize();
    void UpdatePosition();
    
    Style style_ = Style::Number;
    QColor color_ = QColor("#B00020");
    QWidget* target_widget_ = nullptr;
    Qt::Corner corner_ = Qt::TopRightCorner;
    int count_ = 0;
};
```

---

## 6. 输入框增强 (EnhancedLineEdit)

```cpp
// ui/widgets/EnhancedLineEdit.h
#pragma once
#include <QLineEdit>

class EnhancedLineEdit : public QLineEdit {
    Q_OBJECT
    Q_PROPERTY(QString label READ Label WRITE SetLabel)
    Q_PROPERTY(QString helperText READ HelperText WRITE SetHelperText)
    Q_PROPERTY(bool error READ IsError WRITE SetError)
    
public:
    explicit EnhancedLineEdit(QWidget* parent = nullptr);
    
    QString Label() const { return label_; }
    void SetLabel(const QString& label);
    
    QString HelperText() const { return helper_text_; }
    void SetHelperText(const QString& text);
    
    bool IsError() const { return error_; }
    void SetError(bool error);
    void SetErrorText(const QString& text);
    
    void SetLeadingIcon(const QIcon& icon);
    void SetTrailingIcon(const QIcon& icon);

protected:
    void paintEvent(QPaintEvent* event) override;
    void resizeEvent(QResizeEvent* event) override;
    void focusInEvent(QFocusEvent* event) override;
    void focusOutEvent(QFocusEvent* event) override;

private:
    void UpdateStyle();
    void DrawLabel(QPainter& painter);
    void DrawHelperText(QPainter& painter);
    
    QString label_;
    QString helper_text_;
    QString error_text_;
    bool error_ = false;
    bool focused_ = false;
    
    QIcon leading_icon_;
    QIcon trailing_icon_;
};
```

---

## 7. 步骤条 (Stepper)

```cpp
// ui/widgets/Stepper.h
#pragma once
#include <QWidget>
#include <QVector>

class Stepper : public QWidget {
    Q_OBJECT
public:
    struct Step {
        QString title;
        QString description;
        bool optional = false;
    };
    
    explicit Stepper(QWidget* parent = nullptr);
    
    void SetSteps(const QVector<Step>& steps);
    void SetCurrentStep(int index);
    void SetStepCompleted(int index, bool completed);

signals:
    void StepClicked(int index);

protected:
    void paintEvent(QPaintEvent* event) override;
    void mousePressEvent(QMouseEvent* event) override;

private:
    void DrawStep(QPainter& painter, const Step& step, int index, 
                  bool active, bool completed);
    
    QVector<Step> steps_;
    int current_step_ = 0;
    QSet<int> completed_steps_;
};
```

---

## 8. 时间线 (Timeline)

```cpp
// ui/widgets/Timeline.h
#pragma once
#include <QWidget>
#include <QDateTime>

class Timeline : public QWidget {
    Q_OBJECT
public:
    struct Event {
        QString title;
        QString description;
        QDateTime timestamp;
        QColor color;
        QIcon icon;
    };
    
    explicit Timeline(QWidget* parent = nullptr);
    
    void AddEvent(const Event& event);
    void Clear();

protected:
    void paintEvent(QPaintEvent* event) override;

private:
    void DrawEvent(QPainter& painter, const Event& event, 
                   int index, int y);
    
    QVector<Event> events_;
    int line_width_ = 2;
    int dot_size_ = 12;
    int spacing_ = 60;
};
```

---

## 样式应用最佳实践

### 1. 使用属性选择器

```cpp
// 在代码中设置属性
button->setProperty("type", "primary");
button->setProperty("type", "secondary");
button->setProperty("type", "danger");
```

```css
/* 在 QSS 中根据属性应用样式 */
QPushButton[type="primary"] {
    background-color: #6200EE;
    color: white;
}

QPushButton[type="secondary"] {
    background-color: transparent;
    color: #6200EE;
    border: 1px solid #6200EE;
}

QPushButton[type="danger"] {
    background-color: #B00020;
    color: white;
}
```

### 2. 动态主题切换

```cpp
// 监听主题变化
connect(ThemeManager::Instance(), &ThemeManager::ThemeChanged,
        this, [this]() {
    // 重新应用样式
    updateStyle();
});

void CustomWidget::updateStyle() {
    // 根据当前主题更新颜色
    primary_color_ = ThemeManager::Instance()->PrimaryColor();
    update();
}
```

### 3. 高 DPI 适配

```cpp
// 在绘制时使用设备像素比
void CustomWidget::paintEvent(QPaintEvent* event) {
    QPainter painter(this);
    qreal dpr = devicePixelRatioF();
    
    // 调整绘制参数
    int penWidth = qRound(2 * dpr);
    painter.setPen(QPen(color_, penWidth));
    
    // 使用缩放后的尺寸
    QRect rect = this->rect() * dpr;
    // ... 绘制代码
}
```
