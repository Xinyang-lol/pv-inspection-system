# 光伏板智能检测项目

完整安装、运行、模型能力和打包范围见 [交付说明](交付说明.md)。

## 快速启动

安装 Python 后，依次双击 `安装依赖.cmd`、`启动后端.cmd`，访问 http://127.0.0.1:5000 。

或在项目根目录执行：

```bash
pip install -r backend/requirements.txt
python -m backend.app
```

## 目录

- `011 大数据可视化系统数据分析通用模版/`：HTML、JavaScript、CSS、字体和图片，Flask 直接提供前端页面。
- `backend/`：接口、推理流水线、训练入口、模型、样本、运行记录。
- `tools/`：启动、停止、数据准备、训练及材料生成工具。
- `yolo8 cls training data/`、`yolo8 seg training data/`、`老师给的/`：训练数据与原始资料。
- `paper/`、`低碳科技20页蓝色系/`、项目申报书：论文和演示材料。
- `tmp/`：原项目临时资料及训练记录，完整保留。

当前实际模型为面板分割和积灰等级分类。备用 YOLO11 多缺陷分割权重未提供。模型说明见 [backend/models/README.md](backend/models/README.md)。

## API

- `GET /api/health`：模型状态
- `GET /api/dashboard`：仪表盘
- `GET /api/samples`：示例列表
- `POST /api/analyze`：上传图片（image 字段）
- `POST /api/analyze-sample/<sample_id>`：分析示例
- `GET /api/results/<filename>`：结果图
- `POST /api/reset`：清空分析历史
