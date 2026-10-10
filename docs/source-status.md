# 发布范围与源码来源

仓库保留整理后的运行目录，并在 archive/PV_Project/ 上传原始项目的全部 61,418 个文件。原解压目录保留不变。

## 整理后的应用

- Flask 入口、配置、AnalysisPipeline 和训练入口位于 backend/。
- 前端位于 frontend/，已训练权重和初始权重分别位于 models/trained/、models/pretrained/。
- 示例图位于 samples/，论文和答辩资料在 docs/ 分类展示。
- 当前安装、启动、数据导入及核验工具位于 scripts/。

## 完整原始资料

archive/PV_Project/ 保留原解压目录的全部文件和原始路径，包括：

- 前后端、权重、三张示例图及所有原始工具。
- 两套训练数据、老师提供的资料及其中的重复数据。
- 论文、PPT、PPT 模板、全部字体、幻灯片预览和测试副本。
- 项目申报书、原包清单、原验证报告、交付说明及环境记录。
- backend/runtime/ 原上传图片、结果图和运行日志。
- tmp/ 原训练输出、准备数据、远程训练包及临时文件。
- 原 Python 缓存、系统文件和其他历史文件。

文件经过逐个 SHA-256 核验，记录位于 docs/checks/full-snapshot-validation.json。两份超过普通 Git 单文件上限的 ZIP 使用 Git LFS；其余归档文件正常纳入 Git。重复内容不删除，不用摘要或空文件代替原始资料。

## 新生成的本地环境

本次为核验新建的 .venv/、.git/、Ultralytics 配置、运行临时文件和导入后的 data/datasets/ 不属于原解压项目，继续作为本机工作环境保留。完整原始数据及原有同类文件都已通过归档上传。

## 验证记录

docs/checks/ 分别记录应用静态检查、CPU 运行检查及完整归档核验。历史论文数值、接口 targets 字段和演示数据不构成当前模型性能证据。本次没有重新训练模型或验证 GPU 环境。
