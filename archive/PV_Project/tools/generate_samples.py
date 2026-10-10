from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "backend" / "samples"
WIDTH = 1280
HEIGHT = 720


def load_font(size: int):
    candidates = [
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


TITLE_FONT = load_font(28)


def new_canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (WIDTH, HEIGHT), (13, 24, 40))
    draw = ImageDraw.Draw(image, "RGBA")

    for y in range(HEIGHT):
        ratio = y / HEIGHT
        color = (
            int(30 - ratio * 18),
            int(62 - ratio * 34),
            int(102 - ratio * 56),
        )
        draw.line([(0, y), (WIDTH, y)], fill=color)

    draw.rectangle((80, 120, WIDTH - 80, HEIGHT - 60), fill=(34, 53, 77))
    draw_panel_field(draw)
    return image, draw


def draw_panel_field(draw: ImageDraw.ImageDraw) -> None:
    panel_width = 230
    panel_height = 115
    gap_x = 24
    gap_y = 22
    start_x = 120
    start_y = 160

    for row in range(3):
        for col in range(4):
            x = start_x + col * (panel_width + gap_x)
            y = start_y + row * (panel_height + gap_y)
            rect = (x, y, x + panel_width, y + panel_height)
            draw.rounded_rectangle(rect, radius=6, fill=(24, 53, 94), outline=(106, 179, 255), width=3)

            for grid in range(1, 6):
                line_x = x + int(grid * panel_width / 6)
                draw.line([(line_x, y), (line_x, y + panel_height)], fill=(48, 122, 187), width=1)
            for grid in range(1, 4):
                line_y = y + int(grid * panel_height / 4)
                draw.line([(x, line_y), (x + panel_width, line_y)], fill=(48, 122, 187), width=1)


def add_title(draw: ImageDraw.ImageDraw, text: str) -> None:
    draw.text((90, 42), text, font=TITLE_FONT, fill=(255, 255, 255))


def make_dust_sample() -> None:
    image, draw = new_canvas()
    add_title(draw, "Sample 1 - Heavy Dust Coverage")
    overlays = [
        (150, 190, 410, 300, (214, 181, 61, 145)),
        (420, 185, 740, 320, (214, 181, 61, 155)),
        (710, 188, 1030, 308, (246, 214, 90, 125)),
        (285, 338, 645, 470, (214, 181, 61, 150)),
        (824, 350, 1044, 445, (246, 214, 90, 110)),
        (510, 486, 900, 604, (214, 181, 61, 148)),
    ]
    for overlay in overlays:
        draw.ellipse(overlay[:4], fill=overlay[4])
    image.save(OUTPUT_DIR / "dust-heavy.png")


def make_crack_sample() -> None:
    image, draw = new_canvas()
    add_title(draw, "Sample 2 - Critical Crack Risk")
    crack_color = (242, 83, 83, 255)
    segments = [
        [(250, 210), (310, 280), (385, 345), (420, 412)],
        [(700, 202), (760, 250), (845, 315), (912, 382)],
        [(530, 485), (620, 545), (700, 582)],
    ]
    for points in segments:
        draw.line(points, fill=crack_color, width=5, joint="curve")
    image.save(OUTPUT_DIR / "crack-critical.png")


def make_stain_sample() -> None:
    image, draw = new_canvas()
    add_title(draw, "Sample 3 - Bio Stain Accumulation")
    stains = [
        ((215, 210, 310, 295), (64, 205, 117, 155)),
        ((248, 226, 318, 286), (40, 165, 86, 165)),
        ((610, 348, 738, 466), (64, 205, 117, 160)),
        ((654, 373, 720, 438), (40, 165, 86, 170)),
        ((934, 480, 1046, 588), (64, 205, 117, 158)),
        ((974, 506, 1034, 562), (40, 165, 86, 170)),
    ]
    for rect, color in stains:
        draw.ellipse(rect, fill=color)
    image.save(OUTPUT_DIR / "bio-stain.png")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    make_dust_sample()
    make_crack_sample()
    make_stain_sample()
    print(f"Generated samples in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
