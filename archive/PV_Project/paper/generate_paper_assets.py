from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "paper" / "assets"

SEG_TEST_DIR = ROOT / "老师给的" / "yolo8 seg training data" / "Dataset" / "test" / "images"
CLS_ROOT = ROOT / "老师给的" / "yolo8 cls training data" / "Dataset"

SEG_PREVIEW = Path(r"D:\pv_temp\training_runs\panel_seg_baseline_cpu_e1_i320\val_batch0_pred.jpg")
CLS_CONFUSION = Path(r"D:\pv_temp\training_runs\pollution_cls_baseline_cpu_e1_i224\confusion_matrix_normalized.png")


def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def fit_image(path: Path, size: tuple[int, int]) -> Image.Image:
    image = Image.open(path).convert("RGB")
    return ImageOps.fit(image, size, method=Image.Resampling.LANCZOS)


def first_image(directory: Path) -> Path | None:
    if not directory.exists():
        return None
    for path in sorted(directory.iterdir()):
        if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
            return path
    return None


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], fill: str) -> None:
    draw.line((start, end), fill=fill, width=8)
    ex, ey = end
    draw.polygon([(ex, ey), (ex - 24, ey - 14), (ex - 24, ey + 14)], fill=fill)


def block(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], title: str, body: str, fill: str) -> None:
    title_font = load_font(28, bold=True)
    text_font = load_font(20)
    draw.rounded_rectangle(xy, radius=24, fill=fill, outline="#1e293b", width=3)
    left, top, _, _ = xy
    draw.text((left + 22, top + 18), title, font=title_font, fill="#0f172a")
    y = top + 70
    for line in body.split("\n"):
        draw.text((left + 22, y), line, font=text_font, fill="#1f2937")
        y += 28


def make_examples() -> None:
    canvas = Image.new("RGB", (1800, 980), "white")
    draw = ImageDraw.Draw(canvas)
    title_font = load_font(42, bold=True)
    label_font = load_font(24, bold=True)
    text_font = load_font(20)

    draw.text((60, 32), "Dataset Examples for Panel Segmentation and Severity Classification", font=title_font, fill="#111111")
    draw.text((60, 84), "Top row: RGB panel images used for segmentation. Bottom row: tile-level severity samples.", font=text_font, fill="#4b5563")

    seg_paths = []
    if SEG_TEST_DIR.exists():
        seg_paths = [path for path in sorted(SEG_TEST_DIR.iterdir()) if path.suffix.lower() in {".jpg", ".jpeg", ".png"}][:3]

    cls_paths = [
        ("High", first_image(CLS_ROOT / "train" / "0_High")),
        ("Moderate", first_image(CLS_ROOT / "train" / "1_Moderate")),
        ("Low", first_image(CLS_ROOT / "train" / "2_low")),
    ]

    card_w = 520
    card_h = 320
    gap = 40
    start_x = 60

    draw.text((60, 150), "Panel segmentation samples", font=label_font, fill="#0f172a")
    for index, image_path in enumerate(seg_paths):
        x = start_x + index * (card_w + gap)
        y = 200
        draw.rounded_rectangle((x, y, x + card_w, y + card_h), radius=24, outline="#cbd5e1", width=3, fill="#f8fafc")
        image = fit_image(image_path, (card_w - 32, card_h - 70))
        canvas.paste(image, (x + 16, y + 16))
        draw.text((x + 20, y + card_h - 44), image_path.name[:40], font=text_font, fill="#334155")

    draw.text((60, 580), "Tile-level severity samples", font=label_font, fill="#0f172a")
    for index, (label, image_path) in enumerate(cls_paths):
        x = start_x + index * (card_w + gap)
        y = 630
        draw.rounded_rectangle((x, y, x + card_w, y + 260), radius=24, outline="#cbd5e1", width=3, fill="#f8fafc")
        if image_path is not None:
            image = fit_image(image_path, (180, 180))
            canvas.paste(image, (x + 24, y + 36))
        draw.text((x + 236, y + 72), label, font=load_font(30, bold=True), fill="#0f172a")
        draw.text((x + 236, y + 124), "Tile size in raw data:\n25 to 52 pixels", font=text_font, fill="#475569")

    canvas.save(ASSET_DIR / "pv_examples.png")


def make_framework() -> None:
    canvas = Image.new("RGB", (1800, 980), "white")
    draw = ImageDraw.Draw(canvas)
    title_font = load_font(42, bold=True)
    text_font = load_font(22)

    draw.text((60, 32), "Panel-Aware PV Contamination Severity Mapping Pipeline", font=title_font, fill="#111111")
    draw.text((60, 84), "Teacher-provided scripts indicate a two-stage workflow: panel segmentation followed by tile-level severity mapping.", font=text_font, fill="#4b5563")

    boxes = [
        ((70, 180, 330, 390), "Input RGB Image", "Outdoor panel image\nReflection and shadow\nMixed background", "#dbeafe"),
        ((390, 180, 700, 390), "Panel Segmentation", "YOLOv8-seg family\nPanel mask prediction\nSurface localization", "#dcfce7"),
        ((760, 180, 1060, 390), "Panel Ordering", "Sort masks from\n top-left to bottom-right\nAssign panel IDs", "#ede9fe"),
        ((1120, 180, 1450, 390), "Tile Sampling", "Split masked panels into\n32 or 40 pixel tiles\nKeep panel-only tiles", "#fef3c7"),
        ((1510, 180, 1760, 390), "Severity Classifier", "YOLO classifier\nHigh / Moderate / Low", "#fee2e2"),
        ((620, 580, 1140, 820), "Per-Panel Mapping", "Overlay tile colors on panel regions\nCount severity proportions\nBuild pie chart statistics", "#e0f2fe"),
    ]

    for item in boxes:
        block(draw, item[0], item[1], item[2], item[3])

    arrow(draw, (330, 285), (390, 285), "#2563eb")
    arrow(draw, (700, 285), (760, 285), "#2563eb")
    arrow(draw, (1060, 285), (1120, 285), "#2563eb")
    arrow(draw, (1450, 285), (1510, 285), "#2563eb")
    arrow(draw, (1635, 390), (1040, 580), "#dc2626")

    draw.rounded_rectangle((70, 580, 520, 820), radius=24, fill="#f8fafc", outline="#1e293b", width=3)
    draw.text((95, 610), "Core Improvement", font=load_font(30, bold=True), fill="#0f172a")
    draw.text((95, 682), "Use panel localization as a prior\nbefore severity analysis, so the model\nfocuses on photovoltaic surfaces\ninstead of the full background.", font=text_font, fill="#1f2937")

    draw.rounded_rectangle((1210, 580, 1730, 820), radius=24, fill="#f8fafc", outline="#1e293b", width=3)
    draw.text((1235, 610), "System Output", font=load_font(30, bold=True), fill="#0f172a")
    draw.text((1235, 682), "Per-panel overlay map\nSeverity pie chart\nDashboard statistics\nMaintenance cue", font=text_font, fill="#1f2937")

    canvas.save(ASSET_DIR / "framework_overview.png")


def make_qualitative() -> None:
    canvas = Image.new("RGB", (1800, 900), "white")
    draw = ImageDraw.Draw(canvas)
    title_font = load_font(40, bold=True)
    label_font = load_font(24, bold=True)
    text_font = load_font(20)

    draw.text((60, 30), "Current Results and Error Analysis Overview", font=title_font, fill="#111111")
    draw.text((60, 82), "The current draft reports a segmentation preview, a normalized confusion matrix, and representative failure modes.", font=text_font, fill="#4b5563")

    boxes = [
        (60, 150, 860, 690),
        (940, 150, 1740, 690),
    ]
    for left, top, right, bottom in boxes:
        draw.rounded_rectangle((left, top, right, bottom), radius=24, outline="#d0d7de", width=3, fill="#f8fafc")

    if SEG_PREVIEW.exists():
        seg_image = fit_image(SEG_PREVIEW, (760, 420))
        canvas.paste(seg_image, (80, 190))
    if CLS_CONFUSION.exists():
        cls_image = fit_image(CLS_CONFUSION, (760, 420))
        canvas.paste(cls_image, (960, 190))

    draw.text((90, 630), "Segmentation preview", font=label_font, fill="#0f172a")
    draw.text((970, 630), "Classification confusion matrix", font=label_font, fill="#0f172a")

    draw.rounded_rectangle((60, 730, 1740, 860), radius=24, outline="#d0d7de", width=3, fill="#eff6ff")
    draw.text((90, 758), "Observed failure cases", font=label_font, fill="#0f172a")
    draw.text((360, 760), "1) strong reflection reduces panel recall; 2) low-contrast dusty samples may be missed; 3) moderate and high severity remain the main confusion pair.", font=text_font, fill="#334155")

    canvas.save(ASSET_DIR / "qualitative_results.png")


def main() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    make_examples()
    make_framework()
    make_qualitative()


if __name__ == "__main__":
    main()
