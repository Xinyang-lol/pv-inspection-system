# 模型权重

## 已训练权重：`trained/`

| 文件 | 原项目说明中的职责 |
| --- | --- |
| `panel_yolov8_seg.pt` | 分割光伏板表面 `PV_surface` |
| `dust_yolov8_cls.pt` | 面板切片积灰等级分类：`High`、`Moderate`、`low` |

这两份文件来自原项目，未重新训练或重新进行完整验证集评测。文件 SHA-256 和应用运行检查记录位于 `docs/checks/`；单次推理核验不能作为整体准确率或 GPU 性能结果。

`trained/defect_yolo11_seg.pt` 是原项目预留的可选多缺陷权重，当前未提供。不要将裂痕、生物污渍演示结果当作该模型的实际检测结果。

## 初始权重：`pretrained/`

- `yolov8n-seg.pt`：两阶段训练入口的默认分割起点。
- `yolov8n-cls.pt`：两阶段训练入口的默认分类起点。

初始权重与已训练权重分开存放，避免运行和重新训练时混用。

## 路径设置

`backend/config.py` 默认读取 `trained/`，相对路径以仓库根目录为基准，可通过 `PV_PANEL_MODEL`、`PV_TILE_CLS_MODEL`、`PV_DEFECT_MODEL` 改写。

配置保留了原项目中的模型显示名称；显示名称不构成网络规模或模型性能的核验依据。
