import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from ultralytics import YOLO
from collections import Counter
from tqdm import tqdm
from scipy.ndimage import center_of_mass

# Paths
input_folder = r"D:\YOLO-SPHMapper\Classifiers\YOLO8\YOLO8-8SPHMapper test\images4"
results_folder = r"D:\YOLO-SPHMapper\Classifiers\YOLO8\YOLO8-8SPHMapper test\images 4 output"
os.makedirs(results_folder, exist_ok=True)

# Models
seg_model = YOLO(r'D:\YOLO-SPHMapper\best_yolo_8_segmentator.pt')
clf_model = YOLO(r'D:\YOLO-SPHMapper\Classifiers\YOLO8\DustClassifier\batch 64\weights\best.pt')

# Colors
bgr_colors = {"Low": (74, 192, 3), "Moderate": (0, 255, 255), "High": (0, 8, 255)} #for overlays
hex_colors = {"Low": "#03C04A", "Moderate": "#FFFF00", "High": "#FF0800"} #for pie charts

def get_tile_size(img_shape):
    return 32 if max(img_shape) < 1000 else 40 # less than 1000x1000 and more than 1000x1000

def sort_masks_top_left_to_bottom_right(masks_list):
    """Sort masks left-to-right, top-to-bottom based on centroid"""
    mask_infos = []
    for mask in masks_list:
        cy, cx = center_of_mass(mask > 0)
        if not np.isnan(cx) and not np.isnan(cy):
            mask_infos.append(((int(cy), int(cx)), mask))
    # Sort first by y (rows), then by x (cols)
    sorted_masks = sorted(mask_infos, key=lambda x: (x[0][0], x[0][1]))
    return [(i + 1, mask) for i, (_, mask) in enumerate(sorted_masks)]

# Process images
panel_names = sorted([f for f in os.listdir(input_folder) if f.lower().endswith((".jpg", ".png"))])

for filename in tqdm(panel_names, desc="Processing images"):
    name = os.path.splitext(filename)[0]
    img_path = os.path.join(input_folder, filename)
    img = cv2.imread(img_path)
    h, w = img.shape[:2]
    tile_size = get_tile_size((h, w))

    output_dir = os.path.join(results_folder, name)
    os.makedirs(output_dir, exist_ok=True)

    # 1. Run segmentation
    seg_result = seg_model(img)[0]
    masks = seg_result.masks
    combined_mask = np.zeros((h, w), dtype=np.uint8)
    raw_masks = []

    for m in masks.data:
        m = m.cpu().numpy().astype(np.uint8) * 255
        m_resized = cv2.resize(m, (w, h), interpolation=cv2.INTER_NEAREST)
        combined_mask = np.maximum(combined_mask, m_resized)
        raw_masks.append(m_resized)

    # Sort panels top-left to bottom-right
    panel_masks = sort_masks_top_left_to_bottom_right(raw_masks)

    # Save raw YOLO prediction
    seg_result.save(filename=os.path.join(output_dir, "predicted.jpg"))
    cv2.imwrite(os.path.join(output_dir, "panel_mask.png"), combined_mask)
    masked_img = cv2.bitwise_and(img, img, mask=combined_mask)
    cv2.imwrite(os.path.join(output_dir, "masked.jpg"), masked_img)

    # Prepare overlay image
    overlay = img.copy().astype(np.float32)
    alpha = 0.5
    panel_stats = []

    for panel_id, msk in panel_masks:
        classes = []
        coords = []
        tile_masks = []
        tile_shapes = []

        for y in range(0, h, tile_size):
            for x in range(0, w, tile_size):
                y_end = min(y + tile_size, h)
                x_end = min(x + tile_size, w)
                tile_mask = msk[y:y_end, x:x_end]
                if np.any(tile_mask > 0):
                    tile = masked_img[y:y_end, x:x_end]
                    pred = clf_model(tile)[0]
                    cls = pred.names[int(pred.probs.top1)].capitalize()
                    classes.append(cls)
                    coords.append((x, y))
                    tile_masks.append(tile_mask)
                    tile_shapes.append((x_end - x, y_end - y))

        # Overlay classification colors
        for (x, y), cls, tile_mask, (tile_w, tile_h) in zip(coords, classes, tile_masks, tile_shapes):
            if cls not in bgr_colors:
                continue
            color = np.array(bgr_colors[cls], dtype=np.float32)
            region = overlay[y:y+tile_h, x:x+tile_w]
            mask_bool = tile_mask > 0
            for c in range(3):
                region[..., c][mask_bool] = (
                    (1 - alpha) * region[..., c][mask_bool] + alpha * color[c]
                )

        # Label the panel with its ID
        cy, cx = center_of_mass(msk > 0)
        if not np.isnan(cx) and not np.isnan(cy):
            cx, cy = int(cx), int(cy)
            cv2.putText(
                overlay,
                f"Panel {panel_id}",
                (cx - 40, cy),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
                cv2.LINE_AA
            )

        counts = Counter(classes)
        panel_stats.append((f"Panel {panel_id}", counts))

    # Save overlay image
    overlay_img = np.clip(overlay, 0, 255).astype(np.uint8)
    cv2.imwrite(os.path.join(output_dir, "overlay.jpg"), overlay_img)

    # Pie chart dashboard
    cols = 4
    rows = (len(panel_stats) + cols - 1) // cols
    fig, axs = plt.subplots(rows, cols, figsize=(4 * cols, 4 * rows))
    axs = axs.flatten()

    for idx, (panel_name, counts) in enumerate(panel_stats):
        ax = axs[idx]
        labels, sizes, colors = [], [], []
        for k in ["Low", "Moderate", "High"]:
            if k in counts:
                labels.append(k)
                sizes.append(counts[k])
                colors.append(hex_colors[k])
        ax.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90)
        ax.set_title(panel_name, fontsize=10)
        ax.axis("equal")

    for idx in range(len(panel_stats), len(axs)):
        axs[idx].axis("off")

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "dashboard.png"))
    plt.close()

print("✅ Done. Panels are now numbered from top-left to bottom-right and labeled on overlay.")
