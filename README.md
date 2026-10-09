# 光伏板智能检测系统 · PV Inspection System

面向光伏组件巡检的 Python / Flask 项目，包含图像上传与分析接口、YOLOv8 训练入口、两份已训练权重，以及基于 ECharts 的可视化看板。

项目包含应用源码、两份已训练权重和三张合成示例图，使用 CPU 即可运行。原始训练数据与历史运行文件保留在本地，GitHub 仓库提供数据布局、导入脚本和训练配置。论文草稿及答辩材料单独归入 `docs/`。

## 功能与模型范围

主流程为：**光伏板区域分割 → 32 / 40 像素切片 → 积灰等级分类 → 覆盖率和风险汇总 → 看板展示**。

| 内容 | 当前仓库提供情况 |
| --- | --- |
| 可视化界面 | 提供 HTML、CSS、JavaScript、ECharts 和 jQuery 本地资源 |
| Flask 接口和推理模块 | 提供图像上传、分析、结果图、历史与看板接口 |
| 光伏板区域分割权重 | 提供 `models/trained/panel_yolov8_seg.pt` |
| 积灰等级分类权重 | 提供 `models/trained/dust_yolov8_cls.pt`；原说明中的类别为 `High`、`Moderate`、`low` |
| YOLOv8 初始权重 | 提供 `models/pretrained/yolov8n-seg.pt`、`yolov8n-cls.pt` |
| 模型训练入口 | 提供；从原完整项目导入数据或自行准备数据后训练 |
| 裂痕、生物污渍分割 | 可选扩展；缺少 `defect_yolo11_seg.pt`，不能作为已实现能力 |
| 示例图片 | 提供三张合成场景图，支持点击分析 |

**能力边界：** 当前真实模型支持面板分割和积灰等级分类；积灰“覆盖率”为按分类等级加权的估计值，风险分数为规则计算结果。裂痕和生物污渍区域在真实两阶段流程中没有对应训练权重；演示模式的这些结果来自启发式模拟。`/api/health` 中的 `targets` 是设计目标，论文草稿中的占位值和历史基线也不代表当前权重的评测成绩。

## 目录结构

```text
pv-inspection-system/
├── frontend/                       # 可视化界面和本地静态资源
│   ├── index.html
│   ├── css/
│   ├── js/
│   ├── images/
│   └── font/
├── backend/                        # Flask 接口、应用配置、训练入口
│   ├── app.py
│   ├── config.py
│   ├── train_teacher_models.py     # 分割 + 积灰分类两阶段训练
│   ├── train.py                    # 通用 YOLO 训练入口
│   ├── requirements.txt
│   └── services/pipeline.py        # 分割、切片分类、汇总、绘图和历史
├── models/
│   ├── trained/                    # 供应用推理的已训练权重
│   └── pretrained/                 # 供重新训练的初始权重
├── data/
│   ├── configs/                    # 可提交的数据集配置
│   └── datasets/                   # 本地数据，不上传 GitHub
├── samples/                        # 合成示例图
├── scripts/                        # 安装、启动、导入数据、训练辅助与核验
├── docs/                           # 架构、接口、训练及完整性说明
│   ├── checks/                     # 静态核验与应用运行验证记录
│   ├── papers/                     # 论文草稿、图表和历史基线
│   ├── presentations/              # 答辩 PPT、讲稿和预览
│   └── reference/                  # 原交付说明及历史环境记录
├── requirements.txt                # 根目录依赖入口
├── .gitignore
└── README.md
```

运行生成的上传图片、结果图和历史记录位于 `backend/runtime/`，训练输出位于 `backend/runs/`。这些目录与 `data/datasets/`、本地虚拟环境均不进入版本控制。

## 安装与运行

需要 Python 3.10 或以上、可用的 Python 包下载网络。后端直接提供前端页面，无需安装 Node.js。默认使用 CPU。

### Windows

```powershell
git clone https://github.com/Xinyang-lol/pv-inspection-system.git
cd pv-inspection-system
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m backend.app
```

也可依次双击 `scripts/install.cmd` 和 `scripts/start.cmd`。服务在当前窗口运行，按 `Ctrl+C` 停止。

### Linux / macOS

```bash
git clone https://github.com/Xinyang-lol/pv-inspection-system.git
cd pv-inspection-system
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m backend.app
```

启动成功后访问 **http://127.0.0.1:5000**。使用「选择图像 → 开始分析」上传 JPG / PNG；可一次选择多张，前端按顺序调用单图分析接口。

仅预览静态界面时可直接打开 `frontend/index.html`，或执行 `python -m http.server 8000 --directory frontend` 后访问 http://127.0.0.1:8000。没有后端时，上传分析、历史记录和动态图表数据不可用。

## 应用配置

程序直接读取环境变量，**不会自动加载 `.env` 文件**。在启动服务的同一个终端中设置变量，例如：

```powershell
$env:PV_DEVICE = "cpu"
$env:PV_HOST = "127.0.0.1"
.\.venv\Scripts\python.exe -m backend.app
```

| 变量 | 默认值 | 用途 |
| --- | --- | --- |
| `PV_DEVICE` | `cpu` | 推理设备；GPU 配置取决于 PyTorch / CUDA 环境 |
| `PV_HOST` | `0.0.0.0` | Flask 监听地址 |
| `PV_PORT` | `5000` | Flask 端口 |
| `PV_PANEL_MODEL` | `models/trained/panel_yolov8_seg.pt` | 面板分割权重路径 |
| `PV_TILE_CLS_MODEL` | `models/trained/dust_yolov8_cls.pt` | 积灰分类权重路径 |
| `PV_DEFECT_MODEL` | `models/trained/defect_yolo11_seg.pt` | 可选多缺陷分割权重路径；当前未提供 |
| `PV_CONFIDENCE` | `0.25` | 检测置信度阈值 |
| `PV_TILE_MIN_MASK_RATIO` | `0.15` | 切片与面板掩膜的最小重叠比例 |
| `PV_DEMO_MODE` | `false` | 强制启用合成 / 启发式演示流程 |
| `PV_DEBUG` | `false` | Flask 调试开关 |

相对模型路径以仓库根目录为基准。若修改服务端口，原前端需通过 `?api=` 指定地址，例如 `http://127.0.0.1:5001/?api=http://127.0.0.1:5001`。希望演示全部界面时，在启动前设置 `$env:PV_DEMO_MODE = "true"`；演示结果不作为真实检测效果。

## 模型训练

原训练图像与标签不上传 GitHub。已有原完整项目时，可导入原数据目录，优先使用“老师给的”目录中的数据：

```powershell
.\.venv\Scripts\python.exe scripts/import_datasets.py --source "E:\path\to\PV_Project"
```

导入会优先创建文件硬链接，不能创建时复制文件；使用 `--copy` 可强制复制。分割、分类数据分别整理到 `data/datasets/panel-seg/`、`tile-cls/`。也可按 [数据集说明](data/README.md) 自行准备数据。随后在仓库根目录执行：

```bash
python -m backend.train_teacher_models --stage all --epochs 100 --device cpu --copy-best
```

该命令依次训练面板分割和积灰分类，将最佳权重复制至 `models/trained/`，会覆盖同名应用权重。单阶段训练、参数和数据目录说明见 [训练指南](docs/training.md)。

## 接口

服务启动后提供以下路由：

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/api/health` | 模型加载状态和运行模式 |
| GET | `/api/dashboard` | 看板总览、图表和最近记录 |
| GET | `/api/samples` | 可用示例列表 |
| POST | `/api/analyze` | 上传单张图片；multipart 字段名为 `image` |
| POST | `/api/analyze-sample/<sample_id>` | 分析指定示例 |
| GET | `/api/sample-files/<filename>` | 获取示例图片 |
| GET | `/api/results/<filename>` | 获取标注结果图片 |
| POST | `/api/reset` | 重置分析历史 |

调用示例与错误响应见 [接口说明](docs/api.md)。

## 核验与资料

```bash
python scripts/check_project.py
python scripts/check_project.py --require-runtime
python scripts/verify_runtime.py --image /path/to/real-panel.jpg
```

前两个命令检查 Python 语法、目录配置、静态资源引用、文档链接和模型文件；第二个还要求推理模块存在。第三个使用自备的真实光伏板图片检查接口和两阶段推理，并验证三张示例图的显式演示模式。

本次在 Windows、Python 3.12.5、CPU 环境通过静态检查及上述应用运行核验。一次真实图片分析检测到 6 块面板并完成积灰分类；这仅说明流程可运行，不代表验证集准确率或 GPU 性能。核验记录见 [静态检查](docs/checks/static-validation.json)和[应用运行检查](docs/checks/runtime-validation.json)。

- [发布范围说明](docs/source-status.md)：源码来源、目录整理与发布排除项。
- [架构说明](docs/architecture.md)：组件关系及目录迁移规则。
- [模型说明](models/README.md)：两种权重的职责及限制。
- [训练指南](docs/training.md)：数据布局、训练命令和输出位置。
- [历史参考脚本](scripts/reference/README.md)：老师提供的原始训练示例及论文、PPT 生成工具。
- [论文资料](docs/papers/README.md)与[答辩资料](docs/presentations/README.md)：研究草稿、图表、PPT 和讲稿，独立于应用运行。
- [原始交付说明](docs/reference/original-delivery.md)及[历史环境](docs/reference/original-environment.txt)：保留作参考，其中部分文件和路径已不适用于当前副本。

项目申报书、原打包清单和原验证报告保留在整理后的本地 `docs/private/`，不上传公开仓库。原验证报告来自另一个路径和环境，不作为本次核验结果。
