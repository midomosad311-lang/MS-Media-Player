"""Generate the application icon (PNG + multi-size ICO).

Run:  python tools/make_icon.py

Produces:
    resources/icons/app_icon.png   (256x256)
    resources/icons/app_icon.ico   (16,24,32,48,64,128,256)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "resources" / "icons"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SIZE = 256


def _rounded_gradient(size: int) -> Image.Image:
    """Dark blue rounded-square background with a subtle vertical gradient."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    top = (38, 74, 122)
    bottom = (15, 27, 48)
    grad = Image.new("RGBA", (size, size))
    px = grad.load()
    for y in range(size):
        t = y / max(1, size - 1)
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        for x in range(size):
            px[x, y] = (r, g, b, 255)

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, size - 1, size - 1], radius=int(size * 0.22), fill=255
    )
    img.paste(grad, (0, 0), mask)
    return img


def _draw_play(draw: ImageDraw.ImageDraw, size: int):
    """Bright accent play triangle inside a translucent circle."""
    cx, cy = size / 2, size / 2
    r = size * 0.30
    draw.ellipse(
        [cx - r, cy - r, cx + r, cy + r],
        fill=(77, 163, 255, 60),
        outline=(120, 195, 255, 200),
        width=max(2, size // 64),
    )
    t = size * 0.17
    draw.polygon(
        [(cx - t * 0.85, cy - t), (cx - t * 0.85, cy + t), (cx + t * 1.05, cy)],
        fill=(255, 255, 255, 255),
    )


def _draw_text(img: Image.Image, size: int):
    """Small 'MS' wordmark in the lower area (best effort with a system font)."""
    draw = ImageDraw.Draw(img)
    font = None
    for name in ("seguisb.ttf", "segoeui.ttf", "arialbd.ttf", "arial.ttf"):
        try:
            font = ImageFont.truetype(name, int(size * 0.14))
            break
        except Exception:
            continue
    if font is None:
        return
    text = "MS"
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.text(
        ((size - w) / 2 - bbox[0], size * 0.80 - h - bbox[1]),
        text,
        font=font,
        fill=(210, 228, 255, 235),
    )


def build() -> Image.Image:
    img = _rounded_gradient(SIZE)
    _draw_play(ImageDraw.Draw(img), SIZE)
    _draw_text(img, SIZE)
    return img


def main():
    img = build()
    png_path = OUT_DIR / "app_icon.png"
    img.save(png_path)
    ico_path = OUT_DIR / "app_icon.ico"
    img.save(
        ico_path,
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print(f"Wrote {png_path}")
    print(f"Wrote {ico_path}")


if __name__ == "__main__":
    main()
