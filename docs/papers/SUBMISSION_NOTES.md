# ICSIP Submission Notes

This draft is intentionally written as a regular ICSIP paper in the image processing / visual detection direction:

- Main line: contamination detection + panel-level localization + robustness under complex illumination.
- Avoided line: broad project report, cloud platform narrative, or multi-task feature stacking.
- Writing language: English conference style, close to IEEE formatting.

## Files

- `paper/pv_contamination_icsip.tex`: IEEE conference paper source.
- `paper/generate_paper_assets.py`: builds the figure assets used by the manuscript.
- `paper/generate_paper_docx.py`: exports a Word draft based on `E:\ICSIP2026_PV_Contamination_Paper\Template.docx`.

## What Is Already Grounded in the Project

- Topic: UAV-based photovoltaic surface contamination / defect inspection.
- Core classes: dust, crack, biological stain.
- Method line: illumination robustness + YOLOv8 panel segmentation + YOLO11 detection.
- Data scale: about 3000 images.
- Hardware target: RTX 4060.
- Verified preliminary result from the project proposal: dust-only model F1-score = 0.97.

## What Must Be Replaced Before Real Submission

Search and replace these tokens in the paper:

- `XX.X`
- author block placeholder

These values must come from your real training logs:

- final panel segmentation IoU / Dice
- final detector Precision / Recall / mAP@0.5 / mAP@0.5:0.95
- FPS or latency under the final hardware and batch setting
- parameter count if you plan to report it
- baseline results for YOLOv8n / YOLOv8m / YOLO11n
- ablation results

## Strongly Recommended Final Checks

1. Replace the default `70/15/15` split if your actual train/val/test split is different.
2. Make sure every number in the abstract also appears in the results table.
3. Keep one clear claim: the gain comes from panel-aware localization under complex illumination.
4. Do not submit the dashboard demo latency as model runtime.
5. If the final experiments are not ready, do not claim improvements numerically.
