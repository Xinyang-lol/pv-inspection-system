# 示例图片

本目录提供从原项目保留的三张合成示例图：

- `dust-heavy.png`
- `crack-critical.png`
- `bio-stain.png`

可在看板上直接点击分析。默认使用已训练的面板分割与积灰分类模型；希望展示启发式多缺陷效果时，在启动前设置 `PV_DEMO_MODE=true`。图片文件名不代表已经具备对应缺陷的真实识别能力。

使用 `python scripts/generate_samples.py` 可重新生成图片，会覆盖同名文件。
