# Qt Widget 动画模式库

## 1. 基础动画工具类

```cpp
// ui/animation/AnimationUtils.h
#pragma once
#include <QWidget>
#include <QPropertyAnimation>
#include <QParallelAnimationGroup>
#include <QSequentialAnimationGroup>
#include <QEasingCurve>

class AnimationUtils {
public:
    // ========== 淡入淡出 ==========
    
    static QPropertyAnimation* FadeIn(QWidget* widget, 
                                      int duration = 300,
                                      QEasingCurve curve = QEasingCurve::InOutQuad);
    
    static QPropertyAnimation* FadeOut(QWidget* widget, 
                                       int duration = 300,
                                       QEasingCurve curve = QEasingCurve::InOutQuad);
    
    // ========== 滑动动画 ==========
    
    static QPropertyAnimation* SlideIn(QWidget* widget,
                                       Qt::Edge from,
                                       int duration = 300);
    
    static QPropertyAnimation* SlideOut(QWidget* widget,
                                        Qt::Edge to,
                                        int duration = 300);
    
    // ========== 缩放动画 ==========
    
    static QPropertyAnimation* Scale(QWidget* widget,
                                     qreal fromScale,
                                     qreal toScale,
                                     int duration = 200);
    
    static QPropertyAnimation* PopIn(QWidget* widget, int duration = 300);
    static QPropertyAnimation* PopOut(QWidget* widget, int duration = 200);
    
    // ========== 位移动画 ==========
    
    static QPropertyAnimation* MoveTo(QWidget* widget,
                                      const QPoint& targetPos,
                                      int duration = 300);
    
    // ========== 尺寸动画 ==========
    
    static QPropertyAnimation* ResizeTo(QWidget* widget,
                                        const QSize& targetSize,
                                        int duration = 300);
    
    // ========== 颜色动画 ==========
    
    template<typename T>
    static QVariantAnimation* ColorTransition(T* target,
                                               const QColor& from,
                                               const QColor& to,
                                               int duration = 300);
    
    // ========== 组合动画 ==========
    
    static QParallelAnimationGroup* FadeAndSlide(QWidget* widget,
                                                  Qt::Edge from,
                                                  int duration = 300);
    
    static QSequentialAnimationGroup* Shake(QWidget* widget,
                                            int intensity = 10,
                                            int duration = 500);
    
    // ========== 特殊效果 ==========
    
    static QPropertyAnimation* Pulse(QWidget* widget, int duration = 1000);
    static QPropertyAnimation* Bounce(QWidget* widget, int duration = 600);
    static QPropertyAnimation* Flip(QWidget* widget, int duration = 400);
};
```

```cpp
// ui/animation/AnimationUtils.cpp
#include "AnimationUtils.h"
#include <QGraphicsOpacityEffect>

QPropertyAnimation* AnimationUtils::FadeIn(QWidget* widget, int duration, QEasingCurve curve) {
    auto* effect = new QGraphicsOpacityEffect(widget);
    widget->setGraphicsEffect(effect);
    effect->setOpacity(0);
    widget->show();
    
    auto* animation = new QPropertyAnimation(effect, "opacity");
    animation->setDuration(duration);
    animation->setStartValue(0.0);
    animation->setEndValue(1.0);
    animation->setEasingCurve(curve);
    
    QObject::connect(animation, &QPropertyAnimation::finished, [effect]() {
        effect->deleteLater();
    });
    
    animation->start(QAbstractAnimation::DeleteWhenStopped);
    return animation;
}

QPropertyAnimation* AnimationUtils::FadeOut(QWidget* widget, int duration, QEasingCurve curve) {
    auto* effect = new QGraphicsOpacityEffect(widget);
    widget->setGraphicsEffect(effect);
    
    auto* animation = new QPropertyAnimation(effect, "opacity");
    animation->setDuration(duration);
    animation->setStartValue(1.0);
    animation->setEndValue(0.0);
    animation->setEasingCurve(curve);
    
    QObject::connect(animation, &QPropertyAnimation::finished, [widget, effect]() {
        widget->hide();
        effect->deleteLater();
    });
    
    animation->start(QAbstractAnimation::DeleteWhenStopped);
    return animation;
}

QPropertyAnimation* AnimationUtils::SlideIn(QWidget* widget, Qt::Edge from, int duration) {
    QPoint startPos = widget->pos();
    QPoint endPos = startPos;
    
    switch (from) {
    case Qt::LeftEdge:
        startPos.setX(startPos.x() - widget->width());
        break;
    case Qt::RightEdge:
        startPos.setX(startPos.x() + widget->width());
        break;
    case Qt::TopEdge:
        startPos.setY(startPos.y() - widget->height());
        break;
    case Qt::BottomEdge:
        startPos.setY(startPos.y() + widget->height());
        break;
    }
    
    widget->move(startPos);
    widget->show();
    
    auto* animation = new QPropertyAnimation(widget, "pos");
    animation->setDuration(duration);
    animation->setStartValue(startPos);
    animation->setEndValue(endPos);
    animation->setEasingCurve(QEasingCurve::OutCubic);
    
    animation->start(QAbstractAnimation::DeleteWhenStopped);
    return animation;
}

QPropertyAnimation* AnimationUtils::PopIn(QWidget* widget, int duration) {
    widget->setWindowOpacity(0);
    widget->show();
    
    auto* animation = new QPropertyAnimation(widget, "windowOpacity");
    animation->setDuration(duration);
    animation->setStartValue(0.0);
    animation->setEndValue(1.0);
    animation->setEasingCurve(QEasingCurve::OutBack);
    
    animation->start(QAbstractAnimation::DeleteWhenStopped);
    return animation;
}

QSequentialAnimationGroup* AnimationUtils::Shake(QWidget* widget, int intensity, int duration) {
    auto* group = new QSequentialAnimationGroup(widget);
    QPoint originalPos = widget->pos();
    
    int shakeCount = 8;
    int shakeDuration = duration / shakeCount;
    
    for (int i = 0; i < shakeCount; ++i) {
        auto* anim = new QPropertyAnimation(widget, "pos");
        anim->setDuration(shakeDuration);
        
        int offset = (i % 2 == 0 ? 1 : -1) * intensity * (shakeCount - i) / shakeCount;
        anim->setEndValue(originalPos + QPoint(offset, 0));
        
        group->addAnimation(anim);
    }
    
    auto* returnAnim = new QPropertyAnimation(widget, "pos");
    returnAnim->setDuration(100);
    returnAnim->setEndValue(originalPos);
    group->addAnimation(returnAnim);
    
    group->start(QAbstractAnimation::DeleteWhenStopped);
    return group;
}

QPropertyAnimation* AnimationUtils::Pulse(QWidget* widget, int duration) {
    auto* animation = new QPropertyAnimation(widget, "geometry");
    animation->setDuration(duration);
    animation->setKeyValueAt(0.0, widget->geometry());
    animation->setKeyValueAt(0.5, widget->geometry().adjusted(-5, -5, 5, 5));
    animation->setKeyValueAt(1.0, widget->geometry());
    animation->setEasingCurve(QEasingCurve::InOutSine);
    animation->setLoopCount(-1);  // 无限循环
    
    animation->start(QAbstractAnimation::DeleteWhenStopped);
    return animation;
}
```

## 2. 页面切换动画

```cpp
// ui/animation/StackedWidgetAnimator.h
#pragma once
#include <QStackedWidget>
#include <QPropertyAnimation>

class StackedWidgetAnimator : public QObject {
    Q_OBJECT
public:
    enum AnimationType {
        Fade,
        SlideLeft,
        SlideRight,
        SlideUp,
        SlideDown,
        Scale
    };
    
    explicit StackedWidgetAnimator(QStackedWidget* stackedWidget, 
                                   QObject* parent = nullptr);
    
    void SetAnimationType(AnimationType type);
    void SetDuration(int duration);
    
    void AnimateTo(int index);
    void AnimateTo(QWidget* widget);

private:
    void AnimateFade(int from, int to);
    void AnimateSlide(int from, int to, bool left);
    void AnimateScale(int from, int to);
    
    QStackedWidget* stacked_widget_;
    AnimationType type_ = Fade;
    int duration_ = 300;
    bool animating_ = false;
};
```

```cpp
// StackedWidgetAnimator.cpp
void StackedWidgetAnimator::AnimateFade(int from, int to) {
    QWidget* fromWidget = stacked_widget_->widget(from);
    QWidget* toWidget = stacked_widget_->widget(to);
    
    auto* effect = new QGraphicsOpacityEffect(toWidget);
    toWidget->setGraphicsEffect(effect);
    effect->setOpacity(0);
    
    stacked_widget_->setCurrentIndex(to);
    
    auto* anim = new QPropertyAnimation(effect, "opacity");
    anim->setDuration(duration_);
    anim->setStartValue(0.0);
    anim->setEndValue(1.0);
    
    connect(anim, &QPropertyAnimation::finished, [effect]() {
        effect->deleteLater();
    });
    
    anim->start(QAbstractAnimation::DeleteWhenStopped);
}
```

## 3. 列表项动画

```cpp
// ui/animation/ListViewAnimator.h
#pragma once
#include <QListView>
#include <QStandardItemModel>

class ListViewAnimator : public QObject {
    Q_OBJECT
public:
    explicit ListViewAnimator(QListView* listView, QObject* parent = nullptr);
    
    void AnimateInsert(int row, int count = 1);
    void AnimateRemove(int row, int count = 1);
    void AnimateUpdate(int row);

private:
    void SetupItemDelegate();
    
    QListView* list_view_;
};
```

## 4. 加载动画

```cpp
// ui/animation/LoadingSpinner.h
#pragma once
#include <QWidget>

class LoadingSpinner : public QWidget {
    Q_OBJECT
public:
    explicit LoadingSpinner(QWidget* parent = nullptr);
    
    void SetColor(const QColor& color);
    void SetThickness(int thickness);
    void SetSpeed(int rpm);  // 转每分钟
    
    void Start();
    void Stop();

protected:
    void paintEvent(QPaintEvent* event) override;
    void showEvent(QShowEvent* event) override;
    void hideEvent(QHideEvent* event) override;

private:
    void UpdateAnimation();
    
    QColor color_ = QColor("#6200EE");
    int thickness_ = 4;
    int rpm_ = 60;
    qreal angle_ = 0;
    int timer_id_ = -1;
};
```

```cpp
// LoadingSpinner.cpp
void LoadingSpinner::paintEvent(QPaintEvent* event) {
    QPainter painter(this);
    painter.setRenderHint(QPainter::Antialiasing);
    
    int side = qMin(width(), height()) - thickness_;
    QRectF rect((width() - side) / 2.0, (height() - side) / 2.0, side, side);
    
    // 绘制背景圆环
    QPen bgPen(QColor(0, 0, 0, 30));
    bgPen.setWidth(thickness_);
    bgPen.setCapStyle(Qt::RoundCap);
    painter.setPen(bgPen);
    painter.drawEllipse(rect);
    
    // 绘制进度弧
    QPen progressPen(color_);
    progressPen.setWidth(thickness_);
    progressPen.setCapStyle(Qt::RoundCap);
    painter.setPen(progressPen);
    
    int spanAngle = 90 * 16;  // 90度
    painter.drawArc(rect, -angle_ * 16, -spanAngle);
}

void LoadingSpinner::updateAnimation() {
    angle_ += 360.0 / (60.0 * 60 / rpm_);  // 假设 60fps
    if (angle_ >= 360) angle_ = 0;
    update();
}

void LoadingSpinner::showEvent(QShowEvent* event) {
    timer_id_ = startTimer(1000 / 60);  // 60fps
    QWidget::showEvent(event);
}

void LoadingSpinner::hideEvent(QHideEvent* event) {
    if (timer_id_ != -1) {
        killTimer(timer_id_);
        timer_id_ = -1;
    }
    QWidget::hideEvent(event);
}
```

## 5. 骨架屏动画

```cpp
// ui/animation/SkeletonWidget.h
#pragma once
#include <QWidget>

class SkeletonWidget : public QWidget {
    Q_OBJECT
public:
    explicit SkeletonWidget(QWidget* parent = nullptr);
    
    void AddRect(const QRect& rect);
    void AddCircle(const QPoint& center, int radius);
    void Clear();
    
    void StartShimmer();
    void StopShimmer();

protected:
    void paintEvent(QPaintEvent* event) override;

private:
    struct Shape {
        enum Type { Rect, Circle } type;
        QRect rect;
        QPoint center;
        int radius;
    };
    
    QVector<Shape> shapes_;
    qreal shimmer_offset_ = 0;
    int timer_id_ = -1;
};
```

## 6. 数字滚动动画

```cpp
// ui/animation/AnimatedNumber.h
#pragma once
#include <QLabel>

class AnimatedNumber : public QLabel {
    Q_OBJECT
    Q_PROPERTY(int value READ Value WRITE SetValue)
    
public:
    explicit AnimatedNumber(QWidget* parent = nullptr);
    
    int Value() const { return value_; }
    void SetValue(int value);
    
    void AnimateTo(int target, int duration = 500);

private:
    int value_ = 0;
    QPropertyAnimation* animation_ = nullptr;
};
```

## 7. 使用示例

### 对话框弹出

```cpp
void ShowDialog(QDialog* dialog) {
    // 淡入 + 缩放
    dialog->setWindowOpacity(0);
    dialog->show();
    
    auto* fade = AnimationUtils::FadeIn(dialog, 200);
    auto* scale = AnimationUtils::Scale(dialog, 0.9, 1.0, 250);
}
```

### 错误提示抖动

```cpp
void ShowError(QWidget* widget) {
    // 变红 + 抖动
    widget->setStyleSheet("border: 2px solid #B00020;");
    AnimationUtils::Shake(widget, 10, 400);
    
    // 3秒后恢复
    QTimer::singleShot(3000, [widget]() {
        widget->setStyleSheet("");
    });
}
```

### 列表项添加动画

```cpp
void AddListItem(QListWidget* list, const QString& text) {
    auto* item = new QListWidgetItem(text);
    list->addItem(item);
    
    auto* widget = list->itemWidget(item);
    if (widget) {
        AnimationUtils::SlideIn(widget, Qt::LeftEdge, 200);
    }
}
```

## 8. 性能优化建议

1. **使用 QPropertyAnimation 而非手动计时器**
   - 自动处理插值
   - 支持暂停/恢复
   - 更好的性能

2. **避免同时运行过多动画**
   - 限制并发动画数量
   - 使用动画组管理

3. **使用 QWidget::update() 而非 repaint()**
   - 允许 Qt 合并绘制请求

4. **动画结束后清理资源**
   - 使用 DeleteWhenStopped
   - 删除临时效果对象

5. **在低性能设备上禁用复杂动画**
   
```cpp
bool shouldAnimate() {
    // 检测是否低性能模式
    return !QGuiApplication::platformName().contains("embedded");
}
```
