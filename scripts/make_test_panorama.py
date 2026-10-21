#!/usr/bin/env python3
"""Generate a synthetic 2:1 panorama with compass labels for viewer testing."""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH = 4096
HEIGHT = 2048


def create_test_panorama(
    heading: float = 0,
    marker_label: str = "",
) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)
    for y in range(HEIGHT):
        if y < HEIGHT // 2:
            fraction = y / (HEIGHT // 2)
            color = (
                int(96 - 38 * fraction),
                int(184 - 45 * fraction),
                int(224 - 25 * fraction),
            )
        else:
            fraction = (y - HEIGHT // 2) / (HEIGHT // 2)
            color = (
                int(100 - 28 * fraction),
                int(164 - 45 * fraction),
                int(76 - 25 * fraction),
            )
        draw.line((0, y, WIDTH, y), fill=color)

    for x in range(0, WIDTH + 1, 256):
        draw.line((x, 0, x, HEIGHT), fill=(255, 255, 255), width=3)
    for y in range(0, HEIGHT + 1, 256):
        draw.line((0, y, WIDTH, y), fill=(255, 255, 255), width=3)

    font = ImageFont.load_default(size=120)
    center_y = HEIGHT // 2
    for direction_label, compass_bearing in (
        ("N", 0),
        ("E", 90),
        ("S", 180),
        ("W", 270),
    ):
        yaw = (compass_bearing - heading + 180) % 360 - 180
        x = round((yaw + 180) * WIDTH / 360) % WIDTH
        draw.line((x, center_y - 420, x, center_y + 420), fill=(35, 35, 35), width=8)
        draw.rounded_rectangle(
            (x - 90, center_y - 220, x + 90, center_y - 60),
            radius=20,
            fill=(255, 255, 255),
            outline=(20, 20, 20),
            width=6,
        )
        draw.text(
            (x, center_y - 140),
            direction_label,
            font=font,
            fill=(15, 23, 42),
            anchor="mm",
        )

    if marker_label:
        draw.text(
            (WIDTH // 2, 160),
            marker_label,
            font=font,
            fill=(15, 23, 42),
            anchor="mm",
        )

    return image


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "output",
        nargs="?",
        type=Path,
        default=Path("data/test-panorama.jpg"),
    )
    parser.add_argument("--heading", type=float, default=0)
    parser.add_argument("--label", default="")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    create_test_panorama(args.heading, args.label).save(
        args.output, "JPEG", quality=90
    )
    print(f"Wrote synthetic 2:1 panorama to {args.output}")


if __name__ == "__main__":
    main()
