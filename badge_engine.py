from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont


ROOT = Path(__file__).resolve().parent
FONT_FILES = {
    "Jua — closest match": ROOT / "Jua-Regular.ttf",
    "Concert One": ROOT / "ConcertOne-Regular.ttf",
    "Barlow Condensed SemiBold": ROOT / "BarlowCondensed-SemiBold.ttf",
}

SHAPES = {
    "Uploaded Shape 1 — exact SVG": {
        "file": ROOT / "shape-1.svg",
        # The Silhouette file has a 386 mm square canvas. These values are the
        # exact visible artwork bounds, so blank canvas is removed, not resized.
        "width": 80.21133,
        "height": 40.72310,
        "min_x": 13.33612,
        "min_y": 51.99852,
    }
}

SYMBOLS = {"No symbol": ""}
LAYER_FILES = {
    "base": "01_BASE.svg",
    "border": "02_WHITE_BORDER.svg",
    "name": "03_NAME.svg",
    "profession": "04_PROFESSION.svg",
    "symbol": "05_SYMBOL.svg",
}


@lru_cache(maxsize=None)
def _shape_paths(shape_name: str) -> tuple[str, str]:
    source = SHAPES[shape_name]["file"]
    root = ET.parse(source).getroot()
    namespace = {"svg": "http://www.w3.org/2000/svg"}
    paths = root.findall(".//svg:defs/svg:path", namespace)
    if len(paths) != 2:
        raise ValueError(f"{source.name} must contain exactly two paths: base then white border")
    return paths[0].attrib["d"], paths[1].attrib["d"]


@lru_cache(maxsize=None)
def _font_data(font_name: str):
    font = TTFont(FONT_FILES[font_name])
    return {
        "font": font,
        "glyph_set": font.getGlyphSet(),
        "cmap": font.getBestCmap(),
        "hmtx": font["hmtx"].metrics,
        "units_per_em": font["head"].unitsPerEm,
        "ascender": font["hhea"].ascent,
        "descender": font["hhea"].descent,
    }


def _clean_text(value: str, fallback: str, limit: int) -> str:
    allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789&-'./ "
    cleaned = "".join(char for char in (value or fallback).upper() if char in allowed)
    return cleaned[:limit] or fallback


def _text_metrics(text: str, font_name: str) -> tuple[dict, list[str], list[float], float, float]:
    data = _font_data(font_name)
    chars = list(text)
    spacing = data["units_per_em"] * 0.035
    advances = []
    for char in chars:
        glyph_name = data["cmap"].get(ord(char), ".notdef")
        advances.append(data["hmtx"].get(glyph_name, (data["units_per_em"] * 0.6, 0))[0])
    width = sum(advances) + max(0, len(chars) - 1) * spacing
    return data, chars, advances, spacing, max(width, 1)


def text_width_mm(text: str, font_name: str, target_height: float) -> float:
    data, _, _, _, width = _text_metrics(text, font_name)
    scale = target_height / (data["ascender"] - data["descender"])
    return width * scale


def vector_text(text: str, font_name: str, center_x: float, center_y: float, target_height: float, max_width: float) -> str:
    data, chars, advances, spacing, width = _text_metrics(text, font_name)
    scale = min(target_height / (data["ascender"] - data["descender"]), max_width / width)
    cursor = center_x - width * scale / 2
    baseline = center_y + (data["ascender"] + data["descender"]) * scale / 2
    paths = []
    for char, advance in zip(chars, advances):
        glyph_name = data["cmap"].get(ord(char), ".notdef")
        pen = SVGPathPen(data["glyph_set"])
        data["glyph_set"][glyph_name].draw(pen)
        commands = pen.getCommands()
        if commands:
            paths.append(
                f'<path d="{commands}" transform="translate({cursor:.5f} {baseline:.5f}) scale({scale:.7f} {-scale:.7f})"/>'
            )
        cursor += (advance + spacing) * scale
    return "".join(paths)


def badge_values(name: str, profession: str, shape_name: str, name_font: str, symbol_name: str, auto_enlarge: bool) -> dict:
    shape = SHAPES[shape_name]
    clean_name = _clean_text(name, "NAME", 24)
    clean_profession = _clean_text(profession, "PROFESSION", 32)
    base_width = shape["width"]
    available_name_width = base_width * (0.64 if symbol_name != "No symbol" else 0.82)
    required_name_width = text_width_mm(clean_name, name_font, 12.0)
    badge_scale = 1.0
    if auto_enlarge and required_name_width > available_name_width:
        badge_scale = min(required_name_width / available_name_width, 90.0 / base_width)
    return {
        "name": clean_name,
        "profession": clean_profession,
        "shape": shape_name,
        "name_font": name_font,
        "profession_font": "Barlow Condensed SemiBold",
        "symbol": symbol_name,
        "scale": badge_scale,
        "width": base_width * badge_scale,
        "height": shape["height"] * badge_scale,
    }


def layer_markup(layer: str, values: dict) -> str:
    shape = SHAPES[values["shape"]]
    base_path, border_path = _shape_paths(values["shape"])
    scale = values["scale"]
    transform = f'translate({-shape["min_x"] * scale:.6f} {-shape["min_y"] * scale:.6f}) scale({scale:.7f})'
    has_symbol = values["symbol"] != "No symbol"
    text_center = values["width"] * (0.39375 if has_symbol else 0.5)
    text_width = values["width"] * (0.625 if has_symbol else 0.82)
    vertical_offset = 2.35 * scale

    if layer == "base":
        return f'<path d="{base_path}" transform="{transform}" fill-rule="evenodd"/>'
    if layer == "border":
        return f'<path d="{border_path}" transform="{transform}" fill-rule="evenodd"/>'
    if layer == "name":
        return vector_text(values["name"], values["name_font"], text_center, 14.5 * scale + vertical_offset, 12.0 * scale, text_width)
    if layer == "profession":
        return vector_text(values["profession"], values["profession_font"], text_center, 25.0 * scale + vertical_offset, 5.7 * scale, text_width)
    if layer == "symbol":
        return SYMBOLS[values["symbol"]]
    raise ValueError(f"Unknown layer: {layer}")


def make_svg(layer: str, values: dict, colour: str = "#000000") -> str:
    content = layer_markup(layer, values)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{values["width"]:.5f}mm" '
        f'height="{values["height"]:.5f}mm" viewBox="0 0 {values["width"]:.5f} {values["height"]:.5f}">'
        f'<g fill="{colour}" stroke="none">{content}</g></svg>'
    )


def preview_svg(values: dict, base_colour: str) -> str:
    white = "#fffaf7"
    layers = [f'<g fill="{base_colour}">{layer_markup("base", values)}</g>']
    for layer in ("border", "name", "profession", "symbol"):
        markup = layer_markup(layer, values)
        if markup:
            layers.append(f'<g fill="{white}">{markup}</g>')
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {values["width"]:.5f} {values["height"]:.5f}" '
        'style="display:block;width:100%;height:auto;filter:drop-shadow(0 10px 8px rgba(80,32,50,.26))">'
        + "".join(layers)
        + "</svg>"
    )


def clean_file_name(value: str) -> str:
    cleaned = "_".join("".join(char if char.isalnum() else " " for char in value.upper()).split())
    return cleaned or "BADGE"


def make_zip_pack(values: dict) -> bytes:
    folder = f'{clean_file_name(values["name"])}_{clean_file_name(values["profession"])}'
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for layer, file_name in LAYER_FILES.items():
            markup = layer_markup(layer, values)
            if markup:
                archive.writestr(f"{folder}/{file_name}", make_svg(layer, values))
        archive.writestr(
            f"{folder}/TINKERCAD_IMPORT_GUIDE.txt",
            "Teddie & Lane Badge Builder\n\n"
            "1. Import every SVG at 100% scale.\n"
            "2. Keep the base at 2.0 mm high.\n"
            "3. Set every white part to 0.8 mm high.\n"
            "4. Place all white parts at Z = 2.0 mm.\n"
            "5. Select every part and align their centres.\n"
            "6. Without AMS, add one filament change at 2.0 mm.\n\n"
            f'Badge canvas: {values["width"]:.2f} x {values["height"]:.2f} mm\n'
            "Finished height: 2.8 mm\n",
        )
    return output.getvalue()
