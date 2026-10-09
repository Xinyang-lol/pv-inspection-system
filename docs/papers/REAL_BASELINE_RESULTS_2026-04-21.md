# Real Baseline Results (2026-04-21)

## Environment

- Training runtime: `D:\yolo_v8\pv_defect_project\.venv\Scripts\python.exe`
- Ultralytics: `8.4.21`
- Torch: `2.10.0+cpu`
- CUDA: unavailable
- Note: all runs below were executed on CPU only, so they should be treated as quick reproducible baselines rather than final paper-grade training.

## Uploaded Dataset Summary

### 1. Panel Segmentation Dataset

- Source: `D:\大创yolo\yolo8 seg training data\Dataset`
- Prepared root: `D:\pv_temp\seg_dataset`
- Task: single-class segmentation
- Class: `panel`
- Split sizes:
  - train: `898`
  - val: `98`
  - test: `99`

### 2. Pollution Severity Classification Dataset

- Source: `D:\大创yolo\yolo8 cls training data\Dataset`
- Prepared root: `D:\pv_temp\cls_severity`
- Task: 3-class classification
- Classes: `0_High`, `1_Moderate`, `2_low`
- Split sizes:
  - `0_High`: train `2692`, val `299`, test `642`
  - `1_Moderate`: train `2702`, val `300`, test `644`
  - `2_low`: train `2661`, val `296`, test `635`

## Run 1: Panel Segmentation Baseline

- Model: `yolov8n-seg.pt`
- Command profile: `imgsz=320`, `batch=2`, `epochs=1`, `device=cpu`
- Run directory: `D:\pv_temp\training_runs\panel_seg_baseline_cpu_e1_i320`
- Metrics JSON: `D:\pv_temp\metrics\panel_seg_baseline_cpu_e1_i320.json`
- Best weights: `D:\pv_temp\training_runs\panel_seg_baseline_cpu_e1_i320\weights\best.pt`

### Test Metrics

- Box Precision: `0.6008`
- Box Recall: `0.5516`
- Box mAP@0.5: `0.6037`
- Box mAP@0.5:0.95: `0.4418`
- Mask Precision: `0.5914`
- Mask Recall: `0.5421`
- Mask mAP@0.5: `0.5808`
- Mask mAP@0.5:0.95: `0.4066`

### Speed (test split, CPU)

- Preprocess: `0.4563 ms/image`
- Inference: `30.0526 ms/image`
- Postprocess: `6.7104 ms/image`

## Run 2: Pollution Severity Classification Baseline

- Model: `yolo11n-cls.pt`
- Command profile: `imgsz=224`, `batch=32`, `epochs=1`, `device=cpu`
- Run directory: `D:\pv_temp\training_runs\pollution_cls_baseline_cpu_e1_i224`
- Metrics JSON: `D:\pv_temp\metrics\pollution_cls_baseline_cpu_e1_i224.json`
- Detailed report: `D:\pv_temp\metrics\pollution_cls_baseline_cpu_e1_i224_report.json`
- Best weights: `D:\pv_temp\training_runs\pollution_cls_baseline_cpu_e1_i224\weights\best.pt`

### Test Metrics

- Top-1 Accuracy: `0.9266`
- Top-5 Accuracy: `1.0000`
- Macro Precision: `0.9287`
- Macro Recall: `0.9268`
- Macro F1: `0.9263`

### Per-Class F1

- `0_High`: Precision `0.8829`, Recall `0.9751`, F1 `0.9267`
- `1_Moderate`: Precision `0.9337`, Recall `0.8525`, F1 `0.8912`
- `2_low`: Precision `0.9696`, Recall `0.9528`, F1 `0.9611`

### Confusion Matrix

Rows are ground truth and columns are predictions:

```text
[
  [626, 14, 2],
  [78, 549, 17],
  [5, 25, 605]
]
```

## Important Constraint

The two uploaded datasets support:

- panel-level segmentation
- pollution severity classification

They do **not** currently provide defect-level bounding boxes or contamination masks for direct YOLO detection/segmentation of dust, crack, or bio-stain instances. That means the current data is enough to write a paper around:

- `panel segmentation + severity classification`

but not enough to honestly claim:

- `defect localization detection`
- `multi-defect instance segmentation`

unless a third detection-style annotated dataset is added.
