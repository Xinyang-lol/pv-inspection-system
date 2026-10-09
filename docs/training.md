# 模型训练指南

训练入口需要安装依赖并准备本地数据。GitHub 仓库不上传原训练图像、标签或全部训练日志，本次未重新训练。

## 两阶段训练

`backend/train_teacher_models.py` 对应原项目说明中的 YOLOv8 面板分割与积灰分类流程。

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--stage` | `all` | `panel-seg`、`tile-cls` 或 `all` |
| `--seg-data` | `data/configs/pv_surface_seg.yaml` | 分割数据配置 |
| `--cls-data` | `data/datasets/tile-cls` | 分类数据目录 |
| `--seg-model` | `models/pretrained/yolov8n-seg.pt` | 分割初始权重 |
| `--cls-model` | `models/pretrained/yolov8n-cls.pt` | 分类初始权重 |
| `--epochs` | `100` | 两阶段训练轮次 |
| `--seg-imgsz` | `640` | 分割输入尺寸 |
| `--cls-imgsz` | `64` | 分类输入尺寸 |
| `--seg-batch` / `--cls-batch` | `8` / `16` | 批次大小 |
| `--device` | `0` | 默认 GPU 设备；CPU 环境显式传 `cpu` |
| `--workers` | `4` | 数据加载进程数 |
| `--project` | `backend/runs` | 输出目录 |
| `--copy-best` | 默认关闭 | 将最佳权重复制至 `models/trained/`，覆盖同名文件 |
| `--amp` | 默认关闭 | 启用自动混合精度 |

在仓库根目录运行：

```bash
# 两阶段，使用 CPU
python -m backend.train_teacher_models --stage all --epochs 100 --device cpu --copy-best

# 只训练面板分割
python -m backend.train_teacher_models --stage panel-seg --device cpu

# 只训练积灰分类
python -m backend.train_teacher_models --stage tile-cls --device cpu

# 使用已有数据位置
python -m backend.train_teacher_models --stage tile-cls --cls-data /path/to/tile-data --device cpu

# 查看完整参数
python -m backend.train_teacher_models --help
```

分割训练会将数据 YAML 中的相对 `path` 按仓库根目录解析，生成 `backend/runtime/pv_surface_seg.resolved.yaml` 后交给 Ultralytics。

默认训练输出名称为 `pv_surface_yolov8_seg` 和 `pv_tile_yolov8_cls`；重复运行时 Ultralytics 可能添加编号。启用 `--copy-best` 后会复制各阶段 `weights/best.pt`。

## 通用训练入口

`backend/train.py` 保留了原项目的通用入口，支持 `panel-seg`、`defect-seg`、`defect-cls`。后两者只是训练入口，当前不附带已训练多缺陷权重。

```bash
python -m backend.train --stage panel-seg --data data/configs/pv_surface_seg.yaml --model models/pretrained/yolov8n-seg.pt --device cpu
```

该入口直接将 `--data` 交给 Ultralytics；如果数据 YAML 使用相对路径，先将其中 `path` 设置成实际数据集的绝对路径。建议主流程使用上方两阶段入口。

数据目录与标注格式见 [数据集说明](../data/README.md)。训练结束后，请用独立验证集评估模型，再更新应用权重和评测记录。
