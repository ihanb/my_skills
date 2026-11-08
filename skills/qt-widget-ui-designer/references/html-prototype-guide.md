# HTML 视觉原型生成指南

指导 AI 生成用于快速验证布局的 HTML/CSS 原型页面。核心原则：**HTML 原型必须模拟 QWidget 的渲染特征，确保视觉预览效果能被 QWidget 代码 1:1 还原。**

## 1. 生成约束

### 必须遵守（布局约束）

1. **只用 flexbox/grid 布局** — 不用 float、position:absolute、display:inline-block
2. **只用语义化标签** — 用 `<form>`、`<nav>`、`<main>` 等，不用纯 `<div>` 套 `<div>`
3. **用注释标注 Qt 特殊控件** — `<!-- dock -->`, `<!-- splitter -->` 等
4. **不用 CSS 动画/过渡** — 动画效果在 Qt 中用 QPropertyAnimation 实现
5. **允许基础交互 JavaScript** — HTML 原型中可使用简单的 JS 实现交互预览（Tab 切换、按钮状态切换、列表选中、显示/隐藏等），让用户在浏览器中能真实体验交互流程。JS 仅用于原型演示，不映射到 Qt 代码（Qt 中用信号槽实现）。详见第 6 章。

### 必须遵守（QWidget 风格约束）

HTML 原型是 QWidget 的视觉预览，不是 Web 页面。必须遵循以下约束确保原型效果可被 Qt 还原：

6. **禁用 CSS 特效**（与 SKILL.md Step 2 的禁用清单一致）：
   - 不用 `box-shadow`、`text-shadow`（QSS 无这些属性）
   - 不用 `backdrop-filter`、`filter`、`opacity`（QSS 不支持；透明度只能靠自定义绘制）
   - 不用 `border-image`（QSS 语法不同，易出错）
   - 不用 `linear-gradient` / `radial-gradient` 及其叠加（QSS 渐变语法受限且性能差）
   - 不用 `transform`、`transition` / `animation`、`clip-path`
   - 不用 `position: absolute/fixed`、`float`、`z-index`、`::before` / `::after` 伪元素
   - HTML 原型中可用 `border-bottom` 表达视觉分隔，但转换到 Qt 时必须改为独立的
     `QFrame(HLine)`，而非 QSS `border-bottom`

7. **交互态与 Web 专属样式**：
   - **允许**用 `:hover` / `.active` / `[selected]` 表达**静态**交互态预览，便于演示；
     但每处必须加注释 `<!-- hover-state -->` 或 `<!-- state: selected -->`，
     且**禁止**搭配 `transition` / 缩放 / 阴影做动画。Qt 侧对应
     `setAttribute(Qt::WA_Hover)` + QSS 伪状态，或 `Q_PROPERTY` + 属性选择器
     （见 `html-qt-fidelity.md` 第 2、3 章）。主题 qss 里的 `:hover` 是 Qt 侧实现，与本条不冲突。
   - 不用 `cursor` 样式（Qt 使用 `setCursor()` API）
   - 不用 CSS `outline` 画焦点框或装饰线——QSS **只支持 `outline: none`** 清除焦点矩形
     （两份 `themes/*.qss` 正是这么用的），不支持自定义 outline 样式；焦点态用 QSS `:focus` + `border`
   - 不用 `user-select`（Qt 使用 `setTextInteractionFlags()`）

8. **边框规范**：
   - 只用 `border: 1px solid #color`（实线 + 纯色）
   - 不用虚线 `dashed`/`dotted`（QSS 中表现不一致）
   - 不用双线 `double`（QSS 不支持）
   - 不用圆角渐变边框（QSS 无法实现）

9. **圆角有限使用**：
   - 推荐 `border-radius: 4px` 或 `6px`
   - 主操作按钮、卡片容器等可放宽至 `8px`
   - 避免 `>12px` 的大圆角，QSS 大圆角会导致渲染性能下降
   - 不用 `border-radius: 50%`（圆形），Qt 中用 QIcon 或自定义绘制

10. **颜色用纯色**：
    - 只用 `background-color: #hex` 或 `background: #hex`
    - 不用 `linear-gradient`/`radial-gradient`（QSS 渐变语法与 CSS 不同，且性能差）
    - 如需区分层次，用不同深浅的纯色块模拟

11. **字体用系统字体**：
    - `font-family: "Segoe UI", "Microsoft YaHei", sans-serif`
    - 不用 Web 字体/Google Fonts（Qt 无法加载）
    - 不用 `@font-face`

12. **图标用文字/Unicode 占位**：
    - HTML 原型不用内联 SVG 图标、不用 CSS icon font（Font Awesome 等）
    - 占位示例：`▶` 启动、`■` 停止、`⚙` 设置、`✕` 关闭
    - **Qt 侧允许且推荐** `QIcon(QStringLiteral(":/icons/search.svg"))`（QtSvg 标准做法，
      高 DPI 友好），也可用 `QIcon::fromTheme()`。这与「QSS data URI SVG 仅全局主题
      checkbox/radio indicator 可用、运行时动态 `setStyleSheet()` 禁用」是**两条独立规则**，
      不要因为原型用了文字占位就禁止 Qt 使用 SVG 图标资源

13. **间距用像素值**：
    - 只用 `8px/12px/16px` 标准值
    - 不用 `em/rem/vw/vh/%`（Qt 布局基于像素，百分比无法直接映射）
    - `gap: 8px` → `layout->setSpacing(8)`

14. **不用 CSS Grid 复杂特性**：
    - 不用 `grid-template-areas`（QGridLayout 无此概念）
    - 不用 `subgrid`（Qt 不支持）
    - 不用 `auto-fill`/`auto-fit`（Qt 中需手动计算列数）
    - 简单网格用 `display: grid; grid-template-columns: 1fr 1fr 1fr` 即可

15. **模拟 QWidget 默认尺寸策略**：
    - 输入框宽度用 `flex: 1` 而非 `width: 100%`（对应 `QSizePolicy::Expanding`）
    - 按钮用 `min-width: 80px` 而非 `width: 80px`（对应 `setMinimumWidth()`）
    - 固定高度区域用 `min-height` 而非 `height`（对应 `setMinimumHeight()`）
    - 弹性区域用 `flex: 1` 而非 `height: 100%`（对应 `stretch=1`）

## 2. CSS 变量约定

CSS 变量用于定义标准间距和颜色，方便后续映射到 Qt 常量。

**关键规则：颜色变量必须使用项目 ThemeManager 的实际色值，不能用通用色值。** 生成 HTML 前必须先读取项目 `ThemeManager::LoadTheme()` 中的色值定义。

### 2.1 间距变量（固定规范）

```css
:root {
    /* 间距 — 映射到 Qt 布局参数 */
    --spacing-sm: 8px;    /* 同组控件间距 → layout->setSpacing(8) */
    --spacing-md: 12px;   /* 窗口内边距 → layout->setContentsMargins(12,12,12,12) */
    --spacing-lg: 16px;   /* 分组间距 → addSpacing(16) */

    /* 最小尺寸 — 映射到 setMinimumWidth/setMinimumHeight */
    --min-input-width: 200px;
    --min-button-width: 80px;
    --min-list-height: 150px;

    /* 圆角 — 映射到 QSS border-radius，推荐 4px/6px，按钮/卡片可放宽至 8px */
    --border-radius: 4px;
}
```

### 2.2 颜色变量（必须来自 ThemeManager）

**生成 HTML 原型前，先按 Step 1.5 / `references/theme-manager.md` 第 1 节确定色板来源**，
再把每个 `colors_[key]` 映射为同名 CSS 变量。色板的**唯一事实源**是
`references/theme-manager.md` 第 2 节；下面是它 **Dark 列**的展开（Light 列见该文件）：

```css
:root {
    /* 颜色 — 必须与 ThemeManager 完全一致，禁止使用通用色值 */
    --primary: #6200EE;           /* ThemeManager colors_["primary"] */
    --background: #121212;        /* ThemeManager colors_["background"] */
    --surface: #1E1E1E;           /* ThemeManager colors_["surface"] */
    --surface_variant: #2C2C2C;   /* ThemeManager colors_["surface_variant"] */
    --on_background: #FFFFFF;     /* ThemeManager colors_["on_background"] */
    --on_primary: #000000;        /* ThemeManager colors_["on_primary"] */
    --on_surface_secondary: #AAAAAA; /* ThemeManager colors_["on_surface_secondary"] */
    --on_surface_muted: #666666;  /* ThemeManager colors_["on_surface_muted"] */
    --error: #CF6679;             /* ThemeManager colors_["error"] */
    --success: #66BB6A;           /* ThemeManager colors_["success"] */
    --warning: #FFA726;           /* ThemeManager colors_["warning"] */
    --border: #333333;            /* ThemeManager colors_["border"] */
    --divider: #2C2C2C;           /* ThemeManager colors_["divider"] */
    --hover_overlay: #2C2C2C;     /* ThemeManager colors_["hover_overlay"] */
    --selected_bg: #3A2F4A;       /* ThemeManager colors_["selected_bg"] */
}
```

**禁止行为**：
- ❌ 硬编码与 `ThemeManager::ThemeColor(key)` 不一致的字面量（即便它碰巧是色板里的合法值）
- ❌ 项目没有色板时，凭感觉从 Material Design / Tailwind 等第三方设计系统抓一组色值
- ❌ 变量名与 `colors_` 的 key 不一致（如自造 `--bg` / `--card`），导致转换时无法一一对应

**正确做法**：
- ✅ 按 Step 1.5 三分支确定色板：读项目 `LoadTheme()` / 先 Bootstrap ThemeManager / 用用户色板覆盖同名 key
- ✅ 将每个 `colors_[key]` 映射为 `--key` CSS 变量
- ✅ HTML 中所有颜色引用都使用 CSS 变量，不硬编码

> **注意**：颜色变量只用纯色 `#hex`，不用渐变。间距变量只用像素值，不用 em/rem。

## 3. 基础 HTML 模板

模板遵循 QWidget 风格约束：纯色背景、实线边框、推荐 4px/6px 圆角（按钮/卡片可 8px）、系统字体、像素间距。

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{ComponentName} - UI Prototype</title>
    <style>
        :root {
            /* 间距 */
            --spacing-sm: 8px;
            --spacing-md: 12px;
            --spacing-lg: 16px;
            --min-input-width: 200px;
            --min-button-width: 80px;
            --border-radius: 4px;

            /* 颜色 — 取自 references/theme-manager.md 第 2 节 Dark 列；
               实际生成时按 Step 1.5 读到的色板逐 key 覆盖，key 名不可自造 */
            --primary: #6200EE;
            --background: #121212;
            --surface: #1E1E1E;
            --surface_variant: #2C2C2C;
            --on_background: #FFFFFF;
            --on_primary: #000000;
            --on_surface_secondary: #AAAAAA;
            --on_surface_muted: #666666;
            --error: #CF6679;
            --success: #66BB6A;
            --warning: #FFA726;
            --border: #333333;
            --divider: #2C2C2C;
            --hover_overlay: #2C2C2C;
            --selected_bg: #3A2F4A;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
            font-size: 14px;
            color: var(--on_background);
            background: var(--background);
        }

        .card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--border-radius);
            padding: var(--spacing-md);
        }

        input, select, textarea {
            min-width: var(--min-input-width);
            padding: 6px 8px;
            border: 1px solid var(--border);
            border-radius: var(--border-radius);
            background: var(--surface_variant);
            color: var(--on_background);
            font-family: inherit;
            font-size: 14px;
        }

        button {
            min-width: var(--min-button-width);
            padding: 6px 16px;
            border: 1px solid var(--border);
            border-radius: var(--border-radius);
            background: var(--surface_variant);
            color: var(--on_background);
            font-family: inherit;
            font-size: 14px;
        }

        button.primary {
            background: var(--primary);
            color: var(--on_primary);
            border-color: var(--primary);
        }

        label {
            display: inline-block;
            text-align: right;
            min-width: 80px;
        }
    </style>
</head>
<body>
    <!-- 布局内容 -->
</body>
</html>
```

## 4. 组件类型模板

### 对话框模板

```html
<div style="display: flex; flex-direction: column; gap: var(--spacing-lg); padding: var(--spacing-md); max-width: 500px; background: var(--surface); margin: 20px auto;">
    <h2>对话框标题</h2>

    <form style="display: flex; flex-direction: column; gap: var(--spacing-sm);">
        <div style="display: flex; gap: var(--spacing-sm); align-items: center;">
            <label>字段1:</label>
            <input type="text" placeholder="请输入..." style="flex: 1;">
        </div>
        <div style="display: flex; gap: var(--spacing-sm); align-items: center;">
            <label>字段2:</label>
            <select style="flex: 1;">
                <option>选项1</option>
                <option>选项2</option>
            </select>
        </div>
    </form>

    <div style="display: flex; justify-content: flex-end; gap: var(--spacing-sm);">
        <button>取消</button>
        <button class="primary">确定</button>
    </div>
</div>
```

### 列表+详情模板

```html
<div style="display: flex; height: 500px; background: var(--surface);">
    <!-- splitter -->
    <nav style="min-width: 180px; max-width: 300px; border-right: 1px solid var(--border); display: flex; flex-direction: column;">
        <div style="padding: var(--spacing-sm); border-bottom: 1px solid var(--divider);">
            <input type="text" placeholder="搜索..." style="width: 100%;">
        </div>
        <ul style="flex: 1; list-style: none; overflow-y: auto; padding: var(--spacing-sm);">
            <li style="padding: 8px; background: var(--selected_bg); border-radius: var(--border-radius);">项目 1</li>
            <li style="padding: 8px;">项目 2</li>
            <li style="padding: 8px;">项目 3</li>
        </ul>
    </nav>

    <main style="flex: 1; padding: var(--spacing-md); display: flex; flex-direction: column; gap: var(--spacing-md);">
        <h2>详情标题</h2>
        <form style="display: flex; flex-direction: column; gap: var(--spacing-sm);">
            <div style="display: flex; gap: var(--spacing-sm); align-items: center;">
                <label>属性1:</label>
                <input type="text" style="flex: 1;" value="值1">
            </div>
            <div style="display: flex; gap: var(--spacing-sm); align-items: center;">
                <label>属性2:</label>
                <input type="text" style="flex: 1;" value="值2">
            </div>
        </form>
    </main>
</div>
```

### 主窗口模板

```html
<div style="display: flex; flex-direction: column; height: 600px; background: var(--background);">
    <!-- toolbar -->
    <header style="display: flex; gap: 4px; padding: 4px 8px; background: var(--surface); border-bottom: 1px solid var(--border);">
        <!-- toolbar -->
        <button>新建</button>
        <button>打开</button>
        <button>保存</button>
        <span style="flex: 1;"></span>
        <button>设置</button>
    </header>

    <div style="flex: 1; display: flex;">
        <!-- dock: left -->
        <aside style="min-width: 200px; max-width: 300px; background: var(--surface); border-right: 1px solid var(--border); display: flex; flex-direction: column;">
            <h3 style="padding: 8px; margin: 0; border-bottom: 1px solid var(--divider);">导航</h3>
            <ul style="flex: 1; list-style: none; padding: 8px; overflow-y: auto;">
                <li style="padding: 4px 8px;">▸ 项目1</li>
                <li style="padding: 4px 8px;">▸ 项目2</li>
            </ul>
        </aside>

        <!-- central widget -->
        <main style="flex: 1; display: flex; flex-direction: column; background: var(--surface);">
            <div style="flex: 1; display: flex; align-items: center; justify-content: center; color: var(--on_surface_muted);">
                主内容区域
            </div>
        </main>

        <!-- dock: right -->
        <aside style="min-width: 220px; max-width: 320px; background: var(--surface); border-left: 1px solid var(--border); display: flex; flex-direction: column;">
            <h3 style="padding: 8px; margin: 0; border-bottom: 1px solid var(--divider);">属性</h3>
            <div style="padding: 8px; flex: 1; overflow-y: auto;">
                <form style="display: flex; flex-direction: column; gap: var(--spacing-sm);">
                    <div style="display: flex; gap: 4px; align-items: center;">
                        <label style="min-width: 60px;">名称:</label>
                        <input type="text" style="flex: 1;" value="属性值">
                    </div>
                </form>
            </div>
        </aside>
    </div>

    <!-- statusbar -->
    <footer style="padding: 4px 8px; background: var(--surface); border-top: 1px solid var(--border); font-size: 12px; color: var(--on_surface_secondary);">
        <!-- statusbar -->就绪
    </footer>
</div>
```

### 仪表盘模板

```html
<div style="display: flex; flex-direction: column; gap: var(--spacing-lg); padding: var(--spacing-md);">
    <h1>监控面板</h1>

    <div style="display: flex; gap: var(--spacing-md);">
        <div class="card" style="flex: 1; text-align: center;">
            <div style="font-size: 12px; color: var(--on_surface_secondary);">CPU</div>
            <div style="font-size: 28px; font-weight: bold;">45%</div>
        </div>
        <div class="card" style="flex: 1; text-align: center;">
            <div style="font-size: 12px; color: var(--on_surface_secondary);">内存</div>
            <div style="font-size: 28px; font-weight: bold;">60%</div>
        </div>
        <div class="card" style="flex: 1; text-align: center;">
            <div style="font-size: 12px; color: var(--on_surface_secondary);">磁盘</div>
            <div style="font-size: 28px; font-weight: bold;">30%</div>
        </div>
    </div>

    <div class="card" style="flex: 1; min-height: 200px;">
        <h3>趋势图</h3>
        <div style="min-height: 150px; background: var(--surface_variant); border-radius: var(--border-radius); display: flex; align-items: center; justify-content: center; color: var(--on_surface_muted);">
            图表区域
        </div>
    </div>
</div>
```

## 5. 原型调整指南

用户提出调整时，按以下方式修改 HTML：

| 用户说 | HTML 修改 |
|-------|----------|
| "左边太窄" | 增大左侧 min-width 或 flex 值 |
| "控件太挤" | 增大 gap 值 |
| "留白不够" | 增大 padding 值 |
| "加个搜索框" | 在对应位置添加 `<input type="text" placeholder="搜索...">` |
| "换成一排" | 将 `flex-direction: column` 改为 `row` |
| "加个分组" | 用 `<fieldset>` 或 `<div class="card">` 包裹 |

## 6. JavaScript 交互模式

HTML 原型中的 JavaScript **仅用于交互预览**，让用户在浏览器中能真实体验交互流程。这些 JS 代码**不映射到 Qt 代码**，Qt 中用信号槽机制实现相同逻辑。

### 原则

1. **JS 只做 UI 状态切换**：显示/隐藏、class 切换、文本替换
2. **不做业务逻辑**：不调用 API、不处理数据、不做计算
3. **代码内联在 `<script>` 标签中**：不引入外部 JS 库
4. **用 `data-` 属性标记交互元素**：方便识别和绑定事件
5. **每个交互模式用独立函数**：保持代码简洁可读

### 6.1 Tab 切换

对应 Qt：`QTabWidget` 的 `currentChanged` 信号

```html
<nav class="tab-bar">
    <div class="tab-item active" data-tab="control" onclick="switchTab('control')">控制</div>
    <div class="tab-item" data-tab="config" onclick="switchTab('config')">配置</div>
</nav>

<section class="tab-content" data-tab-content="control">控制面板内容</section>
<section class="tab-content" data-tab-content="config" style="display:none;">配置面板内容</section>

<script>
function switchTab(tabId) {
    // 切换 tab 激活状态
    document.querySelectorAll('[data-tab]').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabId);
    });
    // 切换内容显示
    document.querySelectorAll('[data-tab-content]').forEach(content => {
        content.style.display = content.dataset.tabContent === tabId ? '' : 'none';
    });
}
</script>
```

### 6.2 按钮状态切换（启动/停止）

对应 Qt：`QPushButton::setEnabled()` + 信号槽

```html
<div class="action-bar">
    <button id="startBtn" onclick="toggleRunning(true)">&#9654; 启动</button>
    <button id="stopBtn" onclick="toggleRunning(false)" disabled>&#9632; 停止</button>
    <button id="restartBtn" onclick="restart()" disabled>&#8635; 重启</button>
</div>

<script>
let isRunning = false;

function toggleRunning(running) {
    isRunning = running;
    document.getElementById('startBtn').disabled = running;
    document.getElementById('stopBtn').disabled = !running;
    document.getElementById('restartBtn').disabled = !running;

    // 更新状态徽章
    const badge = document.getElementById('statusBadge');
    if (running) {
        badge.className = 'status-badge online';
        badge.innerHTML = '<span class="dot"></span>运行中';
    } else {
        badge.className = 'status-badge offline';
        badge.innerHTML = '<span class="dot"></span>离线';
    }
}

function restart() {
    toggleRunning(false);
    setTimeout(() => toggleRunning(true), 300);
}
</script>
```

### 6.3 列表项选中

对应 Qt：`QListWidget::currentItemChanged` 信号

```html
<ul class="item-list">
    <li class="item active" onclick="selectItem(this)">项目 1</li>
    <li class="item" onclick="selectItem(this)">项目 2</li>
    <li class="item" onclick="selectItem(this)">项目 3</li>
</ul>

<script>
function selectItem(el) {
    document.querySelectorAll('.item-list .item').forEach(item => {
        item.classList.remove('active');
        item.style.background = '';
    });
    el.classList.add('active');
    el.style.background = 'var(--selected_bg)';
}
</script>
```

### 6.4 显示/隐藏切换

对应 Qt：`QWidget::setVisible()` / `QStackedWidget::setCurrentIndex()`

```html
<button onclick="togglePanel('detailPanel')">显示详情</button>
<div id="detailPanel" style="display:none;">详情内容</div>

<script>
function togglePanel(id) {
    const panel = document.getElementById(id);
    panel.style.display = panel.style.display === 'none' ? '' : 'none';
}
</script>
```

### 6.5 空状态/内容状态切换

对应 Qt：`QStackedWidget` 切换 empty/content 页面

```html
<div id="emptyState" class="empty-state">
    <span class="icon">&#9881;</span>
    <span class="text">选择或创建一个设备</span>
</div>
<div id="contentState" class="content" style="display:none;">
    <!-- 实际内容 -->
</div>

<script>
function showContent(show) {
    document.getElementById('emptyState').style.display = show ? 'none' : '';
    document.getElementById('contentState').style.display = show ? '' : 'none';
}
</script>
```

### 6.6 表单交互（添加/删除行）

对应 Qt：`QTableWidget::insertRow()` / `removeRow()`

```html
<table id="fieldTable">
    <thead><tr><th>Key</th><th>Label</th><th>操作</th></tr></thead>
    <tbody>
        <tr>
            <td>rpm</td><td>转速</td>
            <td><button onclick="removeRow(this)">删除</button></td>
        </tr>
    </tbody>
</table>
<button onclick="addRow()">+ 添加字段</button>

<script>
function addRow() {
    const tbody = document.querySelector('#fieldTable tbody');
    const row = document.createElement('tr');
    row.innerHTML = '<td>new_field</td><td>New Field</td><td><button onclick="removeRow(this)">删除</button></td>';
    tbody.appendChild(row);
}

function removeRow(btn) {
    btn.closest('tr').remove();
}
</script>
```

### 6.7 模态对话框

对应 Qt：`QDialog::exec()` / `QDialog::open()`

```html
<button onclick="showDialog('addDialog')">添加设备</button>

<div id="addDialog" class="dialog-overlay" style="display:none;" onclick="if(event.target===this)closeDialog('addDialog')">
    <div class="dialog">
        <h3>添加设备</h3>
        <form><!-- 表单内容 --></form>
        <div class="dialog-actions">
            <button onclick="closeDialog('addDialog')">取消</button>
            <button class="primary" onclick="closeDialog('addDialog')">确定</button>
        </div>
    </div>
</div>

<script>
function showDialog(id) {
    document.getElementById(id).style.display = '';
}
function closeDialog(id) {
    document.getElementById(id).style.display = 'none';
}
</script>
```

### 6.8 数值模拟（定时器驱动）

对应 Qt：`QTimer::timeout` 信号 + `QLabel::setText()` 更新

适用于监控面板、设备状态等需要动态数值展示的场景。启动/停止按钮控制定时器，数值自动递增模拟实时数据。

```html
<div class="stats-grid">
    <div class="stat-card">
        <span id="statCount" class="stat-value">0</span>
        <span class="stat-label">已发送帧数</span>
    </div>
</div>

<div class="action-bar">
    <button id="startBtn" onclick="toggleRunning(true)">&#9654; 启动</button>
    <button id="stopBtn" onclick="toggleRunning(false)" disabled>&#9632; 停止</button>
</div>

<script>
let isRunning = false;
let count = 0;
let timer = null;

function toggleRunning(running) {
    isRunning = running;
    document.getElementById('startBtn').disabled = running;
    document.getElementById('stopBtn').disabled = !running;
    if (running) {
        timer = setInterval(() => {
            count += Math.floor(Math.random() * 5) + 1;
            document.getElementById('statCount').textContent = count;
        }, 1000);
    } else {
        clearInterval(timer);
        timer = null;
    }
}
</script>
```

### JS 交互与 Qt 代码映射总结

| HTML JS 交互 | Qt 实现 | 说明 |
|-------------|---------|------|
| `switchTab(id)` | `QTabWidget::setCurrentIndex()` | Tab 切换 |
| `toggleRunning(bool)` | `QPushButton::setEnabled()` + 信号槽 | 按钮状态 |
| `selectItem(el)` | `QListWidget::currentItemChanged` | 列表选中 |
| `togglePanel(id)` | `QWidget::setVisible()` | 显示/隐藏 |
| `showContent(bool)` | `QStackedWidget::setCurrentIndex()` | 状态切换 |
| `addRow()` / `removeRow()` | `QTableWidget::insertRow/removeRow` | 表格行操作 |
| `showDialog()` / `closeDialog()` | `QDialog::open()/close()` | 对话框 |
| `toggleRunning()` + `setInterval` | `QTimer::timeout` + `QLabel::setText()` | 数值模拟 |
