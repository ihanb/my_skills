---
name: qt-widget-ui-designer
description: >
  辅助 QWidget UI 组件设计与样式优化。当用户需要创建对话框、面板、主窗口布局、
  自定义控件、修改 UI 布局、美化界面、编写 QSS 样式表、实现主题切换、添加动画效果、
  适配高 DPI 或现代化 UI 设计时触发此 Skill。采用 HTML 视觉原型 + Qt 模式库混合方案：
  先生成 HTML/CSS 原型供用户在浏览器中快速验证布局，满意后转换为符合规范的
  QWidget C++ 代码，并完成样式美化和主题适配。支持 8 种核心设计模式、布局规则体系、
  QSS 样式系统、动画效果、质量校验和定点微调。
compatibility: Qt 6.x, C++17/20, CMake 3.25+
---

# Qt Widget UI 设计器 + 样式优化 Skill

## 核心功能

1. **HTML 视觉原型** — 用 HTML/CSS 快速表达布局，浏览器即时预览
2. **设计模式库** — 8 种核心 UI 模式，覆盖常见场景
3. **规范代码生成** — HTML 布局 + Qt 模式 → 符合架构规范的 C++ 代码
4. **QSS 样式系统** — 主题管理器、深色/浅色主题、自定义控件样式
5. **动画效果** — 属性动画、过渡效果、高 DPI 适配
6. **质量校验** — 生成后按清单自查
7. **定点微调** — 最小改动原则，精准调整

## 工作流程

### Step 1: 需求分析

识别以下信息：
- **组件类型**：对话框 / 面板 / 主窗口 / 自定义控件
- **功能需求**：需要哪些控件、数据输入输出
- **布局约束**：是否需要侧边栏、是否可调整大小、是否需要滚动
- **样式需求**：是否需要主题切换、深色/浅色模式、动画效果

向用户确认组件类型和关键约束，再进入下一步。

### Step 2: 生成 HTML 视觉原型

**前置条件：必须先读取项目 ThemeManager 的色值定义**，确保 HTML 原型使用与 Qt 代码完全一致的颜色。

根据需求生成 HTML/CSS 原型页面，遵循以下约束：

#### 布局约束

1. **只用 flexbox/grid 布局**，不用 float/position/absolute
2. **只用语义化标签**，不用纯 div 套 div
3. **用 HTML 注释标注 Qt 特殊控件**：
   - `<!-- dock: left/right/top/bottom -->` → QDockWidget
   - `<!-- splitter -->` → QSplitter
   - `<!-- tab-container -->` → QTabWidget
   - `<!-- stacked: page1, page2 -->` → QStackedWidget
   - `<!-- toolbar -->` → QToolBar
4. **不用 CSS 动画/过渡**（动画效果在 Qt 中用 QPropertyAnimation 实现）
5. **允许基础交互 JavaScript**：HTML 原型中可使用简单的 JS 实现交互预览（Tab 切换、按钮状态切换、列表选中、显示/隐藏、模态对话框、数值模拟等），让用户在浏览器中能真实体验交互流程。JS 仅用于原型演示，不映射到 Qt 代码（Qt 中用信号槽实现）。详见 `references/html-prototype-guide.md` 第 6 章。

#### 颜色约束（关键！）

6. **必须使用 ThemeManager 的实际色值**作为 CSS 变量，不用通用色值。生成 HTML 前先读取项目 `ThemeManager::LoadTheme()` 中的色值定义，将所有颜色映射为 CSS 变量：
   ```css
   :root {
     --primary: #3b82f6;           /* ThemeManager colors_["primary"] */
     --background: #1a1d23;        /* ThemeManager colors_["background"] */
     --surface: #22262e;           /* ThemeManager colors_["surface"] */
     --surface_variant: #2d323c;   /* ThemeManager colors_["surface_variant"] */
     --on_background: #e0e4ec;     /* ThemeManager colors_["on_background"] */
     --on_surface_secondary: #9ca3b0; /* ThemeManager colors_["on_surface_secondary"] */
     --on_surface_muted: #6b7280;  /* ThemeManager colors_["on_surface_muted"] */
     --error: #ef4444;             /* ThemeManager colors_["error"] */
     --success: #22c55e;           /* ThemeManager colors_["success"] */
     --border: #3a3f4b;            /* ThemeManager colors_["border"] */
     --divider: #2d323c;           /* ThemeManager colors_["divider"] */
     --hover_overlay: #363c48;     /* ThemeManager colors_["hover_overlay"] */
     --selected_bg: #2a3040;       /* ThemeManager colors_["selected_bg"] */
   }
   ```

#### QWidget 风格约束（关键！）

HTML 原型必须模拟 QWidget 的渲染特征，避免生成在 Qt 中无法还原的 Web 风格效果：

**核心原则：HTML 原型中使用的每个控件和样式属性，都必须在 QWidget 中有对应实现方案。如果某个 CSS 属性或 HTML 特性在 Qt 中无法用 QSS + 标准控件实现，或实现极度复杂（需要自定义 paintEvent、事件过滤等），则禁止在 HTML 原型中使用，必须改用 Qt 可实现的替代方案。**

| CSS/HTML 特性 | Qt 可行性 | 处理方式 |
|--------------|----------|---------|
| `background-color: #hex` | QSS 直接支持 | 正常使用 |
| `color: #hex` | QSS 直接支持 | 正常使用 |
| `border: 1px solid #hex` | QSS 直接支持 | 正常使用 |
| `border-radius: 4-6px` | QSS 直接支持 | 正常使用 |
| `font-size/font-weight` | QSS 直接支持 | 正常使用 |
| `padding/margin/gap` | QSS + layout margins | 正常使用 |
| `display: flex` | QBoxLayout/QGridLayout | 正常使用 |
| `box-shadow` | QSS 不支持 | 禁用，用 border 颜色差异模拟层次 |
| `text-shadow` | QSS 不支持 | 禁用 |
| `linear-gradient` | QSS 语法不同且性能差 | 禁用，用纯色替代 |
| `radial-gradient` | QSS 不支持 | 禁用，用纯色替代 |
| `backdrop-filter: blur` | QSS 不支持 | 禁用 |
| `border-image` | QSS 支持但复杂 | 禁用 |
| `opacity` | QSS 不支持 | 禁用，用更浅的颜色模拟 |
| `transform: scale/rotate` | QSS 不支持 | 禁用 |
| `transition/animation` | QSS 不支持 | 禁用，Qt 用 QPropertyAnimation |
| `position: absolute/fixed` | QWidget 不支持 | 禁用，用布局管理器 |
| `float` | QWidget 不支持 | 禁用，用布局管理器 |
| `overflow: hidden/scroll` | QScrollArea | 用 `<!-- scroll-area -->` 标注 |
| `::before/::after` 伪元素 | QSS 不支持 | 禁用，用真实 HTML 元素替代 |
| `:hover` 效果 | QSS 支持，但需 WA_Hover | 允许，但转换时需加 setAttribute |
| `:active/:focus` 效果 | QSS 支持 | 允许 |
| `z-index` 层叠 | QWidget 不支持 | 禁用，用布局顺序控制 |
| `filter: blur/drop-shadow` | QSS 不支持 | 禁用 |
| `clip-path` | QSS 不支持 | 禁用，用 border-radius 裁剪 |
| `object-fit: cover/contain` | QLabel setScaledContents | 用 `<!-- scaled-contents -->` 标注 |
| `white-space: nowrap` | QLabel setWordWrap(false) | 允许 |
| `text-overflow: ellipsis` | QLabel 无原生支持 | 用 `<!-- elided-label -->` 标注，Qt 中需自定义 |
| `resize: horizontal/vertical` | QSplitter | 用 `<!-- splitter -->` 标注 |
| CSS 变量 `var(--x)` | QSS 不支持变量 | HTML 中用变量，转换时替换为实际色值 |

**判定标准**：如果某个效果的 Qt 实现需要以下任一方式，则视为"极度复杂"，禁止在 HTML 原型中使用：
- 自定义 `paintEvent()` 绘制（除非是项目已有的自定义控件基类）
- 事件过滤器 `installEventFilter()`
- `QGraphicsEffect` 子类
- 平台相关代码（Win32 API 等）
- 第三方库引入

7. **禁用 CSS 特效**：不用 box-shadow（Qt 无原生支持）、不用 text-shadow、不用 backdrop-filter、不用 CSS gradient 叠加、不用 border-image
8. **禁用 Web 专属交互**：不用 :hover 变色/缩放（Qt hover 需代码实现）、不用 cursor 样式、不用 outline、不用 user-select
9. **边框用实线**：只用 `border: 1px solid #color`，不用虚线/双线/圆角渐变边框
10. **圆角有限使用**：只用 `border-radius: 4px` 或 `6px`，不用大圆角（Qt 圆角通过 QSS 实现，大圆角性能差）
11. **颜色用纯色**：只用 `background-color: #hex`，不用 linear-gradient/radial-gradient（渐变在 QSS 中性能差且语法不同）
12. **字体用系统字体**：`font-family: "Segoe UI", "Microsoft YaHei", sans-serif`，不用 Web 字体
13. **图标用文字/Unicode**：不用 SVG/CSS icon font，Qt 中用 QIcon 或 Unicode 字符
14. **间距用像素值**：只用 `8px/12px/16px` 标准值，不用 em/rem/vw/vh（Qt 布局基于像素）
15. **不用 CSS Grid 复杂特性**：不用 grid-template-areas、subgrid、auto-fill/auto-fit（QGridLayout 无法直接映射）
16. **模拟 QWidget 默认尺寸策略**：输入框宽度用 `flex:1` 而非 `width:100%`，按钮用 `min-width` 而非 `width`
17. **不用 CSS 伪元素**：不用 `::before`/`::after`（QSS 不支持），需要装饰性元素时用真实 HTML 元素
18. **不用 z-index 层叠**：QWidget 不支持 z-index，用布局顺序和父子关系控制层叠
19. **不用 CSS 变量传递到 Qt**：HTML 中可用 CSS 变量方便管理，但转换时必须替换为 ThemeManager 的实际色值，QSS 不支持变量

> 详见 `references/html-prototype-guide.md`

### Step 3: 用户调整 HTML

用户在浏览器中查看原型，提出调整意见。AI 按以下方式处理：

- 布局调整 → 修改 flex 方向/比例
- 尺寸调整 → 修改 width/height/flex
- 增删元素 → 添加/移除 HTML 元素
- 间距调整 → 修改 gap/padding/margin

**迭代直到用户对布局满意。**

### Step 4: 提取布局结构

从 HTML 中提取布局信息：
- 布局方向（垂直/水平/网格/表单）
- 比例关系（flex 值 → stretch factor）
- 分组关系（card → QGroupBox, nav+main → QSplitter）
- 特殊控件标注（dock/splitter/tab/stacked/toolbar）

> 详见 `references/html-qt-mapping.md`

### Step 5: 模式匹配 + 代码生成

1. 根据组件类型和布局结构，从模式库中选择最匹配的设计模式
2. 结合 HTML 布局信息和模式模板，生成 C++ 代码

**代码生成约定**：
- 头文件守卫用 `#pragma once`
- 类命名：XxxDialog / XxxPanel / XxxWidget
- 成员变量：`snake_case_` 尾下划线（与 qt-widget-architecture 规范一致）
- UI 初始化放在 `setupUi()` 私有方法中
- 信号槽连接放在 `connectSignals()` 私有方法中
- 使用新式 connect 语法
- 不混合业务逻辑——UI 类只管布局和交互转发

**子组件全面映射规则（关键！）**：

生成代码时，必须对 HTML 原型中的**每个视觉元素**逐一映射，不能遗漏任何子组件的样式和尺寸属性。这是确保 Qt 渲染与 HTML 原型高度一致的核心要求：

1. **逐元素扫描**：从 HTML 原型中提取所有元素（包括嵌套子元素），每个元素都必须有对应的 Qt 控件和 QSS 规则。不能只映射外层容器而忽略内部子组件。

2. **样式属性全面映射**：每个子组件的以下 CSS 属性必须映射到 QSS：
   - `background-color` → QSS `background-color`
   - `color` → QSS `color`
   - `font-size` / `font-weight` → QSS `font-size` / `font-weight`
   - `border` / `border-radius` → QSS `border` / `border-radius`
   - `padding` → `setContentsMargins()`（有布局时）或 QSS `padding`（无布局时）
   - `margin` → 外层布局 `addSpacing()` 或 `setContentsMargins()`
   - `gap` → `layout->setSpacing()`
   - `width` / `height` → `setFixedWidth()` / `setFixedHeight()` / `setMinimumWidth()` / `setMinimumHeight()`
   - `min-width` / `min-height` → `setMinimumWidth()` / `setMinimumHeight()`
   - `max-width` / `max-height` → `setMaximumWidth()` / `setMaximumHeight()`

3. **复合控件子组件映射**：HTML 中的复合 UI 模式（如筛选栏、消息气泡、卡片列表等），其内部每个子元素都必须单独创建 Qt 控件并设置样式：

   | HTML 复合模式 | 必须映射的子组件 |
   |--------------|----------------|
   | 筛选栏 | 下拉框、输入框、按钮、分隔线、标签 — 每个都要设 objectName + QSS |
   | 消息气泡 | 来源标签、时间标签、内容文本、气泡背景 — 每个都要设 objectName + QSS |
   | 卡片列表 | 卡片容器、标题、副标题、状态指示、操作按钮 — 每个都要设 objectName + QSS |
   | 工具栏 | 按钮组、分隔符、搜索框 — 每个都要设 objectName + QSS |
   | 状态栏 | 文本标签、图标、分隔线 — 每个都要设 objectName + QSS |
   | 滚动区域 | 滚动条（handle/add-line/sub-line/add-page/sub-page）、viewport — 每个都要设 QSS |
   | Tab 栏 | tab 按钮、选中指示器、内容区 — 每个都要设 QSS |

4. **滚动条必须映射**：HTML 原型中滚动条可能被浏览器默认隐藏，但 Qt 代码中**必须显式设置滚动条样式**，否则会显示系统默认样式（白色/灰色，与深色主题严重不协调）：
   ```cpp
   // 必须为每个 QScrollArea 设置滚动条样式
   QScrollBar:vertical { background: transparent; width: 8px; }
   QScrollBar::handle:vertical { background: #3a3f4b; border-radius: 4px; min-height: 30px; }
   QScrollBar::handle:vertical:hover { background: #4a4f5b; }
   QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
   QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
   ```

5. **QFrame 边框四边一致**：使用 QFrame 作为容器时，QSS border 必须四边统一颜色和宽度。如果需要模拟光照效果（顶部亮、底部暗），用子控件的背景色差异实现，不要用不同颜色的边框（Qt 渲染不一致）：
   ```cpp
   // ✅ 正确：四边统一
   #MessageLogWidget { border: 1px solid #4a4f5b; border-radius: 6px; }

   // ❌ 错误：四边不同色，Qt 渲染不一致
   #MessageLogWidget { border-top: 1px solid #5a5f6b; border-left: 1px solid #4a4f5b;
                       border-right: 1px solid #3a3f4b; border-bottom: 1px solid #2a2e36; }
   ```

6. **圆角容器子控件配合**：外层容器有 `border-radius` 时，子控件（如顶部筛选栏、底部状态栏）必须设置对应的圆角，否则子控件的直角会覆盖外层圆角：
   ```cpp
   // 外层容器圆角 6px
   #MessageLogWidget { border-radius: 6px; }
   // 顶部子控件配合顶部圆角
   #MessageFilterBar { border-top-left-radius: 6px; border-top-right-radius: 6px; }
   // 底部子控件配合底部圆角
   #MsgStatusBar { border-bottom-left-radius: 6px; border-bottom-right-radius: 6px; }
   ```

7. **布局边距与边框配合**：当容器有 border 时，主布局 `setContentsMargins()` 必须留出至少 1px 的边距，否则子控件会覆盖边框线：
   ```cpp
   // ✅ 正确：1px 边距防止子控件覆盖边框
   auto* layout = new QVBoxLayout(this);
   layout->setContentsMargins(1, 1, 1, 1);  // 为 1px border 留空间

   // ❌ 错误：子控件贴边覆盖边框
   layout->setContentsMargins(0, 0, 0, 0);
   ```

**QWidget 最佳实践（关键！）**：

生成代码时必须遵循以下 QWidget 开发最佳实践，确保代码质量和运行性能：

1. **样式表性能**：
   - 优先使用 QSS 选择器 `#objectName` 而非 `QObject::className`（后者触发遍历）
   - 样式表尽量设置在根容器上，利用 CSS 继承，避免每个子控件单独设置
   - 避免在循环或频繁调用的方法中 setStyleSheet()，样式表只在 setupUi() 中设置一次
   - 大量相同样式的控件，用 `setObjectName()` + 根容器 QSS 统一管理

2. **布局性能**：
   - 布局嵌套不超过 3 层，超过则拆分为自定义 Widget
   - 避免在 resizeEvent 中手动 setGeometry，始终用布局管理器
   - QScrollArea 必须 `setWidgetResizable(true)`，否则内容不跟随调整
   - 大量数据列表用 QListWidget/QTableWidget + 批量添加（`setUpdatesEnabled(false)` 包裹）

3. **控件选择**：
   - 只读文本用 QLabel 而非 QTextEdit（后者重很多）
   - 简单文本输入用 QLineEdit 而非 QTextEdit
   - 静态列表用 QListWidget 而非 QListView + Model（除非需要自定义 Model）
   - 频繁更新的数值显示用 QLabel.setText() 而非自定义绘制

4. **内存管理**：
   - 所有控件指定 parent 或加入布局（布局自动设 parent），避免内存泄漏
   - 不用 `new` 创建布局（`new QVBoxLayout(this)`），让 QWidget 接管
   - 对话框用栈创建或 `setAttribute(Qt::WA_DeleteOnClose)`

5. **信号槽优化**：
   - 避免信号槽循环连接（A→B→A）
   - 高频更新信号用 `Qt::QueuedConnection` 避免阻塞
   - 批量更新时先 `blockSignals(true)`，更新完再 `blockSignals(false)`

6. **QSS 可维护性**：
   - 样式表字符串提取为 `static const QString` 或 `constexpr` 常量
   - 颜色值提取为命名常量，方便主题切换
   - 复杂样式表拆分为多个 `const QString` 片段拼接

> 详见 `references/widget-patterns.md` 和对应的模板文件

### Step 5.5: 保真度校验（HTML → Qt 视觉一致性）

代码生成后、质量校验前，必须逐项检查 HTML 原型与 Qt 代码的视觉一致性。这是防止"原型好看但 Qt 渲染走样"的关键步骤。

**必须逐项检查以下 10 条保真度规则**（详见 `references/html-qt-fidelity.md`）：

1. **QSS padding 与 layout margins 不叠加**：有布局的 QWidget，QSS 中不写 `padding`，只用 `setContentsMargins()`
2. **`:hover` 需要 `WA_Hover`**：使用 QSS `:hover` 的自定义 QWidget/QFrame 子类，必须 `setAttribute(Qt::WA_Hover)`
3. **属性选择器需要 `Q_PROPERTY`**：QSS `[prop=value]` 匹配的自定义属性，必须用 `Q_PROPERTY` 声明
4. **QLabel 小元素需 `setFixedSize()`**：状态点、徽章等小尺寸 QLabel，必须设置精确尺寸
5. **样式继承不断裂**：子控件单独 `setStyleSheet()` 会覆盖继承的样式，优先在根容器集中管理
6. **`setFixedHeight` vs `setMinimumHeight`**：卡片/列表项用 `setFixedHeight()`，内容区域用 `setMinimumHeight()`
7. **分隔线用 QFrame**：不用 QSS `border-bottom`，用独立的 `QFrame(HLine)` 做分隔线
8. **颜色值与 ThemeManager 一致**：Qt 代码中的颜色必须来自 ThemeManager，不能硬编码
9. **每个 QWidget 显式设置背景色**：不能只设父控件，子控件默认透明会显示系统色
10. **字号微调**：Qt 中 ≤11px 字号可能比 HTML 偏小，必要时增大 1px

**校验方式**：对照 HTML 原型，逐条检查生成的 C++ 代码是否违反上述规则。发现违反立即修正，再进入 Step 6。

### Step 6: 质量校验

生成代码后，按以下清单逐项自查：

**布局合理性**：
- [ ] 布局嵌套不超过 3 层
- [ ] 弹性区域设置了 stretch factor
- [ ] 间距和边距使用标准值（8/12/16px）
- [ ] 没有使用固定像素尺寸（用 minimumSize + stretch 代替）
- [ ] QScrollArea 包裹了可能超长的内容

**模式一致性**：
- [ ] 选择了正确的设计模式
- [ ] 布局结构与模式描述一致

**代码质量**：
- [ ] UI 初始化在 setupUi() 中
- [ ] 信号槽连接在 connectSignals() 中
- [ ] 没有在 UI 类中混入业务逻辑
- [ ] 成员变量命名 snake_case_
- [ ] 使用新式 connect 语法
- [ ] 对话框通过信号返回数据

**可维护性**：
- [ ] 复杂布局拆分为子 Widget
- [ ] 魔法数字提取为命名常量
- [ ] 控件对象有有意义的变量名

**样式质量**：
- [ ] QSS 使用 `#objectName` 选择器
- [ ] 样式表设置在根容器上
- [ ] 运行时样式切换用 setProperty() + polish/unpolish
- [ ] 没有使用 QSS 不支持的属性（box-shadow、text-shadow 等）

**保真度（HTML → Qt 一致性）**：
- [ ] 有布局的 QWidget，QSS 中没有 `padding`（只用 `setContentsMargins()`）
- [ ] 使用 QSS `:hover` 的自定义控件已设置 `setAttribute(Qt::WA_Hover)`
- [ ] QSS 属性选择器 `[prop=value]` 匹配的属性已用 `Q_PROPERTY` 声明
- [ ] 小尺寸 QLabel（状态点、徽章）已设置 `setFixedSize()`
- [ ] 分隔线使用独立 `QFrame(HLine)`，不用 QSS `border-bottom`
- [ ] 每个可见 QWidget 都显式设置了背景色
- [ ] 颜色值来自 ThemeManager，没有硬编码色值
- [ ] 卡片/列表项使用 `setFixedHeight()`，内容区域使用 `setMinimumHeight()`

> 详见 `references/quality-checklist.md`

### Step 7: 样式优化

代码生成后，根据用户的样式需求进行视觉优化：

#### 7.1 主题系统

当项目需要深色/浅色主题切换时，提供 ThemeManager 单例：

```cpp
// ui/style/ThemeManager.h
#pragma once
#include <QObject>
#include <QColor>
#include <QHash>

class ThemeManager : public QObject {
    Q_OBJECT
public:
    enum class Theme { Light, Dark, System };
    Q_ENUM(Theme)

    static ThemeManager* Instance();

    void SetTheme(Theme theme);
    Theme CurrentTheme() const;

    QColor ThemeColor(const QString& name) const;
    QColor PrimaryColor() const;
    QColor BackgroundColor() const;
    QColor SurfaceColor() const;
    QColor TextColor() const;
    QColor ErrorColor() const;

    int BorderRadius() const;
    int Padding() const;

signals:
    void ThemeChanged(Theme theme);

private:
    explicit ThemeManager(QObject* parent = nullptr);
    void LoadTheme(Theme theme);
    void ApplyStylesheet();

    Theme current_theme_ = Theme::Light;
    QHash<QString, QColor> colors_;
    QHash<QString, int> dimensions_;
};
```

**主题色板**（Material Design 风格）：

| 角色 | 浅色模式 | 深色模式 |
|------|---------|---------|
| primary | #6200EE | #BB86FC |
| secondary | #03DAC6 | #03DAC6 |
| background | #FFFFFF | #121212 |
| surface | #FFFFFF | #1E1E1E |
| error | #B00020 | #CF6679 |
| onPrimary | #FFFFFF | #000000 |
| onBackground | #000000 | #FFFFFF |
| onSurface | #000000 | #FFFFFF |

> 完整主题文件见 `references/themes/modern-dark.qss` 和 `references/themes/modern-light.qss`

#### 7.2 QSS 样式编写

样式表编写遵循以下规则：

1. **选择器优先级**：`#objectName` > `.className` > `QObject::className` > 后代选择器
2. **集中设置**：在根容器 `setStyleSheet()` 一次性设置，利用 CSS 继承
3. **运行时切换**：用 `setProperty()` + `style()->unpolish()/polish()` 而非重新 `setStyleSheet()`
4. **性能禁忌**：不用后代选择器链、不在循环中调用 setStyleSheet、不用 QSS 渐变

```cpp
// ✅ 高性能：ID 选择器 + 根容器集中设置
void StatusPanel::setupUi() {
    setObjectName("statusPanel");
    setStyleSheet(R"(
        #statusPanel { background-color: #1e1e1e; }
        #fieldLabel { color: #9ca3b0; font-size: 12px; }
        #valueLabel { color: #ffffff; font-size: 20px; font-weight: bold; }
    )");
}

// ✅ 运行时样式切换
void StatusPanel::UpdateStatus(bool running) {
    auto* label = value_labels_["status"];
    label->setProperty("statusClass", running ? "running" : "stopped");
    label->style()->unpolish(label);
    label->style()->polish(label);
}
```

> 完整 QSS 属性参考见 `references/qss-reference.md`

#### 7.3 自定义控件样式

当标准 QSS 无法满足视觉需求时，通过 `paintEvent()` 自定义绘制：

> **阴影实现方式选择**：
> - **QPainter 手绘**（推荐）：性能好，完全控制渲染，适合大量卡片场景
> - **QGraphicsDropShadowEffect**：实现简单，但性能开销较大（每帧重绘），适合少量卡片或静态布局

```cpp
// ui/widgets/CardWidget.h — 带阴影的卡片控件
class CardWidget : public QFrame {
    Q_OBJECT
    Q_PROPERTY(int elevation READ Elevation WRITE SetElevation)

public:
    explicit CardWidget(QWidget* parent = nullptr);

    int Elevation() const { return elevation_; }
    void SetElevation(int elevation);

protected:
    void paintEvent(QPaintEvent* event) override;

private:
    int elevation_ = 1;
};
```

```cpp
// ui/widgets/CardWidget.cpp
void CardWidget::paintEvent(QPaintEvent* event) {
    QPainter painter(this);
    painter.setRenderHint(QPainter::Antialiasing);

    // 绘制阴影层（通过 QPainter，非 QSS box-shadow）
    if (elevation_ > 0) {
        QColor shadow_color(0, 0, 0, 30 + elevation_ * 10);
        painter.setPen(Qt::NoPen);
        painter.setBrush(shadow_color);
        painter.drawRoundedRect(rect().adjusted(2, 2, -2, -2), 8, 8);
    }

    // 绘制背景
    painter.setBrush(ThemeManager::Instance()->SurfaceColor());
    painter.setPen(QPen(ThemeManager::Instance()->ThemeColor("divider"), 1));
    painter.drawRoundedRect(rect().adjusted(0, 0, -4, -4), 8, 8);
}
```

> 更多自定义控件样式见 `references/custom-widgets.md`

#### 7.4 动画效果

使用 QPropertyAnimation 实现动画，**不用 CSS 动画/过渡**：

```cpp
// ui/animation/AnimationUtils.h
class AnimationUtils {
public:
    static QPropertyAnimation* FadeIn(QWidget* widget, int duration = 300);
    static QPropertyAnimation* FadeOut(QWidget* widget, int duration = 300);
    static QPropertyAnimation* SlideIn(QWidget* widget, Qt::Edge from, int duration = 300);
    static QPropertyAnimation* Scale(QWidget* widget, qreal from, qreal to, int duration = 200);
};
```

**动画使用原则**：
1. 动画持续时间 200-400ms，不超过 500ms
2. 使用 `QEasingCurve::InOutQuad` 缓动曲线
3. 动画对象指定 parent 或连接 `finished` → `deleteLater`
4. 不在动画回调中做耗时操作

> 完整动画模式库见 `references/animation-patterns.md`

#### 7.5 高 DPI 适配

Qt 6 自动处理高 DPI 缩放，无需手动配置。注意事项：

```cpp
// main.cpp — Qt 6 无需额外配置
int main(int argc, char* argv[]) {
    QApplication app(argc, argv);
    // Qt 6 自动启用高 DPI 缩放
    // 不要手动设置 Qt::AA_EnableHighDpiScaling（Qt 6 中已废弃）

    MainWindow window;
    window.show();
    return app.exec();
}
```

**高 DPI 注意事项**：
1. 图标和图片提供 `@2x` / `@3x` 版本
2. 不用固定像素尺寸，用 `minimumSize` + `sizePolicy`
3. QSS 中的 `px` 值会被 Qt 自动缩放
4. 自定义 `paintEvent()` 中使用 `devicePixelRatio()` 处理位图

### Step 8: 定点微调

用户对 C++ 代码提出调整意见时，按以下流程处理：

1. **解析反馈**：判断属于哪类调整
2. **定位代码**：找到需要修改的成员变量和 setupUi() 中的对应代码行
3. **制定改动方案**：列出需要修改的具体位置和内容（不超过 3 处）
4. **执行修改**：用 Edit 工具定点修改，不重写整个文件
5. **局部校验**：只校验受影响的校验项
6. **简要说明**：告诉用户改了什么、为什么这样改

**调整类型**：

| 调整类型 | 调整策略 |
|---------|---------|
| 布局调整 | 修改 stretch/调换控件顺序/更换布局类型 |
| 尺寸调整 | 修改 minimumSize/sizePolicy/stretch |
| 增删控件 | insertWidget/removeWidget |
| 控件替换 | 替换控件类型，保持布局位置和信号不变 |
| 间距调整 | 修改 spacing/contentsMargins/addStretch |
| 结构重组 | 提取子 Widget/包裹 QGroupBox |
| 样式调整 | 修改 QSS 属性/切换 property class/调整 ThemeManager 色板 |
| 动画调整 | 修改 duration/easing curve/添加或移除动画 |

**调整原则**：最小改动、定位精准、校验局部

**迭代终止**：用户满意 / 用户提出新需求 / 超过 5 轮（建议重新审视需求）

---

## 核心规则摘要

### 布局规则

| 规则 | 说明 |
|------|------|
| 布局选择 | 表单用 QFormLayout，列表用 QVBoxLayout+QScrollArea，工具栏+内容用 QSplitter |
| 嵌套深度 | 不超过 3 层，超过则拆分为自定义 Widget |
| 间距规范 | 控件间 8px，分组间 16px，窗口边距 12px |
| 拉伸策略 | 固定高度控件 stretch=0，弹性区域 stretch=1 |
| 尺寸约束 | 输入框最小宽度 200px，按钮最小宽度 80px，列表最小高度 150px |
| 对齐规则 | 标签右对齐，按钮组右对齐或居中 |

> 详见 `references/layout-rules.md`

### 样式规则

| 规则 | 说明 |
|------|------|
| 选择器 | 优先 `#objectName`，避免类选择器和后代选择器 |
| 集中设置 | 在根容器 setStyleSheet()，利用 CSS 继承 |
| 运行时切换 | setProperty() + unpolish/polish，不重新 setStyleSheet() |
| 纯色优先 | 不用 QSS 渐变，纯色背景性能最佳 |
| 圆角限制 | border-radius ≤ 6px，大圆角性能差 |
| 动画 | 用 QPropertyAnimation，不用 CSS animation/transition |

### 设计模式索引

| # | 模式 | 适用场景 | 核心布局 | 模板文件 |
|---|------|---------|---------|---------|
| 1 | 表单模式 | 设置、属性编辑、登录 | QFormLayout + 按钮组 | dialog-templates.md |
| 2 | 列表+详情模式 | 主从浏览、邮件、文件管理 | QSplitter(列表\|详情) | panel-templates.md |
| 3 | 工具栏+内容模式 | 编辑器、查看器 | QToolBar + QStackedWidget | panel-templates.md |
| 4 | 选项卡模式 | 多功能面板、设置中心 | QTabWidget | panel-templates.md |
| 5 | 树形导航+内容模式 | 项目管理、资源浏览器 | QTreeView + 右侧内容区 | mainwindow-templates.md |
| 6 | 向导模式 | 安装、配置、导入导出 | QStackedWidget + 步骤指示 | dialog-templates.md |
| 7 | 状态面板模式 | 仪表盘、监控 | QGridLayout 卡片网格 | panel-templates.md |
| 8 | 停靠窗口模式 | IDE、调试器 | QMainWindow + QDockWidget | mainwindow-templates.md |

> 详见 `references/widget-patterns.md`

---

## 与其他 Skills 的协作

- 生成 UI 代码时遵循 **qt-widget-architecture** 的分层规范（UI 类不包含业务逻辑）
- 代码审查引导用户使用 **qt-cpp-review**

---

## 参考资源

| 主题 | 参考文件 |
|------|----------|
| HTML→Qt 保真度规则 | `references/html-qt-fidelity.md` |
| HTML 原型指南 | `references/html-prototype-guide.md` |
| HTML→Qt 映射 | `references/html-qt-mapping.md` |
| 布局规则 | `references/layout-rules.md` |
| 控件模式 | `references/widget-patterns.md` |
| 对话框模板 | `references/dialog-templates.md` |
| 面板模板 | `references/panel-templates.md` |
| 主窗口模板 | `references/mainwindow-templates.md` |
| 自定义控件模板 | `references/custom-widget-templates.md` |
| 质量校验清单 | `references/quality-checklist.md` |
| QSS 属性参考 | `references/qss-reference.md` |
| 自定义控件样式 | `references/custom-widgets.md` |
| 动画模式库 | `references/animation-patterns.md` |
| 深色主题 | `references/themes/modern-dark.qss` |
| 浅色主题 | `references/themes/modern-light.qss` |
