from __future__ import annotations

import json
import math
import time
import uuid
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw

from backend.config import AppConfig

try:
    from ultralytics import YOLO
except Exception:  # pragma: no cover - optional dependency at runtime
    YOLO = None


ISSUE_LABELS = {
    "dust": "灰尘",
    "crack": "裂痕",
    "stain": "生物污渍",
    "other": "其他异常",
}

ISSUE_COLORS = {
    "dust": (244, 208, 63, 90),
    "crack": (231, 76, 60, 190),
    "stain": (46, 204, 113, 180),
    "other": (52, 152, 219, 180),
}

TILE_LEVEL_COLORS = {
    "low": (74, 192, 3, 70),
    "medium": (255, 220, 45, 105),
    "high": (255, 8, 0, 135),
}
TILE_LEVEL_WEIGHTS = {"low": 0.12, "medium": 0.55, "high": 1.0}

SEVERITY_ORDER = ["low", "medium", "high"]
SEVERITY_LABELS = {"low": "低", "medium": "中", "high": "高"}
RUNTIME_LABELS = ["面板分割", "缺陷识别", "结果绘制"]
METRICS_VERSION = 4

MODEL_ALIASES = {
    "dust": "dust",
    "dirty": "dust",
    "dirt": "dust",
    "soil": "dust",
    "灰尘": "dust",
    "积灰": "dust",
    "crack": "crack",
    "fracture": "crack",
    "split": "crack",
    "裂纹": "crack",
    "裂痕": "crack",
    "污渍": "stain",
    "stain": "stain",
    "bird_drop": "stain",
    "bird": "stain",
    "bio": "stain",
    "leaf": "stain",
    "生物污渍": "stain",
}

SAMPLE_DEFINITIONS = [
    {
        "id": "dust-heavy",
        "filename": "dust-heavy.png",
        "name": "示例一：大面积积灰",
        "summary": "适合演示灰尘覆盖率偏高、需要优先清洗的场景。",
    },
    {
        "id": "crack-critical",
        "filename": "crack-critical.png",
        "name": "示例二：裂痕高风险",
        "summary": "适合演示裂痕长度较高、需要人工复检的场景。",
    },
    {
        "id": "bio-stain",
        "filename": "bio-stain.png",
        "name": "示例三：生物污渍堆积",
        "summary": "适合演示鸟粪或树叶残留导致的局部污染场景。",
    },
]


@dataclass(slots=True)
class HistoryStore:
    path: Path

    def load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as file:
            try:
                payload = json.load(file)
            except json.JSONDecodeError:
                return []
        if not isinstance(payload, list):
            return []
        return payload

    def save(self, records: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(records[-30:], file, ensure_ascii=False, indent=2)

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()

    def append(self, record: dict[str, Any]) -> list[dict[str, Any]]:
        records = self.load()
        records.append(record)
        self.save(records)
        return records


class AnalysisPipeline:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.history = HistoryStore(config.history_path)
        self._panel_model = None
        self._defect_model = None
        self._tile_classifier_model = None
        self._runtime_mode = "demo"
        self._last_runtime = {"panel_ms": 0.0, "defect_ms": 0.0, "render_ms": 0.0}

    def get_status(self) -> dict[str, Any]:
        panel_ready = self.config.panel_model_path.exists()
        defect_ready = self.config.defect_model_path.exists()
        tile_classifier_ready = self.config.tile_classifier_model_path.exists()
        ultralytics_ready = YOLO is not None
        demo_reason = []
        if self.config.force_demo_mode:
            demo_reason.append("已显式启用演示模式")
        if not ultralytics_ready:
            demo_reason.append("未安装 ultralytics")
        if not panel_ready:
            demo_reason.append("缺少 YOLOv8 面板分割权重")
        if not tile_classifier_ready and not defect_ready:
            demo_reason.append("缺少 YOLOv8 tile 分类权重或 YOLO 缺陷检测权重")
        runtime_mode = self._resolve_yolo_runtime_mode() if self._can_use_yolo() else "demo"
        return {
            "runtime_mode": runtime_mode,
            "demo_reason": "；".join(demo_reason) if demo_reason else "",
            "samples_ready": all(
                (self.config.samples_root / item["filename"]).exists() for item in SAMPLE_DEFINITIONS
            ),
            "models": [
                {
                    "name": self.config.panel_model_name,
                    "role": "光伏板区域分割",
                    "status": "ready" if panel_ready and ultralytics_ready else "demo",
                    "weights": str(self.config.panel_model_path),
                    "latency_ms": round(self._last_runtime["panel_ms"], 2),
                },
                {
                    "name": self.config.defect_model_name,
                    "role": "备用多缺陷分割",
                    "status": "ready" if defect_ready and ultralytics_ready else "demo",
                    "weights": str(self.config.defect_model_path),
                    "latency_ms": round(self._last_runtime["defect_ms"], 2),
                },
                {
                    "name": self.config.tile_classifier_model_name,
                    "role": "面板 tile 污染等级分类",
                    "status": "ready" if tile_classifier_ready and ultralytics_ready else "demo",
                    "weights": str(self.config.tile_classifier_model_path),
                    "latency_ms": round(self._last_runtime["defect_ms"], 2),
                },
            ],
            "targets": {
                "iou": 0.95,
                "dice": 0.96,
                "pixel_accuracy": 0.98,
                "macro_f1": 0.93,
                "gpu_latency_ms": 50,
                "edge_latency_ms": 500,
            },
        }

    def list_samples(self) -> list[dict[str, Any]]:
        samples = []
        for item in SAMPLE_DEFINITIONS:
            sample_path = self.config.samples_root / item["filename"]
            samples.append(
                {
                    "id": item["id"],
                    "name": item["name"],
                    "summary": item["summary"],
                    "filename": item["filename"],
                    "ready": sample_path.exists(),
                    "image_url": f"/api/sample-files/{item['filename']}",
                }
            )
        return samples

    def reset_dashboard(self) -> dict[str, Any]:
        self.history.clear()
        self._last_runtime = {"panel_ms": 0.0, "defect_ms": 0.0, "render_ms": 0.0}
        return self.build_dashboard(records=[])

    def resolve_sample(self, sample_id: str) -> Path | None:
        for item in SAMPLE_DEFINITIONS:
            if item["id"] == sample_id:
                sample_path = (self.config.samples_root / item["filename"]).resolve()
                if sample_path.exists() and sample_path.parent == self.config.samples_root.resolve():
                    return sample_path
                return None
        return None

    def analyze(self, image_path: Path) -> dict[str, Any]:
        image = Image.open(image_path).convert("RGBA")
        started_at = time.perf_counter()

        if self._can_use_yolo():
            self._runtime_mode = "yolo"
            panels, detections = self._run_yolo_pipeline(image_path, image)
        else:
            self._runtime_mode = "demo"
            panels, detections = self._run_demo_pipeline(image)

        render_started = time.perf_counter()
        overlay_name = f"{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:8]}.png"
        overlay_path = self.config.results_root / overlay_name
        self._draw_overlay(image, panels, detections, overlay_path)
        self._last_runtime["render_ms"] = (time.perf_counter() - render_started) * 1000

        analysis = self._build_analysis_payload(
            image_path=image_path,
            overlay_name=overlay_name,
            panels=panels,
            detections=detections,
            total_ms=(time.perf_counter() - started_at) * 1000,
        )
        records = self.history.append(analysis["history_entry"])
        dashboard = self.build_dashboard(records=records, latest_analysis=analysis)
        return {"analysis": analysis, "dashboard": dashboard}

    def build_dashboard(
        self,
        records: list[dict[str, Any]] | None = None,
        latest_analysis: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        raw_records = records if records is not None else self.history.load()
        records = [self._normalize_record_metrics(item) for item in raw_records]
        latest_record = (
            self._normalize_record_metrics(latest_analysis["history_entry"])
            if latest_analysis
            else (records[-1] if records else None)
        )
        latest_detail = latest_analysis if latest_analysis else None
        status = self.get_status()

        if latest_record:
            crack_strength = latest_record.get(
                "crack_strength",
                self._estimate_crack_strength_from_length(latest_record.get("crack_length", 0.0)),
            )
            overview = {
                "runtime_mode": status["runtime_mode"],
                "analysis_count": len(records),
                "panel_count": latest_record["panel_count"],
                "dirty_panels": latest_record["dirty_panels"],
                "total_defects": latest_record["total_defects"],
                "avg_confidence": latest_record["avg_confidence"],
                "total_latency_ms": latest_record["runtime_ms"]["total"],
                "risk_score": latest_record["risk_score"],
                "dust_coverage": latest_record["dust_coverage"],
                "crack_length": latest_record["crack_length"],
                "crack_length_px": latest_record["crack_length"],
                "crack_strength": crack_strength,
                "stain_coverage": latest_record["stain_coverage"],
                "dominant_issue": latest_record["dominant_issue"],
                "last_filename": latest_record["filename"],
                "last_image_url": latest_record["result_image_url"],
                "timestamp": latest_record["timestamp"],
            }
            type_breakdown = latest_record["defect_breakdown"]
            severity_breakdown = latest_record["severity_breakdown"]
            panel_ranking = latest_record["panel_ranking"]
            recommendations = latest_record["recommendations"]
            runtime_chart = [
                round(latest_record["runtime_ms"]["panel"], 2),
                round(latest_record["runtime_ms"]["defect"], 2),
                round(latest_record["runtime_ms"]["render"], 2),
            ]
        else:
            overview = {
                "runtime_mode": status["runtime_mode"],
                "analysis_count": 0,
                "panel_count": 0,
                "dirty_panels": 0,
                "total_defects": 0,
                "avg_confidence": 0,
                "total_latency_ms": 0,
                "risk_score": 0,
                "dust_coverage": 0,
                "crack_length": 0,
                "crack_length_px": 0,
                "crack_strength": 0,
                "stain_coverage": 0,
                "dominant_issue": "暂无分析结果",
                "last_filename": "待上传图像",
                "last_image_url": "",
                "timestamp": "",
            }
            type_breakdown = {key: 0 for key in ISSUE_LABELS}
            severity_breakdown = {level: 0 for level in SEVERITY_ORDER}
            panel_ranking = []
            recommendations = [
                "上传一张光伏板图像后，将自动生成缺陷分布、风险排行和维护建议。",
                "将训练好的 YOLOv8/YOLO11 权重放入 backend/models 目录后，系统会自动切换为真实推理模式。",
            ]
            runtime_chart = [0, 0, 0]

        trend_records = records[-8:]
        trend_start_index = len(records) - len(trend_records) + 1
        trend_points = [
            {
                "label": f"第 {trend_start_index + index} 张",
                "image_index": trend_start_index + index,
                "timestamp": item["timestamp"][5:16].replace("T", " "),
                "filename": item["filename"],
                "risk_score": item["risk_score"],
                "total_defects": item["total_defects"],
                "dirty_panels": item["dirty_panels"],
            }
            for index, item in enumerate(trend_records)
        ]

        recent_records = [
            {
                "timestamp": item["timestamp"].replace("T", " "),
                "filename": item["filename"],
                "mode": item["mode"].upper(),
                "dominant_issue": item["dominant_issue"],
                "risk_score": item["risk_score"],
                "total_defects": item["total_defects"],
            }
            for item in records[-6:][::-1]
        ]

        aggregate_counts = Counter()
        aggregate_severity = Counter()
        for item in records:
            aggregate_counts.update(item["defect_breakdown"])
            aggregate_severity.update(item["severity_breakdown"])

        return {
            "status": status,
            "samples": self.list_samples(),
            "overview": overview,
            "charts": {
                "defect_types": [
                    {"name": ISSUE_LABELS[key], "value": type_breakdown.get(key, 0)}
                    for key in ("dust", "crack", "stain", "other")
                ],
                "severity": [
                    {"name": SEVERITY_LABELS[level], "value": severity_breakdown.get(level, 0)}
                    for level in SEVERITY_ORDER
                ],
                "panel_ranking": panel_ranking,
                "trend": trend_points,
                "runtime": {"labels": RUNTIME_LABELS, "values": runtime_chart},
                "aggregate_types": [
                    {"name": ISSUE_LABELS[key], "value": aggregate_counts.get(key, 0)}
                    for key in ("dust", "crack", "stain", "other")
                ],
                "aggregate_severity": [
                    {"name": SEVERITY_LABELS[level], "value": aggregate_severity.get(level, 0)}
                    for level in SEVERITY_ORDER
                ],
            },
            "recent_records": recent_records,
            "recommendations": recommendations,
            "latest_analysis": latest_detail["result"] if latest_detail else None,
        }

    def _build_analysis_payload(
        self,
        image_path: Path,
        overlay_name: str,
        panels: list[dict[str, Any]],
        detections: list[dict[str, Any]],
        total_ms: float,
    ) -> dict[str, Any]:
        defect_breakdown = Counter(item["type"] for item in detections)
        severity_breakdown = Counter(item["severity"] for item in detections)
        dust_coverage = min(
            100.0, round(sum(item["area_ratio"] for item in detections if item["type"] == "dust") * 100, 2)
        )
        stain_coverage = min(
            100.0, round(sum(item["area_ratio"] for item in detections if item["type"] == "stain") * 100, 2)
        )
        crack_length = round(
            sum(item.get("length_px", 0.0) for item in detections if item["type"] == "crack"), 2
        )
        crack_strength = self._calculate_crack_strength(panels, detections, crack_length)
        panel_stats = self._build_panel_stats(panels, detections)
        dirty_panels = sum(1 for item in panel_stats if item["risk_score"] > 0)
        severity_score = self._calculate_severity_score(detections=detections)
        dominant_issue = self._dominant_issue_from_detections(detections)
        avg_confidence = round(
            (sum(item["confidence"] for item in detections) / len(detections)) if detections else 0.0,
            3,
        )

        risk_score = self._calculate_risk_score(
            panel_stats=panel_stats,
            dust_coverage=dust_coverage,
            stain_coverage=stain_coverage,
            crack_strength=crack_strength,
            dirty_panels=dirty_panels,
            total_panels=len(panels),
            severity_score=severity_score,
            total_defects=len(detections),
        )

        panel_ranking = [
            {
                "name": item["id"],
                "risk": item["risk_score"],
                "label": f"{item['id']} ({item['risk_score']})",
            }
            for item in sorted(panel_stats, key=lambda item: item["risk_score"], reverse=True)[:8]
        ]

        recommendations = self._build_recommendations(
            dust_coverage=dust_coverage,
            stain_coverage=stain_coverage,
            crack_length=crack_length,
            dirty_panels=dirty_panels,
            total_panels=len(panels),
        )

        timestamp = datetime.now().isoformat(timespec="seconds")
        result_image_url = f"/api/results/{overlay_name}"
        history_entry = {
            "id": uuid.uuid4().hex[:12],
            "timestamp": timestamp,
            "filename": image_path.name,
            "mode": self._runtime_mode,
            "metrics_version": METRICS_VERSION,
            "panel_count": len(panels),
            "dirty_panels": dirty_panels,
            "total_defects": len(detections),
            "avg_confidence": avg_confidence,
            "dust_coverage": dust_coverage,
            "stain_coverage": stain_coverage,
            "crack_length": crack_length,
            "crack_strength": crack_strength,
            "risk_score": risk_score,
            "dominant_issue": dominant_issue,
            "defect_breakdown": {key: defect_breakdown.get(key, 0) for key in ISSUE_LABELS},
            "severity_breakdown": {level: severity_breakdown.get(level, 0) for level in SEVERITY_ORDER},
            "panel_ranking": panel_ranking,
            "panel_stats": panel_stats,
            "recommendations": recommendations,
            "runtime_ms": {
                "panel": round(self._last_runtime["panel_ms"], 2),
                "defect": round(self._last_runtime["defect_ms"], 2),
                "render": round(self._last_runtime["render_ms"], 2),
                "total": round(total_ms, 2),
            },
            "result_image_url": result_image_url,
        }

        return {
            "result": {
                "mode": self._runtime_mode,
                "filename": image_path.name,
                "image_url": result_image_url,
                "panels": panels,
                "detections": detections,
                "summary": {
                    "panel_count": len(panels),
                    "dirty_panels": dirty_panels,
                    "total_defects": len(detections),
                    "avg_confidence": avg_confidence,
                    "dust_coverage": dust_coverage,
                    "stain_coverage": stain_coverage,
                    "crack_length": crack_length,
                    "crack_strength": crack_strength,
                    "risk_score": risk_score,
                    "dominant_issue": dominant_issue,
                },
                "panel_stats": panel_stats,
                "recommendations": recommendations,
                "runtime_ms": history_entry["runtime_ms"],
            },
            "history_entry": history_entry,
        }

    def _build_recommendations(
        self,
        dust_coverage: float,
        stain_coverage: float,
        crack_length: float,
        dirty_panels: int,
        total_panels: int,
    ) -> list[str]:
        advice = []
        if dust_coverage >= 12:
            advice.append("灰尘覆盖率偏高，建议优先安排清洗任务，并复核阵列倾角与排灰条件。")
        elif dust_coverage >= 5:
            advice.append("存在中度积灰，建议纳入下一轮例行清洁计划。")

        if stain_coverage >= 8:
            advice.append("生物污渍面积较大，建议结合人工复检定位污染源并做好局部清洁。")
        elif stain_coverage >= 3:
            advice.append("检测到零散生物污渍，可在低峰时段安排点状处理。")

        if crack_length >= 80:
            advice.append("裂痕长度累计较高，建议尽快安排人工复检并评估组件更换风险。")
        elif crack_length >= 20:
            advice.append("存在疑似裂痕，应重点关注局部热点和功率衰减趋势。")

        if total_panels and dirty_panels / total_panels >= 0.5:
            advice.append("异常面板占比较高，建议按阵列分区生成清洁与检修工单。")

        if not advice:
            advice.append("当前图像未见明显高风险缺陷，可继续保持例行巡检频率。")
        return advice

    def _can_use_yolo(self) -> bool:
        return (
            not self.config.force_demo_mode
            and YOLO is not None
            and self.config.panel_model_path.exists()
            and (
                self.config.tile_classifier_model_path.exists()
                or self.config.defect_model_path.exists()
            )
        )

    def _can_use_tile_classifier(self) -> bool:
        return (
            YOLO is not None
            and self.config.panel_model_path.exists()
            and self.config.tile_classifier_model_path.exists()
        )

    def _resolve_yolo_runtime_mode(self) -> str:
        if self._can_use_tile_classifier():
            return "yolo-tile"
        if YOLO is not None and self.config.panel_model_path.exists() and self.config.defect_model_path.exists():
            return "yolo"
        return "demo"

    def _load_panel_model(self):
        if self._panel_model is None:
            self._panel_model = YOLO(str(self.config.panel_model_path))
        return self._panel_model

    def _load_defect_model(self):
        if self._defect_model is None:
            self._defect_model = YOLO(str(self.config.defect_model_path))
        return self._defect_model

    def _load_tile_classifier_model(self):
        if self._tile_classifier_model is None:
            self._tile_classifier_model = YOLO(str(self.config.tile_classifier_model_path))
        return self._tile_classifier_model

    def _run_yolo_pipeline(
        self,
        image_path: Path,
        image: Image.Image,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        width, height = image.size
        panel_model = self._load_panel_model()

        panel_started = time.perf_counter()
        panel_result = panel_model.predict(
            source=str(image_path),
            conf=self.config.confidence_threshold,
            device=self.config.device,
            verbose=False,
        )[0]
        self._last_runtime["panel_ms"] = (time.perf_counter() - panel_started) * 1000

        panels = self._parse_panel_predictions(panel_result, width, height)
        defect_started = time.perf_counter()
        if self._can_use_tile_classifier():
            self._runtime_mode = "yolo-tile"
            detections = self._run_tile_classifier_pipeline(image, panels, width, height)
        else:
            self._runtime_mode = "yolo"
            defect_model = self._load_defect_model()
            defect_result = defect_model.predict(
                source=str(image_path),
                conf=self.config.confidence_threshold,
                device=self.config.device,
                verbose=False,
            )[0]
            detections = self._parse_defect_predictions(defect_result, panels, width, height)

        self._last_runtime["defect_ms"] = (time.perf_counter() - defect_started) * 1000
        return self._strip_internal_panel_fields(panels), detections

    def _parse_panel_predictions(
        self,
        result: Any,
        width: int,
        height: int,
    ) -> list[dict[str, Any]]:
        boxes = []
        if getattr(result, "boxes", None) is not None and getattr(result.boxes, "xyxy", None) is not None:
            boxes = result.boxes.xyxy.cpu().tolist()
        confidences = result.boxes.conf.cpu().tolist() if getattr(getattr(result, "boxes", None), "conf", None) is not None else []
        masks_xy = []
        if getattr(result, "masks", None) is not None and getattr(result.masks, "xy", None) is not None:
            masks_xy = [polygon.tolist() for polygon in result.masks.xy]
        masks = self._extract_panel_masks(result, width, height)

        panels = []
        for index, box in enumerate(boxes):
            x1, y1, x2, y2 = [float(value) for value in box]
            mask = masks[index] if index < len(masks) else self._bbox_mask([x1, y1, x2, y2], width, height)
            panels.append(
                {
                    "id": f"Panel-{index + 1}",
                    "bbox": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)],
                    "polygon": masks_xy[index] if index < len(masks_xy) else None,
                    "area": round(max(1.0, float(mask.sum()) if mask is not None else (x2 - x1) * (y2 - y1)), 2),
                    "confidence": round(float(confidences[index]) if index < len(confidences) else 0.0, 3),
                    "_mask": mask,
                }
            )

        if panels:
            return self._sort_panels_top_left_to_bottom_right(self._filter_overlapping_panels(panels, width, height))

        return [
            {
                "id": "Panel-1",
                "bbox": [0.0, 0.0, float(width), float(height)],
                "polygon": None,
                "area": float(width * height),
                "_mask": np.ones((height, width), dtype=bool),
            }
        ]

    def _extract_panel_masks(self, result: Any, width: int, height: int) -> list[np.ndarray]:
        masks = []
        raw_masks = getattr(getattr(result, "masks", None), "data", None)
        if raw_masks is None:
            return masks
        for raw_mask in raw_masks:
            mask_array = raw_mask.cpu().numpy()
            mask_image = Image.fromarray((mask_array > 0.5).astype(np.uint8) * 255)
            resized = mask_image.resize((width, height), Image.Resampling.NEAREST)
            masks.append(np.asarray(resized) > 0)
        return masks

    def _bbox_mask(self, bbox: list[float], width: int, height: int) -> np.ndarray:
        x1, y1, x2, y2 = bbox
        left = max(0, min(width, int(math.floor(x1))))
        top = max(0, min(height, int(math.floor(y1))))
        right = max(left + 1, min(width, int(math.ceil(x2))))
        bottom = max(top + 1, min(height, int(math.ceil(y2))))
        mask = np.zeros((height, width), dtype=bool)
        mask[top:bottom, left:right] = True
        return mask

    def _strip_internal_panel_fields(self, panels: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [{key: value for key, value in panel.items() if not key.startswith("_")} for panel in panels]

    def _filter_overlapping_panels(self, panels: list[dict[str, Any]], width: int, height: int) -> list[dict[str, Any]]:
        kept = []
        image_area = max(1.0, width * height)
        for panel in sorted(panels, key=lambda item: float(item.get("confidence", 0.0)), reverse=True):
            x1, y1, x2, y2 = panel["bbox"]
            box_width = max(1.0, x2 - x1)
            box_height = max(1.0, y2 - y1)
            if (
                float(panel.get("area", 0.0)) / image_area < 0.025
                or box_width / max(1.0, box_height) < 0.18
                or box_height / max(1.0, box_width) < 0.18
            ):
                continue
            panel_mask = panel.get("_mask")
            if panel_mask is None:
                kept.append(panel)
                continue
            panel_area = max(1, int(panel_mask.sum()))
            duplicate = False
            for kept_panel in kept:
                kept_mask = kept_panel.get("_mask")
                if kept_mask is None:
                    continue
                kx1, ky1, kx2, ky2 = kept_panel["bbox"]
                center_x = (x1 + x2) / 2.0
                center_y = (y1 + y2) / 2.0
                if (
                    kx1 <= center_x <= kx2
                    and ky1 <= center_y <= ky2
                    and float(panel.get("area", 0.0)) < float(kept_panel.get("area", 0.0)) * 0.30
                ):
                    duplicate = True
                    break
                kept_area = max(1, int(kept_mask.sum()))
                intersection = int(np.logical_and(panel_mask, kept_mask).sum())
                union = max(1, panel_area + kept_area - intersection)
                iou = intersection / union
                containment = intersection / max(1, min(panel_area, kept_area))
                if iou >= 0.40 or containment >= 0.55:
                    duplicate = True
                    break
            if not duplicate:
                kept.append(panel)
        return kept

    def _run_tile_classifier_pipeline(
        self,
        image: Image.Image,
        panels: list[dict[str, Any]],
        width: int,
        height: int,
    ) -> list[dict[str, Any]]:
        classifier = self._load_tile_classifier_model()
        rgb_array = np.asarray(image.convert("RGB"), dtype=np.uint8)
        tile_size = self._tile_size(width, height)
        detections = []

        for panel in panels:
            panel_tiles = self._collect_panel_tiles(rgb_array, panel, tile_size, width, height)
            if not panel_tiles:
                continue

            tile_images = [tile["image"] for tile in panel_tiles]
            results = []
            for batch_start in range(0, len(tile_images), 64):
                batch = tile_images[batch_start : batch_start + 64]
                results.extend(
                    classifier.predict(
                        source=batch,
                        imgsz=64,
                        device=self.config.device,
                        verbose=False,
                    )
                )

            classified_tiles = []
            for tile, result in zip(panel_tiles, results):
                level, confidence = self._parse_tile_classification(result)
                classified_tiles.append(
                    {
                        "bbox": tile["bbox"],
                        "level": level,
                        "confidence": confidence,
                        "mask_pixels": tile["mask_pixels"],
                    }
                )

            detection = self._build_tile_detection(panel, classified_tiles, width, height)
            if detection:
                detections.append(detection)

        return detections

    def _tile_size(self, width: int, height: int) -> int:
        return 32 if max(width, height) < 1000 else 40

    def _collect_panel_tiles(
        self,
        image_array: np.ndarray,
        panel: dict[str, Any],
        tile_size: int,
        width: int,
        height: int,
    ) -> list[dict[str, Any]]:
        mask = panel.get("_mask")
        if mask is None:
            mask = self._bbox_mask(panel["bbox"], width, height)
        x1, y1, x2, y2 = panel["bbox"]
        left = max(0, min(width - 1, int(math.floor(x1))))
        top = max(0, min(height - 1, int(math.floor(y1))))
        right = max(left + 1, min(width, int(math.ceil(x2))))
        bottom = max(top + 1, min(height, int(math.ceil(y2))))

        tiles = []
        for tile_y in range(top, bottom, tile_size):
            for tile_x in range(left, right, tile_size):
                tile_right = min(tile_x + tile_size, right)
                tile_bottom = min(tile_y + tile_size, bottom)
                tile_mask = mask[tile_y:tile_bottom, tile_x:tile_right]
                tile_area = max(1, tile_mask.size)
                mask_pixels = int(tile_mask.sum())
                if mask_pixels / tile_area < self.config.tile_min_mask_ratio:
                    continue
                tile_rgb = image_array[tile_y:tile_bottom, tile_x:tile_right].copy()
                tile_rgb[~tile_mask] = 0
                tiles.append(
                    {
                        "bbox": [float(tile_x), float(tile_y), float(tile_right), float(tile_bottom)],
                        "image": Image.fromarray(tile_rgb),
                        "mask_pixels": mask_pixels,
                    }
                )
        return tiles

    def _parse_tile_classification(self, result: Any) -> tuple[str, float]:
        probs = getattr(result, "probs", None)
        if probs is None:
            return "low", 0.0
        class_id = int(getattr(probs, "top1", 0))
        top1_conf = getattr(probs, "top1conf", 0.0)
        if hasattr(top1_conf, "cpu"):
            confidence = float(top1_conf.cpu())
        else:
            confidence = float(top1_conf)

        names = result.names if hasattr(result, "names") else {}
        if isinstance(names, dict):
            raw_name = names.get(class_id, str(class_id))
        elif isinstance(names, list) and 0 <= class_id < len(names):
            raw_name = names[class_id]
        else:
            raw_name = str(class_id)
        return self._normalize_tile_level(raw_name), round(confidence, 3)

    def _normalize_tile_level(self, raw_name: str) -> str:
        lowered = raw_name.strip().lower()
        if "high" in lowered or "严重" in lowered:
            return "high"
        if "moderate" in lowered or "medium" in lowered or "中" in lowered:
            return "medium"
        return "low"

    def _build_tile_detection(
        self,
        panel: dict[str, Any],
        classified_tiles: list[dict[str, Any]],
        width: int,
        height: int,
    ) -> dict[str, Any] | None:
        panel_area = max(1.0, float(panel["area"]))
        image_area = max(1.0, width * height)
        total_pixels = max(1, sum(int(tile["mask_pixels"]) for tile in classified_tiles))
        weighted_pixels = 0.0
        confidence_sum = 0.0
        level_pixels = {"low": 0, "medium": 0, "high": 0}

        tile_regions = []
        for tile in classified_tiles:
            level = tile["level"]
            mask_pixels = int(tile["mask_pixels"])
            weighted_pixels += mask_pixels * TILE_LEVEL_WEIGHTS[level]
            confidence_sum += mask_pixels * float(tile["confidence"])
            level_pixels[level] += mask_pixels
            tile_regions.append(
                {
                    "bbox": tile["bbox"],
                    "level": level,
                    "confidence": tile["confidence"],
                }
            )

        panel_coverage_ratio = min(1.0, weighted_pixels / total_pixels)
        if panel_coverage_ratio < 0.05 and level_pixels["medium"] == 0 and level_pixels["high"] == 0:
            return None

        high_ratio = level_pixels["high"] / total_pixels
        medium_high_ratio = (level_pixels["medium"] + level_pixels["high"]) / total_pixels
        if high_ratio >= 0.08 or panel_coverage_ratio >= 0.35:
            severity = "high"
        elif medium_high_ratio >= 0.08 or panel_coverage_ratio >= 0.16:
            severity = "medium"
        else:
            severity = "low"

        area_ratio = round(min(1.0, panel_coverage_ratio * panel_area / image_area), 4)
        confidence = round(confidence_sum / total_pixels, 3)
        risk_score = self._risk_for_detection("dust", confidence, area_ratio, 0.0, severity)
        return {
            "type": "dust",
            "label": ISSUE_LABELS["dust"],
            "confidence": confidence,
            "severity": severity,
            "severity_label": SEVERITY_LABELS[severity],
            "bbox": panel["bbox"],
            "polygon": None,
            "panel_id": panel["id"],
            "area_ratio": area_ratio,
            "panel_coverage_ratio": round(panel_coverage_ratio, 4),
            "length_px": 0.0,
            "length_ratio": 0.0,
            "risk_score": risk_score,
            "tile_regions": tile_regions,
            "tile_breakdown": {
                level: round(level_pixels[level] / total_pixels, 4)
                for level in ("low", "medium", "high")
            },
        }

    def _parse_defect_predictions(
        self,
        result: Any,
        panels: list[dict[str, Any]],
        width: int,
        height: int,
    ) -> list[dict[str, Any]]:
        detections = []
        if getattr(result, "boxes", None) is None or getattr(result.boxes, "xyxy", None) is None:
            return detections

        names = result.names if hasattr(result, "names") else {}
        boxes = result.boxes.xyxy.cpu().tolist()
        confidences = result.boxes.conf.cpu().tolist() if getattr(result.boxes, "conf", None) is not None else []
        classes = result.boxes.cls.cpu().tolist() if getattr(result.boxes, "cls", None) is not None else []
        masks_xy = []
        if getattr(result, "masks", None) is not None and getattr(result.masks, "xy", None) is not None:
            masks_xy = [polygon.tolist() for polygon in result.masks.xy]

        image_area = max(1.0, width * height)
        for index, box in enumerate(boxes):
            x1, y1, x2, y2 = [float(value) for value in box]
            class_id = int(classes[index]) if index < len(classes) else -1
            if isinstance(names, dict):
                raw_name = names.get(class_id, str(class_id))
            elif isinstance(names, list) and 0 <= class_id < len(names):
                raw_name = names[class_id]
            else:
                raw_name = str(class_id)
            defect_type = self._normalize_issue_name(raw_name)
            bbox_area = max(1.0, (x2 - x1) * (y2 - y1))
            polygon = masks_xy[index] if index < len(masks_xy) else None
            area_ratio = round((self._polygon_area(polygon) if polygon else bbox_area) / image_area, 4)
            confidence = round(float(confidences[index]) if index < len(confidences) else 0.0, 3)
            panel_id = self._match_panel([x1, y1, x2, y2], panels)
            panel = next((item for item in panels if item["id"] == panel_id), panels[0])
            panel_area = max(1.0, float(panel["area"]))
            length_px = round(math.hypot(x2 - x1, y2 - y1), 2) if defect_type == "crack" else 0.0
            panel_coverage_ratio = round(min(1.0, (self._polygon_area(polygon) if polygon else bbox_area) / panel_area), 4)
            length_ratio = (
                round(min(1.0, length_px / max(self._panel_diagonal(panel), 1.0)), 4)
                if defect_type == "crack"
                else 0.0
            )
            severity = self._severity_for_detection(defect_type, area_ratio, length_px)
            risk_score = self._risk_for_detection(defect_type, confidence, area_ratio, length_px, severity)
            detections.append(
                {
                    "type": defect_type,
                    "label": ISSUE_LABELS.get(defect_type, raw_name),
                    "confidence": confidence,
                    "severity": severity,
                    "severity_label": SEVERITY_LABELS[severity],
                    "bbox": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)],
                    "polygon": polygon,
                    "panel_id": panel_id,
                    "area_ratio": area_ratio,
                    "panel_coverage_ratio": panel_coverage_ratio,
                    "length_px": length_px,
                    "length_ratio": length_ratio,
                    "risk_score": risk_score,
                }
            )
        return detections

    def _run_demo_pipeline(self, image: Image.Image) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        width, height = image.size
        arr = np.asarray(image.convert("RGB"), dtype=np.float32)

        panels = self._build_demo_surface_panels(arr, width, height)

        detections = []
        panel_feature_scores = []
        for panel_index, panel in enumerate(panels):
            features = self._compute_demo_panel_features(panel, arr, width, height)
            panel_feature_scores.append(features)
            detections.extend(self._build_demo_detections_for_panel(panel, panel_index, features, width, height))

        mean_dust = sum(item["dust"] for item in panel_feature_scores) / max(1, len(panel_feature_scores))
        mean_stain = sum(item["stain"] for item in panel_feature_scores) / max(1, len(panel_feature_scores))
        self._last_runtime["panel_ms"] = round(16 + mean_dust * 60 + mean_stain * 18, 2)
        self._last_runtime["defect_ms"] = round(20 + mean_dust * 26 + mean_stain * 48, 2)
        return panels, detections

    def _build_demo_surface_panels(self, image_array: np.ndarray, image_width: int, image_height: int) -> list[dict[str, Any]]:
        x1, y1, x2, y2 = self._estimate_demo_surface_bbox(image_array, image_width, image_height)
        return [
            {
                "id": "Panel-1",
                "bbox": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)],
                "polygon": None,
                "area": round(max(1.0, (x2 - x1) * (y2 - y1)), 2),
            }
        ]

    def _estimate_demo_surface_bbox(
        self,
        image_array: np.ndarray,
        image_width: int,
        image_height: int,
    ) -> tuple[float, float, float, float]:
        gray = image_array.mean(axis=2) / 255.0
        grad_y = np.abs(np.diff(gray, axis=0, prepend=gray[:1, :]))
        grad_x = np.abs(np.diff(gray, axis=1, prepend=gray[:, :1]))
        texture = grad_x + grad_y
        threshold = max(0.018, float(np.percentile(texture, 72)))
        mask = (texture >= threshold) & (gray > 0.08) & (gray < 0.96)

        if not np.any(mask):
            return (0.0, 0.0, float(image_width), float(image_height))

        ys, xs = np.where(mask)
        x1 = float(xs.min())
        y1 = float(ys.min())
        x2 = float(xs.max() + 1)
        y2 = float(ys.max() + 1)
        pad_x = image_width * 0.025
        pad_y = image_height * 0.025
        x1 = max(0.0, x1 - pad_x)
        y1 = max(0.0, y1 - pad_y)
        x2 = min(float(image_width), x2 + pad_x)
        y2 = min(float(image_height), y2 + pad_y)

        area_ratio = ((x2 - x1) * (y2 - y1)) / max(1.0, image_width * image_height)
        if area_ratio < 0.35:
            return (0.0, 0.0, float(image_width), float(image_height))
        return (x1, y1, x2, y2)

    def _draw_overlay(
        self,
        image: Image.Image,
        panels: list[dict[str, Any]],
        detections: list[dict[str, Any]],
        overlay_path: Path,
    ) -> None:
        base = image.copy().convert("RGBA")
        overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay, "RGBA")

        for panel in panels:
            x1, y1, x2, y2 = panel["bbox"]
            draw.rectangle([x1, y1, x2, y2], outline=(52, 152, 219, 220), width=3)
            draw.text((x1 + 6, y1 + 6), panel["id"], fill=(235, 245, 251, 255))

        for detection in detections:
            color = ISSUE_COLORS.get(detection["type"], ISSUE_COLORS["other"])
            if detection["type"] == "dust":
                coverage = float(detection.get("panel_coverage_ratio", 0.0))
                color = color[:3] + (int(min(115, max(45, 55 + coverage * 150))),)
            x1, y1, x2, y2 = detection["bbox"]
            tile_regions = detection.get("tile_regions") or []
            if tile_regions:
                for region in tile_regions:
                    rx1, ry1, rx2, ry2 = region["bbox"]
                    region_color = TILE_LEVEL_COLORS.get(region["level"], color)
                    draw.rectangle([rx1, ry1, rx2, ry2], fill=region_color)
                draw.rectangle([x1, y1, x2, y2], outline=color[:3] + (255,), width=3)
            elif detection["polygon"]:
                polygon = [tuple(point) for point in detection["polygon"]]
                draw.polygon(polygon, fill=color, outline=color[:3] + (255,))
            else:
                draw.rectangle([x1, y1, x2, y2], outline=color[:3] + (255,), width=4)
            label = f"{detection['label']} {int(detection['confidence'] * 100)}%"
            text_y = max(0, y1 - 18)
            draw.rectangle([x1, text_y, x1 + max(90, len(label) * 10), text_y + 18], fill=color)
            draw.text((x1 + 4, text_y + 2), label, fill=(0, 15, 42, 255))

        canvas = Image.alpha_composite(base, overlay)
        canvas.save(overlay_path)

    def _normalize_issue_name(self, raw_name: str) -> str:
        lowered = raw_name.strip().lower()
        for keyword, normalized in MODEL_ALIASES.items():
            if keyword in lowered:
                return normalized
        return "other"

    def _match_panel(self, bbox: list[float], panels: list[dict[str, Any]]) -> str:
        center_x = (bbox[0] + bbox[2]) / 2
        center_y = (bbox[1] + bbox[3]) / 2
        for panel in panels:
            x1, y1, x2, y2 = panel["bbox"]
            if x1 <= center_x <= x2 and y1 <= center_y <= y2:
                return panel["id"]
        return panels[0]["id"]

    def _polygon_area(self, polygon: list[list[float]] | None) -> float:
        if not polygon or len(polygon) < 3:
            return 0.0
        points = np.asarray(polygon)
        x = points[:, 0]
        y = points[:, 1]
        return abs(float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))) / 2.0)

    def _compute_demo_panel_features(
        self,
        panel: dict[str, Any],
        image_array: np.ndarray,
        image_width: int,
        image_height: int,
    ) -> dict[str, float]:
        x1, y1, x2, y2 = panel["bbox"]
        left = max(0, min(image_width - 1, int(round(x1))))
        top = max(0, min(image_height - 1, int(round(y1))))
        right = max(left + 1, min(image_width, int(round(x2))))
        bottom = max(top + 1, min(image_height, int(round(y2))))

        panel_rgb = image_array[top:bottom, left:right] / 255.0
        red = panel_rgb[:, :, 0]
        green = panel_rgb[:, :, 1]
        blue = panel_rgb[:, :, 2]
        value = np.max(panel_rgb, axis=2)
        minimum = np.min(panel_rgb, axis=2)
        saturation = np.where(value > 1e-6, (value - minimum) / np.maximum(value, 1e-6), 0.0)

        panel_gray = panel_rgb.mean(axis=2)
        brightness = float(panel_gray.mean())
        contrast = float(panel_gray.std())
        edge_vertical = float(np.abs(np.diff(panel_gray, axis=0)).mean()) if panel_gray.shape[0] > 1 else 0.0
        edge_horizontal = float(np.abs(np.diff(panel_gray, axis=1)).mean()) if panel_gray.shape[1] > 1 else 0.0
        edge_strength = edge_vertical + edge_horizontal

        green_bias = float(((green - red).mean() + (green - blue).mean()) / 2.0)
        warm_bias = float(((red - blue).mean() + (green - blue).mean()) / 2.0)
        blue_dominance = blue - np.maximum(red, green)
        blue_baseline = float(np.median(blue_dominance))
        value_mean = float(value.mean())
        sat_mean = float(saturation.mean())

        # Dust is modeled as warm yellow-brown coverage or a neutral gray haze on top of blue panels.
        warm_dust_mask = (
            (red > blue * 1.10)
            & (green > blue * 1.06)
            & (red > 0.34)
            & (green > 0.30)
            & (value > 0.26)
        )
        neutral_dust_mask = (
            (blue_dominance < blue_baseline - 0.14)
            & (np.abs(red - green) < 0.09)
            & (np.abs(red - blue) < 0.18)
            & (saturation < min(0.18, sat_mean + 0.03))
            & (value > 0.18)
            & (value < value_mean + 0.06)
        )
        diffuse_dust_mask = (
            (panel_gray > 0.26)
            & (panel_gray < 0.84)
            & (saturation < 0.36)
            & (blue_dominance < 0.12)
            & (value > 0.20)
        )
        diffuse_dust_ratio = float(diffuse_dust_mask.mean()) if diffuse_dust_mask.size else 0.0
        dust_mask = warm_dust_mask | neutral_dust_mask

        # Bio-pollution is dominated by green blobs or bright white droppings.
        green_stain_mask = (green > red * 1.18) & (green > blue * 1.12) & (green > 0.30) & (saturation > 0.18)
        white_stain_mask = (
            (value > max(0.76, value_mean + 0.16))
            & (np.abs(red - green) < 0.08)
            & (np.abs(green - blue) < 0.12)
            & (saturation < 0.16)
            & (blue_dominance < 0.03)
        )
        stain_mask = (green_stain_mask | white_stain_mask) & (value > 0.12)
        stain_bbox = self._mask_bbox_relative(stain_mask)
        stain_extent_ratio = 0.0
        if stain_bbox:
            rx1, ry1, rx2, ry2 = stain_bbox
            stain_extent_ratio = max(0.0, (rx2 - rx1) * (ry2 - ry1))
        # Bio-pollution should remain local; full-panel coverage is treated as dust/haze instead.
        if stain_mask.size and (float(stain_mask.mean()) > 0.22 or stain_extent_ratio > 0.28):
            stain_mask = np.zeros_like(stain_mask, dtype=bool)
            stain_bbox = None
            stain_extent_ratio = 0.0

        # Give stain precedence over dust when both hit the same pixels.
        dust_mask = dust_mask & ~stain_mask
        dust_bbox_mask = dust_mask
        if diffuse_dust_ratio >= 0.35 and brightness >= 0.26:
            dust_bbox_mask = (dust_mask | diffuse_dust_mask) & ~stain_mask

        raw_dust_ratio = float(dust_mask.mean()) if dust_mask.size else 0.0
        diffuse_dust_coverage = min(0.55, diffuse_dust_ratio * 0.42) if brightness >= 0.26 else 0.0
        dust_ratio = max(raw_dust_ratio, diffuse_dust_coverage)
        stain_ratio = float(stain_mask.mean()) if stain_mask.size else 0.0
        dust_compactness = self._mask_compactness(dust_bbox_mask)
        stain_compactness = self._mask_compactness(stain_mask)
        chroma = float((np.abs(red - green).mean() + np.abs(green - blue).mean() + np.abs(red - blue).mean()) / 3.0)

        dust_score = float(
            np.clip(
                (
                    dust_ratio * 2.15
                    + max(warm_bias, 0.0) * 0.42
                    + max(0.0, 0.06 - blue_baseline) * 0.18
                    + contrast * 0.12
                )
                * (0.42 + dust_compactness),
                0.0,
                0.34,
            )
        )
        stain_score = 0.0
        if stain_bbox is not None and stain_ratio >= 0.008:
            stain_score = float(
                np.clip(
                    (stain_ratio * 3.2 + max(green_bias, 0.0) * 0.95 + chroma * 0.10)
                    * (0.28 + stain_compactness * 1.05),
                    0.0,
                    0.30,
                )
            )

        return {
            "brightness": brightness,
            "contrast": contrast,
            "edge_strength": edge_strength,
            "dust_mask_bbox": self._mask_bbox_relative(dust_bbox_mask),
            "stain_mask_bbox": stain_bbox,
            "dust_ratio": dust_ratio,
            "stain_ratio": stain_ratio,
            "dust": dust_score,
            "crack": 0.0,
            "stain": stain_score,
        }

    def _build_demo_detections_for_panel(
        self,
        panel: dict[str, Any],
        panel_index: int,
        feature_scores: dict[str, float],
        image_width: int,
        image_height: int,
    ) -> list[dict[str, Any]]:
        thresholds = {"dust": 0.050, "stain": 0.028}
        detections = []
        for issue_type in ("dust", "stain"):
            score = float(feature_scores[issue_type])
            if score < thresholds[issue_type]:
                continue
            detections.append(
                self._build_demo_detection(panel, panel_index, issue_type, score, feature_scores, image_width, image_height)
            )
        return detections

    def _build_demo_detection(
        self,
        panel: dict[str, Any],
        panel_index: int,
        issue_type: str,
        score: float,
        feature_scores: dict[str, float],
        image_width: int,
        image_height: int,
    ) -> dict[str, Any]:
        x1, y1, x2, y2 = panel["bbox"]
        panel_w = x2 - x1
        panel_h = y2 - y1
        panel_area = max(1.0, float(panel["area"]))
        image_area = max(1.0, image_width * image_height)
        bbox_rel = feature_scores.get(f"{issue_type}_mask_bbox")
        coverage_ratio = float(feature_scores.get(f"{issue_type}_ratio", 0.0))
        phase = (panel_index % 3) * 0.02

        if bbox_rel:
            rx1, ry1, rx2, ry2 = bbox_rel
            bx1 = x1 + panel_w * rx1
            by1 = y1 + panel_h * ry1
            bx2 = x1 + panel_w * rx2
            by2 = y1 + panel_h * ry2
        else:
            default_scale = 0.34 if issue_type == "dust" else 0.20
            bw = panel_w * (default_scale + score * 0.65)
            bh = panel_h * (default_scale * 0.7 + score * 0.45)
            bx1 = x1 + panel_w * (0.12 + phase)
            by1 = y1 + panel_h * (0.16 + phase * 0.7)
            bx2 = min(x2 - panel_w * 0.06, bx1 + bw)
            by2 = min(y2 - panel_h * 0.06, by1 + bh)

        bbox = [round(bx1, 2), round(by1, 2), round(bx2, 2), round(by2, 2)]
        polygon = [
            [round(bx1, 2), round(by1 + panel_h * 0.03, 2)],
            [round(bx2, 2), round(by1, 2)],
            [round(bx2 - panel_w * 0.04, 2), round(by2, 2)],
            [round(bx1 + panel_w * 0.04, 2), round(by2 - panel_h * 0.03, 2)],
        ]
        if bbox_rel:
            panel_coverage_ratio = round(min(1.0, max(0.0, coverage_ratio)), 4)
        else:
            panel_coverage_ratio = round(min(1.0, max(coverage_ratio, self._polygon_area(polygon) / panel_area)), 4)
        area_ratio = round(min(1.0, panel_coverage_ratio * panel_area / image_area), 4)
        length_px = 0.0
        confidence = round(
            min(0.98, (0.79 if issue_type == "dust" else 0.76) + score * 0.70 + panel_coverage_ratio * 0.35),
            3,
        )

        severity = self._severity_for_detection(issue_type, area_ratio, length_px)
        return {
            "type": issue_type,
            "label": ISSUE_LABELS[issue_type],
            "confidence": confidence,
            "severity": severity,
            "severity_label": SEVERITY_LABELS[severity],
            "bbox": bbox,
            "polygon": polygon,
            "panel_id": panel["id"],
            "area_ratio": area_ratio,
            "panel_coverage_ratio": panel_coverage_ratio,
            "length_px": length_px,
            "length_ratio": 0.0,
            "risk_score": self._risk_for_detection(issue_type, confidence, area_ratio, length_px, severity),
        }

    def _mask_bbox_relative(self, mask: np.ndarray) -> tuple[float, float, float, float] | None:
        if mask.size == 0 or not np.any(mask):
            return None
        ys, xs = np.where(mask)
        if ys.size < 12 or xs.size < 12:
            return None
        height, width = mask.shape[:2]
        return (
            float(xs.min()) / max(width, 1),
            float(ys.min()) / max(height, 1),
            float(xs.max() + 1) / max(width, 1),
            float(ys.max() + 1) / max(height, 1),
        )

    def _mask_compactness(self, mask: np.ndarray) -> float:
        if mask.size == 0 or not np.any(mask):
            return 0.0
        ys, xs = np.where(mask)
        bbox_area = max(1, (int(xs.max()) - int(xs.min()) + 1) * (int(ys.max()) - int(ys.min()) + 1))
        return min(1.0, float(ys.size) / float(bbox_area))

    def _sort_panels_top_left_to_bottom_right(self, panels: list[dict[str, Any]]) -> list[dict[str, Any]]:
        sorted_panels = sorted(panels, key=lambda item: self._panel_anchor(item))
        normalized = []
        for index, panel in enumerate(sorted_panels, start=1):
            normalized_panel = dict(panel)
            normalized_panel["id"] = f"Panel-{index}"
            normalized.append(normalized_panel)
        return normalized

    def _panel_anchor(self, panel: dict[str, Any]) -> tuple[float, float]:
        polygon = panel.get("polygon")
        if polygon:
            xs = [float(point[0]) for point in polygon]
            ys = [float(point[1]) for point in polygon]
            return (sum(ys) / len(ys), sum(xs) / len(xs))
        x1, y1, x2, y2 = panel["bbox"]
        return ((y1 + y2) / 2.0, (x1 + x2) / 2.0)

    def _calculate_crack_strength(
        self,
        panels: list[dict[str, Any]],
        detections: list[dict[str, Any]],
        crack_length: float,
    ) -> float:
        crack_detections = [item for item in detections if item["type"] == "crack"]
        if not crack_detections:
            return 0.0

        panel_lookup = {panel["id"]: panel for panel in panels}
        cracked_panels = set()
        relative_lengths = []
        panel_coverages = []
        severity_values = []
        confidence_values = []

        for detection in crack_detections:
            panel = panel_lookup.get(detection["panel_id"])
            panel_diagonal = self._panel_diagonal(panel) if panel else 0.0
            if panel_diagonal <= 0:
                panel_diagonal = max(crack_length, 1.0)

            cracked_panels.add(detection["panel_id"])
            relative_lengths.append(
                float(
                    detection.get(
                        "length_ratio",
                        min(1.0, detection.get("length_px", 0.0) / panel_diagonal),
                    )
                )
            )
            panel_coverages.append(float(detection.get("panel_coverage_ratio", 0.0)))
            severity_values.append({"low": 35.0, "medium": 65.0, "high": 90.0}[detection.get("severity", "low")])
            confidence_values.append(float(detection.get("confidence", 0.0)) * 100.0)

        if not relative_lengths:
            return self._estimate_crack_strength_from_length(crack_length)

        avg_relative_length = sum(relative_lengths) / len(relative_lengths)
        avg_panel_coverage = sum(panel_coverages) / len(panel_coverages) if panel_coverages else 0.0
        cracked_panel_ratio = len(cracked_panels) / max(1, len(panels))
        avg_severity = sum(severity_values) / len(severity_values)
        avg_confidence = sum(confidence_values) / len(confidence_values)
        length_score = min(100.0, avg_relative_length * 100.0)

        return round(
            length_score * 0.40
            + avg_panel_coverage * 100.0 * 0.10
            + cracked_panel_ratio * 100.0 * 0.15
            + avg_severity * 0.25
            + avg_confidence * 0.10,
            2,
        )

    def _estimate_crack_strength_from_length(self, crack_length: float) -> float:
        if crack_length <= 0:
            return 0.0
        return round(100.0 * (1.0 - math.exp(-crack_length / 420.0)), 2)

    def _panel_diagonal(self, panel: dict[str, Any] | None) -> float:
        if not panel:
            return 0.0
        x1, y1, x2, y2 = panel["bbox"]
        return math.hypot(x2 - x1, y2 - y1)

    def _calculate_severity_score(
        self,
        detections: list[dict[str, Any]] | None = None,
        severity_breakdown: dict[str, int] | None = None,
    ) -> float:
        if detections is not None:
            breakdown = Counter(item["severity"] for item in detections)
            total = len(detections)
        else:
            breakdown = Counter(severity_breakdown or {})
            total = sum(int(value) for value in breakdown.values())

        if total <= 0:
            return 0.0

        severity_weights = {"low": 35.0, "medium": 65.0, "high": 90.0}
        return round(
            sum(breakdown.get(level, 0) * severity_weights[level] for level in SEVERITY_ORDER) / total,
            2,
        )

    def _calculate_risk_score(
        self,
        panel_stats: list[dict[str, Any]] | None,
        dust_coverage: float,
        stain_coverage: float,
        crack_strength: float,
        dirty_panels: int,
        total_panels: int,
        severity_score: float,
        total_defects: int,
    ) -> float:
        dirty_panel_ratio = dirty_panels / total_panels if total_panels else 0.0
        defect_density = min(100.0, (total_defects / max(total_panels, 1)) * 35.0)
        active_panel_stats = [item for item in (panel_stats or []) if float(item.get("risk_score", 0.0)) > 0]
        active_panel_avg = (
            sum(float(item["risk_score"]) for item in active_panel_stats) / len(active_panel_stats)
            if active_panel_stats
            else 0.0
        )
        coverage_mix = dust_coverage * 0.55 + stain_coverage * 0.45
        return round(
            min(
                100.0,
                active_panel_avg * 0.52
                + dirty_panel_ratio * 100.0 * 0.18
                + severity_score * 0.10
                + crack_strength * 0.10
                + coverage_mix * 0.06
                + defect_density * 0.04,
            ),
            2,
        )

    def _build_panel_stats(
        self,
        panels: list[dict[str, Any]],
        detections: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = {panel["id"]: [] for panel in panels}
        for detection in detections:
            grouped.setdefault(detection["panel_id"], []).append(detection)

        panel_stats = []
        for panel in panels:
            panel_detections = grouped.get(panel["id"], [])
            severity_counts = {level: 0 for level in SEVERITY_ORDER}
            issue_counts = {key: 0 for key in ISSUE_LABELS}

            for detection in panel_detections:
                severity_counts[detection["severity"]] += 1
                issue_counts[detection["type"]] += 1

            if panel_detections:
                severity_score = self._calculate_severity_score(detections=panel_detections)
                avg_confidence = sum(item["confidence"] for item in panel_detections) / len(panel_detections)
                coverage_ratio = min(
                    1.0,
                    sum(float(item.get("panel_coverage_ratio", 0.0)) for item in panel_detections),
                )
                max_coverage_ratio = max(float(item.get("panel_coverage_ratio", 0.0)) for item in panel_detections)
                risk_score = round(
                    min(
                        100.0,
                        severity_score * 0.58
                        + coverage_ratio * 100.0 * 0.22
                        + max_coverage_ratio * 100.0 * 0.10
                        + avg_confidence * 100.0 * 0.10,
                    ),
                    2,
                )
                dominant_issue_key = max(issue_counts, key=issue_counts.get)
                issue_impacts = {key: 0.0 for key in ISSUE_LABELS}
                for detection in panel_detections:
                    issue_impacts[detection['type']] += self._issue_impact(detection)
                dominant_issue_key = max(issue_impacts, key=issue_impacts.get)
            else:
                severity_score = 0.0
                avg_confidence = 0.0
                coverage_ratio = 0.0
                max_coverage_ratio = 0.0
                risk_score = 0.0
                dominant_issue_key = "other"

            panel_stats.append(
                {
                    "id": panel["id"],
                    "risk_score": risk_score,
                    "severity_score": round(severity_score, 2),
                    "level": self._severity_level_from_score(risk_score),
                    "level_label": self._severity_level_label_from_score(risk_score),
                    "detection_count": len(panel_detections),
                    "coverage_ratio": round(coverage_ratio, 4),
                    "max_coverage_ratio": round(max_coverage_ratio, 4),
                    "avg_confidence": round(avg_confidence, 3),
                    "dominant_issue": ISSUE_LABELS.get(dominant_issue_key, "暂无异常"),
                    "severity_breakdown": severity_counts,
                    "issue_breakdown": issue_counts,
                }
            )

        return panel_stats

    def _severity_level_from_score(self, risk_score: float) -> str:
        if risk_score >= 70:
            return "high"
        if risk_score >= 35:
            return "medium"
        return "low"

    def _severity_level_label_from_score(self, risk_score: float) -> str:
        return SEVERITY_LABELS[self._severity_level_from_score(risk_score)]

    def _dominant_issue_from_detections(self, detections: list[dict[str, Any]]) -> str:
        if not detections:
            return "暂无异常"
        issue_impacts = {key: 0.0 for key in ISSUE_LABELS}
        for detection in detections:
            issue_impacts[detection["type"]] += self._issue_impact(detection)
        dominant_issue_key = max(issue_impacts, key=issue_impacts.get)
        return ISSUE_LABELS.get(dominant_issue_key, "暂无异常")

    def _issue_impact(self, detection: dict[str, Any]) -> float:
        area_ratio = float(detection.get("area_ratio", 0.0))
        panel_coverage_ratio = float(detection.get("panel_coverage_ratio", 0.0))
        confidence = float(detection.get("confidence", 0.0))
        issue_type = detection.get("type", "other")
        weight = {"dust": 1.0, "stain": 1.35, "crack": 1.6, "other": 0.8}.get(issue_type, 0.8)
        return area_ratio * 100.0 * weight + panel_coverage_ratio * 30.0 * weight + confidence * 8.0

    def _normalize_record_metrics(self, record: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(record)
        crack_length = float(normalized.get("crack_length", 0.0) or 0.0)
        if normalized.get("metrics_version") == METRICS_VERSION:
            crack_strength = float(
                normalized.get("crack_strength", self._estimate_crack_strength_from_length(crack_length)) or 0.0
            )
        else:
            crack_strength = self._estimate_crack_strength_from_length(crack_length)
        severity_breakdown = normalized.get("severity_breakdown", {})
        severity_score = self._calculate_severity_score(severity_breakdown=severity_breakdown)
        panel_count = int(normalized.get("panel_count", 0) or 0)
        dirty_panels = int(normalized.get("dirty_panels", 0) or 0)
        total_defects = int(normalized.get("total_defects", 0) or 0)
        dust_coverage = float(normalized.get("dust_coverage", 0.0) or 0.0)
        stain_coverage = float(normalized.get("stain_coverage", 0.0) or 0.0)
        panel_stats = normalized.get("panel_stats") if isinstance(normalized.get("panel_stats"), list) else None

        normalized["crack_strength"] = round(crack_strength, 2)
        normalized["metrics_version"] = METRICS_VERSION
        normalized["risk_score"] = self._calculate_risk_score(
            panel_stats=panel_stats,
            dust_coverage=dust_coverage,
            stain_coverage=stain_coverage,
            crack_strength=crack_strength,
            dirty_panels=dirty_panels,
            total_panels=panel_count,
            severity_score=severity_score,
            total_defects=total_defects,
        )
        if panel_stats:
            normalized["panel_ranking"] = [
                {
                    "name": item["id"],
                    "risk": round(float(item.get("risk_score", 0.0)), 2),
                    "label": f"{item['id']} ({round(float(item.get('risk_score', 0.0)), 2)})",
                }
                for item in sorted(panel_stats, key=lambda item: float(item.get("risk_score", 0.0)), reverse=True)[:8]
            ]
        return normalized

    def _severity_for_detection(self, issue_type: str, area_ratio: float, length_px: float) -> str:
        if issue_type == "crack":
            if length_px >= 120:
                return "high"
            if length_px >= 50:
                return "medium"
            return "low"
        if area_ratio >= 0.08:
            return "high"
        if area_ratio >= 0.03:
            return "medium"
        return "low"

    def _risk_for_detection(
        self,
        issue_type: str,
        confidence: float,
        area_ratio: float,
        length_px: float,
        severity: str,
    ) -> float:
        base = {"dust": 28, "stain": 24, "crack": 38, "other": 18}.get(issue_type, 18)
        severity_bonus = {"low": 6, "medium": 14, "high": 24}[severity]
        geometry = length_px * 0.15 if issue_type == "crack" else area_ratio * 220
        return round(min(100.0, base + severity_bonus + confidence * 12 + geometry), 2)

