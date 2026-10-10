from __future__ import annotations

import argparse

from ultralytics import YOLO


STAGES = {
    "panel-seg": {
        "default_model": "yolov8m-seg.pt",
        "description": "训练光伏板区域分割模型（YOLOv8）。",
    },
    "defect-seg": {
        "default_model": "yolo11m-seg.pt",
        "description": "训练光伏板多缺陷分割模型（YOLO11）。",
    },
    "defect-cls": {
        "default_model": "yolo11m-cls.pt",
        "description": "训练切片级缺陷分类模型（YOLO11）。",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Photovoltaic YOLO training entrypoint")
    parser.add_argument("--stage", choices=STAGES.keys(), required=True, help="训练阶段")
    parser.add_argument("--data", required=True, help="数据集 YAML 或分类目录路径")
    parser.add_argument("--model", help="基础模型权重路径")
    parser.add_argument("--epochs", type=int, default=100, help="训练轮次")
    parser.add_argument("--imgsz", type=int, default=640, help="输入尺寸")
    parser.add_argument("--batch", type=int, default=8, help="batch size")
    parser.add_argument("--device", default="0", help="训练设备，如 0 / cpu")
    parser.add_argument("--project", default="runs/pv", help="输出目录")
    parser.add_argument("--name", default="", help="实验名")
    parser.add_argument("--workers", type=int, default=4, help="数据加载线程数")
    parser.add_argument("--patience", type=int, default=20, help="早停 patience")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    stage = STAGES[args.stage]
    model_path = args.model or stage["default_model"]
    model = YOLO(model_path)
    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project=args.project,
        name=args.name or args.stage,
        workers=args.workers,
        patience=args.patience,
    )


if __name__ == "__main__":
    main()
