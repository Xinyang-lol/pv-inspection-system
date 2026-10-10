Put trained weights here:

- `panel_yolov8_seg.pt`: YOLOv8 segmentation model for class `PV_surface`.
- `dust_yolov8_cls.pt`: YOLOv8 classification model for panel tiles: `High`, `Moderate`, `low`.
- `defect_yolo11_seg.pt`: optional legacy defect segmentation model.

The backend now prefers the two-stage teacher flow:

1. Segment PV panel surfaces with `panel_yolov8_seg.pt`.
2. Split each panel mask into 32/40 px tiles.
3. Classify each tile with `dust_yolov8_cls.pt`.
4. Convert tile-level `High / Moderate / low` results into dust coverage and risk score.

Override paths with environment variables if needed:

- `PV_PANEL_MODEL`
- `PV_TILE_CLS_MODEL`
- `PV_DEFECT_MODEL`
- `PV_DEVICE`
- `PV_DEMO_MODE=true`
