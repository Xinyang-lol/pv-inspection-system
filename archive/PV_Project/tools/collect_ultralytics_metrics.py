from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ultralytics import YOLO


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Ultralytics checkpoint and export metrics")
    parser.add_argument("--task", choices=["segment", "classify", "detect"], required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--data", required=True)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--split", default="test")
    parser.add_argument("--out", required=True)
    return parser.parse_args()


def serialize(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {key: serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [serialize(item) for item in value]
    if hasattr(value, "tolist"):
        return value.tolist()
    return str(value)


def main() -> None:
    args = parse_args()
    model = YOLO(args.model)
    metrics = model.val(data=args.data, imgsz=args.imgsz, device=args.device, split=args.split)

    result: dict[str, Any] = {
        "task": args.task,
        "model": args.model,
        "data": args.data,
        "split": args.split,
        "results_dict": serialize(getattr(metrics, "results_dict", None)),
        "speed": serialize(getattr(metrics, "speed", None)),
    }

    if args.task == "segment":
        result["box"] = {
            "map50": serialize(getattr(metrics.box, "map50", None)),
            "map50_95": serialize(getattr(metrics.box, "map", None)),
            "precision": serialize(getattr(metrics.box, "p", None)),
            "recall": serialize(getattr(metrics.box, "r", None)),
        }
        result["seg"] = {
            "map50": serialize(getattr(metrics.seg, "map50", None)),
            "map50_95": serialize(getattr(metrics.seg, "map", None)),
            "precision": serialize(getattr(metrics.seg, "p", None)),
            "recall": serialize(getattr(metrics.seg, "r", None)),
        }
    elif args.task == "classify":
        result["classify"] = {
            "top1": serialize(getattr(metrics, "top1", None)),
            "top5": serialize(getattr(metrics, "top5", None)),
            "fitness": serialize(getattr(metrics, "fitness", None)),
        }
    else:
        result["box"] = {
            "map50": serialize(getattr(metrics.box, "map50", None)),
            "map50_95": serialize(getattr(metrics.box, "map", None)),
            "precision": serialize(getattr(metrics.box, "p", None)),
            "recall": serialize(getattr(metrics.box, "r", None)),
        }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
