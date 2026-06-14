# Model-View 模式 (Model-View Patterns)

## Qt 的 Model-View 体系

Qt 提供了最成熟的 Model-View 框架之一，但很多项目只用 `QTableWidget` (Item-Based)，错过了 Model-View 的最大价值：**数据与显示的分离**。

## Item-Based vs Model-Based

| | Item-Based (`QTableWidget`) | Model-Based (`QTableView` + Model) |
|---|---|---|
| 数据存储 | 存储在 Widget 内部 | Model 持有，Widget 无状态 |
| 大数据量 (10k+ 行) | 极慢，内存高 | 快，只渲染可见行 |
| 多视图同一数据 | 需要手动同步 | 天然支持（一个 Model，多个 View） |
| 更新方式 | 直接 `setItem()` | `dataChanged()` 信号触发重绘 |
| 可测试性 | 低（需要创建 Widget） | 高（Model 是纯数据适配，可独立测试） |
| 适用规模 | < 500 行 | 任意规模 |

**推荐**：所有表格和列表都使用 Model-Based 方案，即使是小项目——它强制你养成数据与视图分离的习惯。

## 自定义 TableModel 模板

```cpp
// device_list_model.h
class DeviceListModel : public QAbstractTableModel {
    Q_OBJECT
public:
    enum Column {
        kName = 0,
        kStatus,
        kAddress,
        kLastSeen,
        kColumnCount  // 用于 columnCount()
    };

    // 角色的扩展定义
    enum CustomRole {
        kDeviceIdRole = Qt::UserRole + 1,   // 用于查找
        kSortRole = Qt::UserRole + 2,        // 用于排序
        kStatusColorRole = Qt::UserRole + 3, // 用于 Delegate 绘制
    };

    explicit DeviceListModel(QObject* parent = nullptr);

    // ── 必须实现的虚函数 ──
    int rowCount(const QModelIndex& parent = QModelIndex{}) const override;
    int columnCount(const QModelIndex& parent = QModelIndex{}) const override;
    QVariant data(const QModelIndex& index, int role = Qt::DisplayRole) const override;
    QVariant headerData(int section, Qt::Orientation orientation,
                        int role = Qt::DisplayRole) const override;

    // ── 数据更新接口 ──
    void SetDevices(QList<DeviceInfo> devices);
    void UpdateDeviceStatus(DeviceId id, bool online);
    void AddDevice(const DeviceInfo& device);
    void RemoveDevice(DeviceId id);
    DeviceInfo GetDevice(int row) const;

private:
    QList<DeviceInfo> devices_;
};
```

```cpp
// device_list_model.cpp
int DeviceListModel::rowCount(const QModelIndex& parent) const {
    return parent.isValid() ? 0 : devices_.size();
}

int DeviceListModel::columnCount(const QModelIndex& parent) const {
    return parent.isValid() ? 0 : kColumnCount;
}

QVariant DeviceListModel::data(const QModelIndex& index, int role) const {
    if (!index.isValid() || index.row() >= devices_.size())
        return {};

    const auto& device = devices_[index.row()];

    switch (role) {
    case Qt::DisplayRole:
        switch (index.column()) {
        case kName:    return device.name;
        case kStatus:  return device.online ? "在线" : "离线";
        case kAddress: return device.address;
        case kLastSeen: return device.lastSeen.toString("hh:mm:ss");
        }
        break;

    case Qt::ToolTipRole:
        return QString("设备: %1\n状态: %2\n地址: %3")
            .arg(device.name)
            .arg(device.online ? "在线" : "离线")
            .arg(device.address);

    case kDeviceIdRole:
        return device.id;

    case kStatusColorRole:
        return device.online ? QColor("#4CAF50") : QColor("#F44336");

    case Qt::TextAlignmentRole:
        return int(Qt::AlignLeft | Qt::AlignVCenter);
    }
    return {};
}

QVariant DeviceListModel::headerData(int section, Qt::Orientation orientation,
                                      int role) const {
    if (orientation != Qt::Horizontal || role != Qt::DisplayRole)
        return {};

    switch (section) {
    case kName:    return "设备名称";
    case kStatus:  return "状态";
    case kAddress: return "地址";
    case kLastSeen: return "最后在线";
    }
    return {};
}
```

## 数据更新模式

### 全量替换（适合小数据量）

```cpp
void DeviceListModel::SetDevices(QList<DeviceInfo> devices) {
    beginResetModel();
    devices_ = std::move(devices);
    endResetModel();
    // View 完全重建——简单但适合 < 1000 行的数据
}
```

### 增量更新（适合大数据量）

```cpp
void DeviceListModel::AddDevice(const DeviceInfo& device) {
    int row = devices_.size();
    beginInsertRows(QModelIndex{}, row, row);
    devices_.append(device);
    endInsertRows();
}

void DeviceListModel::UpdateDeviceStatus(DeviceId id, bool online) {
    for (int i = 0; i < devices_.size(); ++i) {
        if (devices_[i].id == id) {
            devices_[i].online = online;
            auto index = createIndex(i, kStatus);
            emit dataChanged(index, index, {Qt::DisplayRole, kStatusColorRole});
            return;
        }
    }
}

void DeviceListModel::RemoveDevice(DeviceId id) {
    for (int i = 0; i < devices_.size(); ++i) {
        if (devices_[i].id == id) {
            beginRemoveRows(QModelIndex{}, i, i);
            devices_.removeAt(i);
            endRemoveRows();
            return;
        }
    }
}
```

## 自定义 Delegate

Delegate 负责**绘制**和**编辑**单个单元格。把绘制逻辑从 Model 和 View 中抽离：

```cpp
class StatusColorDelegate : public QStyledItemDelegate {
    Q_OBJECT
public:
    using QStyledItemDelegate::QStyledItemDelegate;

    void paint(QPainter* painter, const QStyleOptionViewItem& option,
               const QModelIndex& index) const override
    {
        auto opt = option;
        initStyleOption(&opt, index);

        // 获取自定义角色数据
        QColor statusColor = index.data(DeviceListModel::kStatusColorRole).value<QColor>();

        // 绘制背景圆点
        painter->save();
        painter->setRenderHint(QPainter::Antialiasing);
        QRectF dotRect(opt.rect.left() + 8, opt.rect.center().y() - 4, 8, 8);
        painter->setBrush(statusColor);
        painter->setPen(Qt::NoPen);
        painter->drawEllipse(dotRect);
        painter->restore();

        // 偏移文本以容纳圆点
        opt.rect.adjust(24, 0, 0, 0);
        QStyledItemDelegate::paint(painter, opt, index);
    }

    QSize sizeHint(const QStyleOptionViewItem& option,
                   const QModelIndex& index) const override
    {
        auto size = QStyledItemDelegate::sizeHint(option, index);
        size.setHeight(32);  // 固定行高
        return size;
    }
};
```

## 排序与过滤：QSortFilterProxyModel

```cpp
// 在 Model 和 View 之间插入代理
auto* model = new DeviceListModel(this);
auto* proxy = new QSortFilterProxyModel(this);
proxy->setSourceModel(model);

// 按名称过滤
proxy->setFilterKeyColumn(DeviceListModel::kName);
proxy->setFilterCaseSensitivity(Qt::CaseInsensitive);

// 只显示在线的设备
proxy->setFilterFixedString("在线");  // 或自定义 filterAcceptsRow

auto* view = new QTableView;
view->setModel(proxy);         // View 绑定到 Proxy
view->setSortingEnabled(true);  // 点击表头排序
```

## Model 在架构中的位置

```
src/
├── core/
│   └── models/           ← QAbstractXxxModel 放这里
│       ├── device_list_model.h
│       └── log_table_model.h
├── ui/
│   ├── delegates/        ← QStyledItemDelegate 放这里
│   │   ├── status_color_delegate.h
│   │   └── log_level_delegate.h
│   └── panels/
│       └── device_list_panel.h  ← QTableView + 布局 放这里
```

**为什么 Model 在 `core/` 而不是 `ui/`**：
- Model 是数据的适配层，不绘制任何像素
- Model 不依赖 QWidget
- Model 可以独立进行单元测试（不需要创建 View）

## 常见反模式

### ❌ 直接操作 QTableWidget

```cpp
// ❌ 数据混在 Widget 中
auto* table = new QTableWidget(100, 4);
for (int i = 0; i < devices.size(); ++i) {
    table->setItem(i, 0, new QTableWidgetItem(devices[i].name));
    table->setItem(i, 1, new QTableWidgetItem(devices[i].address));
}
// 问题：
// 1. 数据和视图耦合，无法换数据源
// 2. 10000 行时性能崩溃
// 3. 要给另一个 View (如 QListView) 展示相同数据时，需要复制
```

### ❌ 循环 emit dataChanged

```cpp
// ❌ 更新 500 行数据，触发 500 次重绘
for (int i = 0; i < 500; ++i) {
    devices_[i].online = true;
    emit dataChanged(index(i, 1), index(i, 1));
}

// ✅ 使用 beginResetModel / endResetModel 批量更新
for (auto& d : devices_) d.online = true; // 内存操作，很快
beginResetModel();
endResetModel();  // 一次重绘
```

### ❌ 在 data() 函数中做耗时操作

```cpp
// ❌ data() 被 View 在绘制每一帧时调用，可能每秒几十次
QVariant MyModel::data(const QModelIndex& index, int role) const {
    if (role == Qt::DisplayRole) {
        return db_.QueryValue(index.row());  // 每次绘制都查数据库！
    }
}

// ✅ 数据预加载到内存
QVariant MyModel::data(const QModelIndex& index, int role) const {
    if (role == Qt::DisplayRole) {
        return cache_[index.row()];  // 内存访问，< 50ns
    }
}
```
