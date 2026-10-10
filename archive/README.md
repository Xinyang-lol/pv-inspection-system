# 完整原始项目

`PV_Project/` 保存原解压目录中的全部 61,418 个文件，保留文件名称、目录结构和文件内容。包含原打包清单记录的 61,417 个文件，以及打包清单 `PACKAGE_MANIFEST.json` 自身。

逐文件复制并核对 SHA-256，校验结果见 [完整副本核验记录](../docs/checks/full-snapshot-validation.json)。重复数据、测试副本、缓存、运行日志和原有压缩包均完整保留。

## 按用途查找

| 分类 | 原始目录或文件 |
| --- | --- |
| 前端 | `PV_Project/011 大数据可视化系统数据分析通用模版/` |
| 后端、原权重、示例图、上传记录与结果图 | `PV_Project/backend/` |
| 面板分割训练数据 | `PV_Project/yolo8 seg training data/` |
| 积灰等级分类训练数据 | `PV_Project/yolo8 cls training data/` |
| 老师提供的完整资料与另一套数据 | `PV_Project/老师给的/` |
| 论文、图表、原 PPT 和测试副本 | `PV_Project/paper/` |
| PPT 模板、原预览与字体 | `PV_Project/低碳科技20页蓝色系/` |
| 原工具 | `PV_Project/tools/` |
| 历史训练输出、准备数据、远程训练包和临时记录 | `PV_Project/tmp/` |
| 申报书 | `PV_Project/大学生创新创业训练计划项目申报书.doc` |
| 原清单、验证结果和交付说明 | `PV_Project/PACKAGE_MANIFEST.json`、`validation_report.json`、`交付说明.md` |
| 原安装、启动和停止入口 | `PV_Project/安装依赖.cmd`、`启动后端.cmd`、`停止后端.cmd` |
| 原初始权重与环境记录 | 根目录的 `yolov8n-*.pt`、`delivery_environment.txt` |

## 下载与使用

```bash
git lfs install
git clone https://github.com/Xinyang-lol/pv-inspection-system.git
cd pv-inspection-system
git lfs pull
```

`tmp/remote_train_payload.zip` 和 `tmp/remote_train_payload_posix.zip` 在完整副本中各约 200 MB，使用 Git LFS 保存真实文件；其他原文件正常纳入 Git。

运行整理后的应用，请使用仓库根目录的 README 和 scripts/。导入归档中的训练数据：

```bash
python scripts/import_datasets.py --source archive/PV_Project
```

原始历史脚本和文档仍可能包含旧机器路径，按原内容保留。本副本是完整资料归档，运行核验针对仓库根目录的整理后应用。
