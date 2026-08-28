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
    "RUBY — custom SVG font": ROOT / "RUBY-Regular.ttf",
    "Jua — closest match": ROOT / "Jua-Regular.ttf",
    "Concert One": ROOT / "ConcertOne-Regular.ttf",
    "Barlow Condensed SemiBold": ROOT / "BarlowCondensed-SemiBold.ttf",
}

# Every entry points to paths in the user's combined Silhouette SVG.  Bounds are
# the original saved artwork bounds in millimetres, so the enormous empty page
# is removed without changing the size or proportions of any badge.
SHAPES = {
    "Shape 01 — Ornate Edge": {
        "file": ROOT / "shape-1.svg", "base": "path_3f423b3ab92f2102d20eb4ed90074420",
        "white": ["path_813568b31b0fd4317b7613699086303b"],
        "min_x": 13.34511, "min_y": 51.96073, "width": 80.20235, "height": 40.76197,
    },
    "Shape 02 — Tab Top": {
        "file": ROOT / "shape-1.svg", "base": "path_dfefc154ea14bb309363fa610a249ae6",
        "white": ["path_97f2458cf5c95612ddcdd4c4fea282a8"],
        "min_x": 185.48218, "min_y": 24.74320, "width": 81.12284, "height": 42.07536,
    },
    "Shape 03 — Rounded Oval": {
        "file": ROOT / "shape-1.svg", "base": "path_397fd59534ed8683878c71420cb7b731",
        "white": ["path_4b872a789c6dbc95fa064bdcc15d1886"],
        "min_x": 278.80733, "min_y": 30.33263, "width": 82.59921, "height": 32.97740,
    },
    "Shape 04 — Ribbon": {
        "file": ROOT / "shape-1.svg", "base": "path_46d1e0df805ea21680a1e5dc82c1ea85",
        "white": ["path_b5d2ec868da95492248db403e956c3c4"],
        "min_x": 187.45941, "min_y": 177.88731, "width": 80.64368, "height": 33.38195,
    },
    "Shape 05 — Curved Frame": {
        "file": ROOT / "shape-1.svg", "base": "path_f78e0aaa70919b65ab50be8ec2f4fc5a",
        "white": ["path_a01cf821a6d74a4bca65275b4705dc35"],
        "min_x": 184.33256, "min_y": 131.78790, "width": 84.29122, "height": 35.74944,
    },
    "Shape 06 — Scalloped Frame": {
        "file": ROOT / "shape-1.svg", "base": "path_56bf836ea2e29c7a53c020153655d9a2",
        "white": ["path_8271e5b800c1cd306fe37ad393023f72"],
        "min_x": 183.54305, "min_y": 221.67506, "width": 90.37267, "height": 36.83026,
    },
    "Shape 07 — Hexagon Frame": {
        "file": ROOT / "shape-1.svg", "base": "path_9e764f2f0b65323421f5f6e27090dc85",
        "white": ["path_e4984834a7939d94a4e928d911f441fe"],
        "min_x": 181.65471, "min_y": 74.02327, "width": 81.89886, "height": 42.45451,
    },
    "Shape 08 — Eight-Petal Flower": {
        "file": ROOT / "shape-1.svg", "base": "path_d529411b5364fe83d2b843cad2b4fd7a",
        "white": [], "min_x": 32.49110, "min_y": 309.75035, "width": 80.59314, "height": 79.03184,
    },
    "Shape 09 — Oval": {
        "file": ROOT / "shape-1.svg", "base": "path_fbe1a66e793afcd99680b898df54ce5d",
        "white": [], "min_x": -101.41294, "min_y": 118.00152, "width": 79.70890, "height": 82.15604,
    },
    "Shape 10 — Scalloped Square": {
        "file": ROOT / "shape-1.svg", "base": "path_bf5ba89f85b64cfd7a7f2da69eadcfa7",
        "white": [], "min_x": -88.61742, "min_y": 221.15013, "width": 80.97441, "height": 63.53466,
    },
    "Shape 11 — Rounded Arch": {
        "file": ROOT / "shape-1.svg", "base": "path_04576767ce038b4522a5eaa3f011d6b6",
        "white": [], "min_x": -96.17075, "min_y": 33.44466, "width": 83.26332, "height": 68.00585,
    },
    "Shape 12 — Rounded Rectangle": {
        "file": ROOT / "shape-1.svg", "base": "path_3038ac9be4a35c59c60017800ad38ed5",
        "white": [], "min_x": -78.20713, "min_y": 303.04317, "width": 82.62541, "height": 36.18071,
    },
    "Shape 13 — Six-Petal Flower": {
        "file": ROOT / "shape-1.svg", "base": "path_1969e93c08159eaf56b2512549f11106",
        "white": [], "min_x": 18.35057, "min_y": 221.01201, "width": 75.06335, "height": 70.83266,
    },
    "Shape 14 — Pencil": {
        "file": ROOT / "shape-1.svg", "base": "path_70c6cce3b3465e680c795774bb7edfb4",
        "white": ["path_a30eed1acd416922e9df689d12c8f0c6"],
        "min_x": 27.76881, "min_y": 112.93449, "width": 92.05727, "height": 39.08478,
        "text_x": 0.43, "text_width": 0.66,
    },
    "Shape 15 — Pencil Alternate": {
        "file": ROOT / "shape-1.svg", "base": "path_bafa0b766fbbe23b6fbb9c7183b93656",
        "white": ["path_7a52611c1bae2781f966f6ab8c27910b", "path_f7d32addf9a189809b2ca85670d866de"],
        "min_x": 26.60756, "min_y": 168.33030, "width": 101.38801, "height": 39.52266,
        "body_width": 92.05674, "text_x": 0.39, "text_width": 0.60,
    },
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
def _shape_paths(shape_name: str) -> tuple[str, tuple[str, ...]]:
    source = SHAPES[shape_name]["file"]
    root = ET.parse(source).getroot()
    paths = {element.attrib.get("id"): element.attrib.get("d", "") for element in root.iter() if element.tag.endswith("path")}
    spec = SHAPES[shape_name]
    missing = [path_id for path_id in [spec["base"], *spec["white"]] if path_id not in paths]
    if missing:
        raise ValueError(f"{source.name} is missing required vector paths: {', '.join(missing)}")
    return paths[spec["base"]], tuple(paths[path_id] for path_id in spec["white"])


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
    body_width = shape.get("body_width", base_width)
    available_name_width = body_width * shape.get("text_width", 0.64 if symbol_name != "No symbol" else 0.78)
    name_height = min(12.0, shape["height"] * 0.30)
    required_name_width = text_width_mm(clean_name, name_font, name_height)
    badge_scale = 1.0
    if auto_enlarge and required_name_width > available_name_width:
        badge_scale = min(required_name_width / available_name_width, max(1.0, 120.0 / base_width))
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
    base_path, white_paths = _shape_paths(values["shape"])
    scale = values["scale"]
    transform = f'translate({-shape["min_x"] * scale:.6f} {-shape["min_y"] * scale:.6f}) scale({scale:.7f})'
    has_symbol = values["symbol"] != "No symbol"
    text_center = values["width"] * shape.get("text_x", 0.39375 if has_symbol else 0.5)
    body_width = shape.get("body_width", shape["width"]) * scale
    text_width = body_width * shape.get("text_width", 0.625 if has_symbol else 0.78)
    name_height = min(12.0, shape["height"] * 0.30) * scale
    profession_height = min(5.7, shape["height"] * 0.16) * scale
    name_y = values["height"] * 0.40
    profession_y = values["height"] * 0.66

    if layer == "base":
        return f'<path d="{base_path}" transform="{transform}" fill-rule="evenodd"/>'
    if layer == "border":
        return "".join(f'<path d="{path}" transform="{transform}" fill-rule="evenodd"/>' for path in white_paths)
    if layer == "name":
        return vector_text(values["name"], values["name_font"], text_center, name_y, name_height, text_width)
    if layer == "profession":
        return vector_text(values["profession"], values["profession_font"], text_center, profession_y, profession_height, text_width)
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
        'style="display:block;width:100%;height:100%;max-width:720px;max-height:350px;filter:drop-shadow(0 10px 8px rgba(80,32,50,.26))">'
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
