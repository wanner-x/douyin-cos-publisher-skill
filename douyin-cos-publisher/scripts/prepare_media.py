#!/usr/bin/env python3
"""Create a read-only media inventory and optional image contact sheet."""

from __future__ import annotations

import argparse
import json
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
VIDEO_EXTENSIONS = {".mov", ".mp4"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--contact-sheet", type=Path)
    parser.add_argument("--recursive", action="store_true")
    return parser.parse_args()


def discover(source: Path, recursive: bool) -> list[Path]:
    iterator = source.rglob("*") if recursive else source.iterdir()
    allowed = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS
    return sorted(
        (path for path in iterator if path.is_file() and path.suffix.lower() in allowed),
        key=lambda path: str(path.relative_to(source)).lower(),
    )


def image_metadata(path: Path) -> dict[str, Any]:
    try:
        from PIL import Image, ImageOps

        with Image.open(path) as image:
            image = ImageOps.exif_transpose(image)
            exif = image.getexif()
            return {
                "width": image.width,
                "height": image.height,
                "captured_at": exif.get(36867) or exif.get(306),
            }
    except Exception as exc:
        return {"metadata_error": str(exc)}


def make_manifest(source: Path, paths: list[Path]) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for path in paths:
        stat = path.stat()
        item: dict[str, Any] = {
            "path": str(path.resolve()),
            "relative_path": str(path.relative_to(source)),
            "extension": path.suffix.lower(),
            "mime_type": mimetypes.guess_type(path.name)[0],
            "bytes": stat.st_size,
            "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            "kind": "image" if path.suffix.lower() in IMAGE_EXTENSIONS else "video",
        }
        if item["kind"] == "image":
            item.update(image_metadata(path))
        items.append(item)
    return {
        "source": str(source.resolve()),
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "count": len(items),
        "items": items,
    }


def make_contact_sheet(paths: list[Path], output: Path) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageOps
    except ImportError as exc:
        raise SystemExit(
            "Contact sheet requires Pillow. Use an available image-enabled Python runtime."
        ) from exc

    image_paths = [path for path in paths if path.suffix.lower() in IMAGE_EXTENSIONS]
    if not image_paths:
        raise SystemExit("No supported images found for contact sheet.")

    tile_width, image_height, label_height, columns = 240, 200, 34, 5
    rows = (len(image_paths) + columns - 1) // columns
    canvas = Image.new(
        "RGB", (columns * tile_width, rows * (image_height + label_height)), "white"
    )
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()

    for index, path in enumerate(image_paths):
        try:
            with Image.open(path) as source_image:
                image = ImageOps.exif_transpose(source_image).convert("RGB")
                image.thumbnail((tile_width - 10, image_height - 10))
                column, row = index % columns, index // columns
                x = column * tile_width + (tile_width - image.width) // 2
                y = row * (image_height + label_height) + (image_height - image.height) // 2
                canvas.paste(image, (x, y))
                draw.text(
                    (column * tile_width + 5, row * (image_height + label_height) + image_height + 5),
                    path.name[:36],
                    fill="black",
                    font=font,
                )
        except Exception as exc:
            column, row = index % columns, index // columns
            draw.text(
                (column * tile_width + 5, row * (image_height + label_height) + 10),
                f"Unreadable: {path.name}\n{exc}",
                fill="red",
                font=font,
            )

    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, quality=88)


def main() -> None:
    args = parse_args()
    source = args.source.expanduser().resolve()
    if not source.is_dir():
        raise SystemExit(f"Source directory not found: {source}")

    paths = discover(source, args.recursive)
    manifest = make_manifest(source, paths)

    if args.manifest:
        manifest_path = args.manifest.expanduser().resolve()
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    if args.contact_sheet:
        make_contact_sheet(paths, args.contact_sheet.expanduser().resolve())

    if args.manifest:
        summary = {
            "source": manifest["source"],
            "count": manifest["count"],
            "manifest": str(args.manifest.expanduser().resolve()),
            "contact_sheet": (
                str(args.contact_sheet.expanduser().resolve())
                if args.contact_sheet
                else None
            ),
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
