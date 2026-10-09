# 数据与配置

仓库提供 `configs/pv_surface_seg.yaml` 和数据导入脚本，原训练图像和标签保留在本地完整项目中。`datasets/` 为本地数据存放位置，被 `.gitignore` 排除。

建议结构：

```text
data/
├── configs/pv_surface_seg.yaml
└── datasets/
    ├── panel-seg/
    │   ├── train/images/  与 train/labels/
    │   ├── valid/images/  与 valid/labels/
    │   └── test/images/   与 test/labels/
    └── tile-cls/
        ├── train/{0_High,1_Moderate,2_low}/
        ├── val/{0_High,1_Moderate,2_low}/
        └── test/{0_High,1_Moderate,2_low}/
```

## 面板分割

当前 YAML 定义单类别 `PV_surface`，类别编号为 0。图片与标签同名，标签使用 YOLO 多边形分割格式：

```text
0 x1 y1 x2 y2 x3 y3 ...
```

坐标相对于图片宽高归一化到 `[0, 1]`，每行对应一个面板实例。两阶段训练入口会将 YAML 的 `path: data/datasets/panel-seg` 解析为当前仓库中的绝对路径。

## 积灰等级分类

按原模型说明准备 `High`、`Moderate`、`low` 三类切片，各类别分别存放在独立文件夹中。原数据的目录名称带有编号前缀，推理模块按名称中的 `high` / `moderate` / `low` 识别等级。分类验证目录使用 `val`；分割 YAML 使用 `valid`，请按各自配置存放。

有完整项目时运行 `python scripts/import_datasets.py --source /path/to/PV_Project`。脚本优先选用 `老师给的/` 中对应的原始数据，否则使用项目根目录下的数据；只导入图像、标签和数据说明，排除缓存文件。

可使用 `--seg-data` 和 `--cls-data` 指定外部数据位置。数据来源、授权和训练 / 验证划分需要由数据提供方补充记录。
