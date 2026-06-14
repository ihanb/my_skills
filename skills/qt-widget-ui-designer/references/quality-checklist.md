# 质量校验清单

AI 生成 QWidget UI 代码后，按此清单逐项自查。定点微调后只校验受影响的项。

## 1. 布局合理性

- [ ] **嵌套深度**：布局嵌套不超过 3 层，超过则拆分为自定义 Widget
- [ ] **stretch 分配**：弹性区域设置了 stretch factor，没有无 stretch 的嵌套布局
- [ ] **间距标准**：控件间 8px，分组间 16px，窗口边距 12px
- [ ] **无固定尺寸**：没有使用 setFixedWidth/setFixedHeight（用 minimumSize + stretch 代替）
- [ ] **ScrollArea**：可能超长的内容用 QScrollArea 包裹，且 setWidgetResizable(true)
- [ ] **布局选择**：表单用 QFormLayout，侧边栏+内容用 QSplitter，没有"万能布局"

## 2. 模式一致性

- [ ] **模式匹配**：选择了正确的设计模式（表单/列表+详情/工具栏+内容/选项卡/树形导航/向导/状态面板/停靠窗口）
- [ ] **布局结构**：布局结构与模式描述一致
- [ ] **控件组合**：控件组合符合模式规范（如列表+详情模式使用 QSplitter）

## 3. 代码质量

- [ ] **setupUi()**：UI 初始化在 setupUi() 私有方法中，不在构造函数直接写
- [ ] **connectSignals()**：信号槽连接在 connectSignals() 私有方法中
- [ ] **无业务逻辑**：UI 类中没有业务逻辑，数据操作通过信号发出
- [ ] **成员变量命名**：snake_case_ 尾下划线风格
- [ ] **新式 connect**：使用新式 connect 语法，不用 SLOT/SIGNAL 宏
- [ ] **对话框数据返回**：对话框通过信号返回数据，不直接操作外部对象
- [ ] **#pragma once**：头文件使用 #pragma once 守卫

## 4. 可维护性

- [ ] **子 Widget 拆分**：复杂布局拆分为子 Widget（嵌套超过 3 层时必须拆分）
- [ ] **命名常量**：魔法数字提取为命名常量或 constexpr
- [ ] **有意义的变量名**：控件对象有有意义的变量名（不是 label1, label2, button1）
- [ ] **tr() 包裹**：用户可见文字用 tr() 包裹，支持国际化

## 5. QSS 性能校验

- [ ] **选择器性能**：QSS 使用 `#objectName` 选择器而非类名选择器或后代选择器
- [ ] **样式表集中**：样式表设置在根容器上，利用 CSS 继承，不在每个子控件单独设置
- [ ] **一次性设置**：setStyleSheet() 只在 setupUi() 中调用，不在运行时频繁调用
- [ ] **无渐变**：没有使用 QSS 渐变（qlineargradient 等），用纯色替代
- [ ] **无阴影**：没有试图用 QSS 实现阴影效果（QSS 不支持 box-shadow）
- [ ] **圆角合理**：border-radius 不超过 6px，避免大圆角性能问题
- [ ] **动态样式切换**：运行时样式变化使用 setProperty() + polish/unpolish，而非重新 setStyleSheet()
- [ ] **样式字符串管理**：长样式表字符串提取为 static const 变量，不内联在代码中

## 6. 控件选择校验

- [ ] **只读文本用 QLabel**：没有用 QTextEdit/QTextBrowser 显示只读文本
- [ ] **单行输入用 QLineEdit**：没有用 QTextEdit 做单行输入
- [ ] **数值输入用 QSpinBox**：没有用 QLineEdit + 正则验证做数值输入
- [ ] **少量选项用 QComboBox**：没有用 QListView + Model 做少量选项选择
- [ ] **状态指示用 QLabel + QSS**：没有用 QFrame + 自定义绘制做简单状态指示

## 7. 内存管理校验

- [ ] **所有控件有 parent**：所有 new 出的控件都指定了 parent 或加入了布局
- [ ] **对话框生命周期**：模态对话框用栈创建，非模态对话框设置 WA_DeleteOnClose
- [ ] **无裸 new**：没有 new 出控件但不加入布局或指定 parent 的情况
- [ ] **布局接管**：布局通过 `new QVBoxLayout(this)` 创建，让 QWidget 接管

## 8. 信号槽校验

- [ ] **无循环连接**：没有 A→B→A 的信号槽循环
- [ ] **批量更新阻塞**：批量设置控件值时使用 blockSignals(true/false)
- [ ] **高频更新队列化**：高频数据更新使用 Qt::QueuedConnection
- [ ] **信号选择正确**：区分 textChanged（程序+用户）和 textEdited（仅用户）

## 9. 保真度校验（HTML → Qt 视觉一致性）

- [ ] **无双重 padding**：有布局的 QWidget，QSS 中没有 `padding`（只用 `setContentsMargins()`）
- [ ] **WA_Hover 已设置**：使用 QSS `:hover` 的自定义 QWidget/QFrame 子类已设置 `setAttribute(Qt::WA_Hover)`
- [ ] **Q_PROPERTY 已声明**：QSS 属性选择器 `[prop=value]` 匹配的自定义属性已用 `Q_PROPERTY` 声明
- [ ] **小 QLabel 精确尺寸**：状态点、徽章等小尺寸 QLabel 已设置 `setFixedSize()`
- [ ] **分隔线用 QFrame**：水平分隔线使用独立 `QFrame(HLine)`，不用 QSS `border-bottom`
- [ ] **背景色全覆盖**：每个可见 QWidget 都显式设置了背景色，没有依赖透明继承
- [ ] **颜色来自 ThemeManager**：所有颜色值来自 ThemeManager，没有硬编码色值
- [ ] **高度策略正确**：卡片/列表项用 `setFixedHeight()`，内容区域用 `setMinimumHeight()`
- [ ] **字号一致性**：Qt 中 ≤11px 字号已检查是否偏小，必要时增大 1px
- [ ] **样式继承完整**：子控件单独 `setStyleSheet()` 时，继承属性（font-size 等）没有丢失

## 10. 常见微调速查表

用户反馈调整时的快速参考：

| 用户说 | 可能的问题 | 代码级修改 |
|-------|-----------|-----------|
| "控件太挤" | spacing 太小 | `layout->setSpacing(16)` |
| "留白不够" | margins 太小 | `layout->setContentsMargins(16,16,16,16)` |
| "左边太窄" | stretch 不对 | 左侧 stretch=1, 右侧 stretch=3 |
| "按钮太小" | 缺少最小尺寸 | `btn->setMinimumWidth(100)` |
| "输入框太短" | 缺少 sizePolicy | `edit->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed)` |
| "内容被截断" | 缺少 ScrollArea | 用 QScrollArea 包裹内容区 |
| "窗口不能拉伸" | 缺少 sizePolicy | 设置 `QSizePolicy::Expanding` |
| "控件对不齐" | 布局类型不对 | 换用 QFormLayout 或添加 layout alignment |
| "侧边栏不能拖拽调整" | 用了 QHBoxLayout | 换用 QSplitter |
| "列表项太少看不到" | 缺少最小高度 | `listWidget->setMinimumHeight(150)` |

## 10. 调整类型与校验范围

定点微调后只需校验受影响的项：

| 调整类型 | 需校验的清单项 |
|---------|--------------|
| 布局调整 | 1.布局合理性（全部） |
| 尺寸调整 | 1.无固定尺寸、1.stretch分配 |
| 增删控件 | 2.模式一致性、3.无业务逻辑、3.对话框数据返回、6.控件选择 |
| 控件替换 | 3.connectSignals、3.新式connect、3.对话框数据返回、6.控件选择 |
| 间距调整 | 1.间距标准 |
| 结构重组 | 全量校验（影响面大） |
| 样式调整 | 5.QSS性能校验（全部） |
| 信号槽调整 | 8.信号槽校验（全部） |
| 内存相关 | 7.内存管理校验（全部） |
