from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from math import acos, ceil, degrees, hypot
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.basePen import BasePen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path.parser import parse_path
from fontTools.ttLib import TTFont


ROOT = Path(__file__).resolve().parent
FONT_FILES = {
    "RUBY — custom SVG font": ROOT / "RUBY-Regular.ttf",
    "EMMA — custom SVG font": ROOT / "EMMA-Regular.ttf",
    "Jua — closest match": ROOT / "Jua-Regular.ttf",
    "Concert One": ROOT / "ConcertOne-Regular.ttf",
    "Barlow Condensed SemiBold": ROOT / "BarlowCondensed-SemiBold.ttf",
}
for consolas_name in ("Consolas.ttf", "consola.ttf"):
    if (ROOT / consolas_name).exists():
        FONT_FILES["Consolas"] = ROOT / consolas_name
        break

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

SYMBOL_SHEET = ROOT / "symbols.svg"
SYMBOLS = {
    "No symbol": [],
    "Books": ["path_6ed86875b65ab5610aa6e15e5f10d18c"],
    "Open Book": ["path_8626ed85d6e34ffdc46e1fe8786a0016"],
    "Pencil": ["path_71482ec58792b49c301d53e9714aa9e9"],
    "Pen": ["path_320a31ae9cb977148949750d5f69a094"],
    "Art Palette": ["path_4d500725313570986e3f1df8ac1de721"],
    "Smiley Face": ["path_2f41dd64ed083a60119a208bce4ad592"],
    "Daisy Outline": ["path_3018c154bdee9937ffd73418d1d4572b"],
    "Daisy": ["path_f7b740f484cc81e81c54d36004fde910"],
    "Rose": ["path_4076f162b6113ae8a113e0789b6ef27c"],
    "Rainbow": ["path_b7729085b6bbea5f333586384795636c"],
    "Sun": ["path_84d4c4200310a76c52d1efa957882b81"],
    "Moon and Stars": ["path_6e1e0ca792f0094d5ca5b67d3675b0c9"],
    "Cloud": ["path_0c41b101ec6c14aa572dbdfb44fe72ca"],
    "Lightning": ["path_b093ea3354cf65bce8c650d068cbaf44"],
    "Hot Drink": ["path_943f9d6b9006b9b5ed352bb92f60a05d"],
    "Coffee Cup": ["path_b92ec2f4ca41ed91a7d6a2f8f0032d4d"],
    "Iced Drink": ["path_f4a313ed4f576108a18562ba7f43b1c4"],
    "Cupcake": ["path_cd86124de43dcc80a189e694f7012515"],
    "Donut": ["path_6c81ed59ebad99baa07bc557a88cee70"],
    "Strawberry": ["path_7ef0506af3b9f06c3a2d3ce50c5b30bd"],
    "Cherries": ["path_938bbc5c73d517edfd00cadc6ebd02a6"],
    "Pizza": ["path_8a6041a1b5fdd3c7f7f076f655d50704"],
    "Stethoscope": ["path_05d24fb968450b70621c3b013a04ce0a"],
    "Mother and Baby": ["path_4645bd778019d042b32e2fcc8baa58ad"],
    "Healthcare Worker": ["path_eaaacbfe359001db9db0eb71dec8e680"],
    "Caring People": ["path_d33688da9b6afd0bcffe48bc25604fd3"],
    "Medical Cross": ["path_0cf5909676b59757db4acd76c69fd53b"],
    "Veterinary Paw Cross A": ["path_8ec7450153fb9d813378aebbf79567bd"],
    "Animal Care Paw": ["path_596868d4415d6f53e1b6483383d93ce2"],
    "Veterinary Paw Cross B": ["path_2bafb65d1d622868487b957e455d732b"],
    "Veterinarian and Pet": ["path_a9b110428542adf3991b8ffa7ba4a1ac"],
    "Medical Monitor": ["path_b0e9d3013d1888a2c33a97e0e2241dcb"],
    "Star of Life": ["path_d67340b045f7889c6fc8c0f0aa1ea1c7"],
    "Physiotherapy": ["path_8d4ecc2716bdeb4330fc6a0080b8135b"],
    "Care and Support": ["path_97e7e70730316b25cc5cef7fb2207e24"],
    "Chat": ["path_2b39ac324dc54f5cb4f9f0bb4e525a6d"],
    "Hairdresser": ["path_37a1157e3cf7c3f02d516823e311e3a3"],
    "Paw Print": ["path_38055091cba468ac89c97dc91cb376ef", "path_aa3d8e6144f10d497166cc5b22a9df43", "path_8f84131214201045a4dbac42b3bfb7d6", "path_7b0de287de1670f64cb1fbfcf4bfd20e", "path_77b45a992fc68b82712aaa6d1eb7d4cf"],
    "Dog": ["path_33eae147307a8f624bbfcc071e6aa41e"],
    "Dog Heart": ["path_4ef9c6a929a63d69c10ce0a3784524ba"],
    "Tooth": ["path_ff5630e85547ed1ddd537e72194c3130"],
    "Pharmacy": ["path_8e1d7a166321505bc4db5ba1347b7d04"],
    "X-Ray": ["path_94bd1b9f3486ba6f0edd86ee57a0bc13"],
    "Ultrasound": ["path_8ba8e3a5d423b75bf988911633f55b2d"],
    "Test Tube": ["path_ce94ed77ffa455d2bbc86053e7997cc3"],
    "Dog Sitting": ["path_ac49cf3aa7132a5526622ee99fbcb747", "path_954eeefd484dea3788e514c0c8f0c0d2"],
    "Cat": ["path_ca90537c370cc2afe2b442f82f94a043"],
    "Rabbit": ["path_8dfd773c3a50e2614b2021a083ae1c1f"],
    "Horse": ["path_059a586ddb248acaa2bb459de0aa1b9a"],
    "Cow": ["path_0d6e134b2863a592f93343d94b48f399"],
    "First Aid Kit": ["path_803e49762b48a057b3cf4d48fa1d32e4"],
    "Syringe": ["path_f87c971ea34f42461d01d951b78b8c57"],
    "Scrubs": ["path_b54e6e7410a90fa71e893ad0bf11da90"],
    "Bandage": ["path_c1b68365961fd8f95d4bb669ff6e6201"],
    "Heartbeat": ["path_0e795be99c9e6fd1747a6761b5ba9b6f"],
    "Sheep": ["path_27f3b7870af758afe7b1685cd18bf18a"],
    "Pig": ["path_09d41c7794a195e02153e3e13c241e8b"],
    "Bird": ["path_946d45b63ab9640c0e373a277947fe31"],
    "Fish": ["path_4b7823c463d5c4408907b976ffe0a83b"],
    "Turtle": ["path_4a5769889d0781235562ae1b129f2c38"],
}

# Extra education and care symbols supplied as a second vector sheet.
# A few designs contain several independent paths; keeping those path IDs
# together makes each complete design appear as one selectable symbol.
NEW_SYMBOL_SHEET = ROOT / "symbols-3.svg"
NEW_SYMBOLS = {
    "People Care": ["path_4b6649bffb8815e87a4d101795b2001e"],
    "Home Support": [
        "path_7307190a9faa3b3738a860d983a08602",
        "path_6f1df7161037a7b9249e45ece4347751",
        "path_7cdcaadebc4de2f998ca9c12d87c8cd9",
        "path_4f6f03aa6294302ce516c459a4c9e321",
        "path_991c8a7c422476d1839f3e52f16c26ef",
        "path_3c825de9d07256dc6d6b76f6113431a9",
    ],
    "Education Home": ["path_88061a2144bd562d8b15be26b490e897"],
    "Childcare Classroom": ["path_5584df8fbd931447396017ef724bb4df"],
    "Star Team": ["path_8ce2b30a464551b82d6e85fd6b6bc5d1"],
    "Early Learning Classroom": ["path_e3a57ed500a65e52f29a809b47ae361d"],
    "Star Student Group": ["path_46ebb8e43cb1a3bcde9098016ecb04b6"],
    "Staff ID": ["path_7db7e49d2adc620d097813338dba74ff"],
    "Learning Ideas": ["path_09da6e5aa43370656fc111d1f28eb50c"],
    "Mentoring": ["path_d3c5c4c227d69948c831ce1f29031b72"],
    "Caring Apple": ["path_0df2e91f5ea94f88c5218c81c7ce83da"],
    "Shared Reading": ["path_60063afb17b4936a4b96bba18be13338"],
    "Graduate Books": ["path_7505a52f6c93181321d1c531dc799586"],
    "Art and Craft": ["path_94bccbafdaa2a0b4fd5ca3e1e0611b47"],
    "Reading Teacher": ["path_68a77e4e857f41996eb0356ca0387ac2"],
    "Music": ["path_93f68dd02ea5ffc2e51fcb877b37c854"],
    "Sport and Movement": ["path_bb10769a95d1f87dbcffa53030150e5c"],
    "Mathematics": ["path_ee1d26ada409c08c93a12bb8e4459ebe"],
    "Science": ["path_ebe6104b4818489558764a5587f1951a"],
    "Graduate": ["path_e6cbb8ac3ebd79adcc351c7c2a9d3e4d"],
    "Open Book Bookmark": ["path_6dc8e86f1a508cf4cc31936c059af8fb"],
    "Counselling": ["path_627fe73bbf93db933c58fae454ad8421"],
    "Tutoring": ["path_08541cbf95a1e75d0cbe164d0311cd1e"],
    "Teamwork": ["path_6494c67be98e385ddee02e345f652c29"],
    "Bookshelf": ["path_4f0e9f19c592d5040fe72ae21de472bd"],
}
SYMBOLS.update(NEW_SYMBOLS)
LAYER_FILES = {
    "base": "01_BASE.svg",
    "border": "02_WHITE_BORDER.svg",
    "name": "03_NAME_LINE_1.svg",
    "name2": "04_NAME_LINE_2.svg",
    "profession": "05_PROFESSION.svg",
    "extra_text": "06_EXTRA_TEXT.svg",
    "symbol": "07_SYMBOL.svg",
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


@lru_cache(maxsize=None)
def _symbol_sheet_paths(source: Path = SYMBOL_SHEET) -> dict[str, str]:
    root = ET.parse(source).getroot()
    return {element.attrib.get("id"): element.attrib.get("d", "") for element in root.iter() if element.tag.endswith("path")}


@lru_cache(maxsize=None)
def _symbol_data(symbol_name: str) -> tuple[tuple[str, ...], tuple[float, float, float, float]]:
    source = NEW_SYMBOL_SHEET if symbol_name in NEW_SYMBOLS else SYMBOL_SHEET
    sheet_paths = _symbol_sheet_paths(source)
    path_ids = SYMBOLS[symbol_name]
    missing = [path_id for path_id in path_ids if path_id not in sheet_paths]
    if missing:
        raise ValueError(f"{SYMBOL_SHEET.name} is missing symbol paths: {', '.join(missing)}")
    paths = tuple(sheet_paths[path_id] for path_id in path_ids)
    bounds = []
    for path in paths:
        pen = BoundsPen(None)
        parse_path(path, pen)
        if pen.bounds:
            bounds.append(pen.bounds)
    return paths, (
        min(item[0] for item in bounds), min(item[1] for item in bounds),
        max(item[2] for item in bounds), max(item[3] for item in bounds),
    )


class _FlattenPen(BasePen):
    """Convert SVG curves to fine final-size polylines for true path rounding."""

    def __init__(self, max_step: float = 0.18):
        super().__init__(None)
        self.max_step = max_step
        self.contours: list[list[tuple[float, float]]] = []
        self.current: list[tuple[float, float]] = []

    def _moveTo(self, point):
        if self.current:
            self.contours.append(self.current)
        self.current = [tuple(point)]

    def _lineTo(self, point):
        self.current.append(tuple(point))

    def _curveToOne(self, p1, p2, p3):
        p0 = self._getCurrentPoint()
        length = hypot(p1[0] - p0[0], p1[1] - p0[1]) + hypot(p2[0] - p1[0], p2[1] - p1[1]) + hypot(p3[0] - p2[0], p3[1] - p2[1])
        steps = max(2, min(128, ceil(length / self.max_step)))
        for index in range(1, steps + 1):
            t = index / steps
            u = 1 - t
            self.current.append((
                u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1],
            ))

    def _qCurveToOne(self, p1, p2):
        p0 = self._getCurrentPoint()
        length = hypot(p1[0] - p0[0], p1[1] - p0[1]) + hypot(p2[0] - p1[0], p2[1] - p1[1])
        steps = max(2, min(128, ceil(length / self.max_step)))
        for index in range(1, steps + 1):
            t = index / steps
            u = 1 - t
            self.current.append((u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0], u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]))

    def _closePath(self):
        if self.current:
            if len(self.current) > 1 and hypot(self.current[-1][0] - self.current[0][0], self.current[-1][1] - self.current[0][1]) < 1e-6:
                self.current.pop()
            self.contours.append(self.current)
            self.current = []

    def _endPath(self):
        if self.current:
            self.contours.append(self.current)
            self.current = []


def _flatten_path(path: str, transform: tuple[float, float, float, float, float, float]) -> list[list[tuple[float, float]]]:
    pen = _FlattenPen()
    parse_path(path, TransformPen(pen, transform))
    pen.endPath()
    return [contour for contour in pen.contours if len(contour) >= 3]


def _point_line_distance(point, start, end) -> float:
    dx, dy = end[0] - start[0], end[1] - start[1]
    if dx == 0 and dy == 0:
        return hypot(point[0] - start[0], point[1] - start[1])
    t = max(0.0, min(1.0, ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / (dx * dx + dy * dy)))
    projection = (start[0] + t * dx, start[1] + t * dy)
    return hypot(point[0] - projection[0], point[1] - projection[1])


def _rdp(points: list[tuple[float, float]], tolerance: float) -> list[tuple[float, float]]:
    if len(points) <= 2:
        return points
    distance, position = max((_point_line_distance(point, points[0], points[-1]), index) for index, point in enumerate(points[1:-1], 1))
    if distance <= tolerance:
        return [points[0], points[-1]]
    left = _rdp(points[: position + 1], tolerance)
    right = _rdp(points[position:], tolerance)
    return left[:-1] + right


def _simplify_closed(points: list[tuple[float, float]], tolerance: float = 0.055) -> list[tuple[float, float]]:
    if len(points) < 5:
        return points
    anchor = points[0]
    opposite = max(range(1, len(points)), key=lambda index: hypot(points[index][0] - anchor[0], points[index][1] - anchor[1]))
    first = _rdp(points[: opposite + 1], tolerance)
    second = _rdp(points[opposite:] + [points[0]], tolerance)
    result = first[:-1] + second[:-1]
    return result if len(result) >= 3 else points


def _corner_angle(previous, point, following) -> float:
    ax, ay = previous[0] - point[0], previous[1] - point[1]
    bx, by = following[0] - point[0], following[1] - point[1]
    al, bl = hypot(ax, ay), hypot(bx, by)
    if al < 1e-6 or bl < 1e-6:
        return 180.0
    cosine = max(-1.0, min(1.0, (ax * bx + ay * by) / (al * bl)))
    return degrees(acos(cosine))


def _corner_records(contours: list[list[tuple[float, float]]], simplify: bool = True, angle_limit: float = 152.0):
    records = []
    for contour_index, original in enumerate(contours):
        points = _simplify_closed(original) if simplify else original
        for vertex_index, point in enumerate(points):
            previous = points[vertex_index - 1]
            following = points[(vertex_index + 1) % len(points)]
            if _corner_angle(previous, point, following) <= angle_limit and min(hypot(point[0] - previous[0], point[1] - previous[1]), hypot(point[0] - following[0], point[1] - following[1])) >= 0.22:
                records.append((contour_index, vertex_index, point, points))
    return sorted(records, key=lambda item: (round(item[2][1], 2), round(item[2][0], 2)))


def _text_contours(text: str, font_name: str, center_x: float, center_y: float, target_height: float, max_width: float):
    data, chars, advances, spacing, width, bounds = _text_layout(text, font_name)
    min_x, min_y, max_x, max_y = bounds
    ink_height = max(max_y - min_y, 1)
    fit_width = max(width, max_x - min_x, 1)
    text_scale = min(target_height / ink_height, max_width / fit_width)
    cursor = center_x - (min_x + max_x) * text_scale / 2
    baseline = center_y + (min_y + max_y) * text_scale / 2
    contours = []
    for char, advance in zip(chars, advances):
        glyph_name = data["cmap"].get(ord(char), ".notdef")
        pen = SVGPathPen(data["glyph_set"])
        data["glyph_set"][glyph_name].draw(pen)
        commands = pen.getCommands()
        if commands:
            contours.extend(_flatten_path(commands, (text_scale, 0, 0, -text_scale, cursor, baseline)))
        cursor += (advance + spacing) * text_scale
    return contours


def _component_contours(component: str, values: dict):
    shape = SHAPES[values["shape"]]
    badge_scale = values["scale"]
    if component in ("base", "border"):
        base_path, white_paths = _shape_paths(values["shape"])
        paths = (base_path,) if component == "base" else white_paths
        part_scale = 1.0 if component == "base" else values["border_size"] / 100
        center_x, center_y = values["width"] / 2, values["height"] / 2
        tx = -shape["min_x"] * badge_scale
        ty = -shape["min_y"] * badge_scale
        transform = (
            badge_scale * part_scale, 0, 0, badge_scale * part_scale,
            center_x + values.get("border_x", 0.0) - center_x * part_scale + tx * part_scale,
            center_y + values.get("border_y", 0.0) - center_y * part_scale + ty * part_scale,
        )
        return [contour for path in paths for contour in _flatten_path(path, transform)]
    if component == "symbol":
        if values["symbol"] == "No symbol":
            return []
        paths, (min_x, min_y, max_x, max_y) = _symbol_data(values["symbol"])
        target_size = min(values["height"] * 0.45, values["width"] * 0.21) * values["symbol_size"] / 100
        symbol_scale = target_size / max(max_x - min_x, max_y - min_y)
        target_x = values["width"] * 0.79 + values["symbol_x"]
        target_y = values["height"] * 0.51 + values["symbol_y"]
        transform = (symbol_scale, 0, 0, symbol_scale, target_x - (min_x + max_x) * symbol_scale / 2, target_y - (min_y + max_y) * symbol_scale / 2)
        return [contour for path in paths for contour in _flatten_path(path, transform)]

    has_symbol = values["symbol"] != "No symbol"
    default_center = values["width"] * shape.get("text_x", 0.39375 if has_symbol else 0.5)
    body_width = shape.get("body_width", shape["width"]) * badge_scale
    text_width = body_width * shape.get("text_width", 0.625 if has_symbol else 0.78)
    if component == "name":
        has_second_name = bool(values.get("name2"))
        default_y = 0.27 if has_second_name else 0.40
        target_height = min(10.0, shape["height"] * 0.23) if has_second_name else min(12.0, shape["height"] * 0.30)
        return _text_contours(values["name"], values["name_font"], default_center + values["name_x"], values["height"] * default_y + values["name_y"], target_height * badge_scale * values["name_size"] / 100, text_width)
    if component == "name2":
        return _text_contours(values.get("name2", ""), values["name2_font"], default_center + values["name2_x"], values["height"] * 0.48 + values["name2_y"], min(9.0, shape["height"] * 0.21) * badge_scale * values["name2_size"] / 100, text_width)
    if component == "profession":
        default_y = 0.69 if values.get("name2") else 0.66
        return _text_contours(values["profession"], values["profession_font"], default_center + values["profession_x"], values["height"] * default_y + values["profession_y"], min(5.7, shape["height"] * 0.16) * badge_scale * values["profession_size"] / 100, text_width)
    if component == "extra_text":
        default_y = 0.84 if values.get("name2") else 0.80
        return _text_contours(values.get("extra_text", ""), values["extra_font"], default_center + values["extra_x"], values["height"] * default_y + values["extra_y"], min(4.8, shape["height"] * 0.12) * badge_scale * values["extra_size"] / 100, text_width)
    return []


def component_corner_points(component: str, values: dict) -> list[tuple[float, float]]:
    angle_limit = 165.0 if component in ("base", "border", "symbol") else 152.0
    return [record[2] for record in _corner_records(_component_contours(component, values), angle_limit=angle_limit)]


def _rounded_component_path(component: str, values: dict, setting: dict) -> str:
    radius = max(0.0, float(setting.get("radius", 0.0)))
    selected_mode = setting.get("mode") == "Selected corners"
    is_graphic = component in ("base", "border", "symbol")
    tolerance = 0.055 if selected_mode or not is_graphic else min(1.2, max(0.055, radius * 0.20))
    angle_limit = 165.0 if is_graphic else 152.0
    contours = [_simplify_closed(contour, tolerance) for contour in _component_contours(component, values)]
    records = _corner_records(contours, simplify=False, angle_limit=angle_limit)
    if selected_mode:
        selected_numbers = set(setting.get("corners", []))
        rounded_vertices = {(record[0], record[1]) for number, record in enumerate(records) if number in selected_numbers}
    else:
        rounded_vertices = {(record[0], record[1]) for record in records}
    commands = []
    for contour_index, points in enumerate(contours):
        if len(points) < 3:
            continue
        entries, exits, rounded = [], [], []
        for vertex_index, point in enumerate(points):
            previous, following = points[vertex_index - 1], points[(vertex_index + 1) % len(points)]
            use_rounding = (contour_index, vertex_index) in rounded_vertices and radius > 0
            if use_rounding:
                previous_length = hypot(previous[0] - point[0], previous[1] - point[1])
                following_length = hypot(following[0] - point[0], following[1] - point[1])
                offset = min(radius, previous_length * 0.42, following_length * 0.42)
                entry = (point[0] + (previous[0] - point[0]) * offset / previous_length, point[1] + (previous[1] - point[1]) * offset / previous_length)
                exit_point = (point[0] + (following[0] - point[0]) * offset / following_length, point[1] + (following[1] - point[1]) * offset / following_length)
            else:
                entry = exit_point = point
            entries.append(entry); exits.append(exit_point); rounded.append(use_rounding)
        commands.append(f"M {exits[0][0]:.4f} {exits[0][1]:.4f}")
        for vertex_index in range(1, len(points)):
            commands.append(f"L {entries[vertex_index][0]:.4f} {entries[vertex_index][1]:.4f}")
            if rounded[vertex_index]:
                commands.append(f"Q {points[vertex_index][0]:.4f} {points[vertex_index][1]:.4f} {exits[vertex_index][0]:.4f} {exits[vertex_index][1]:.4f}")
        commands.append(f"L {entries[0][0]:.4f} {entries[0][1]:.4f}")
        if rounded[0]:
            commands.append(f"Q {points[0][0]:.4f} {points[0][1]:.4f} {exits[0][0]:.4f} {exits[0][1]:.4f}")
        commands.append("Z")
    return " ".join(commands)


def _rounding_markup(component: str, values: dict) -> str | None:
    setting = values.get("rounding", {}).get(component, {})
    if float(setting.get("radius", 0.0)) <= 0:
        return None
    path = _rounded_component_path(component, values, setting)
    return f'<path d="{path}" fill-rule="evenodd"/>' if path else ""


def _supported_text(value: str, font_name: str, limit: int) -> str:
    cmap = _font_data(font_name)["cmap"]
    replacements = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-"})
    source = (value or "").translate(replacements)
    return "".join(char for char in source if char == " " or ord(char) in cmap)[:limit]


def _clean_text(value: str, fallback: str, limit: int, font_name: str) -> str:
    cleaned = _supported_text(value or fallback, font_name, limit)
    return cleaned or _supported_text(fallback, font_name, limit)


def _clean_optional_text(value: str, limit: int, font_name: str) -> str:
    return _supported_text(value, font_name, limit)


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


def _text_layout(text: str, font_name: str):
    data, chars, advances, spacing, width = _text_metrics(text, font_name)
    cursor = 0.0
    glyph_bounds = []
    for char, advance in zip(chars, advances):
        glyph_name = data["cmap"].get(ord(char), ".notdef")
        pen = BoundsPen(data["glyph_set"])
        data["glyph_set"][glyph_name].draw(pen)
        if pen.bounds:
            min_x, min_y, max_x, max_y = pen.bounds
            glyph_bounds.append((min_x + cursor, min_y, max_x + cursor, max_y))
        cursor += advance + spacing
    if glyph_bounds:
        bounds = (
            min(item[0] for item in glyph_bounds), min(item[1] for item in glyph_bounds),
            max(item[2] for item in glyph_bounds), max(item[3] for item in glyph_bounds),
        )
    else:
        bounds = (0.0, data["descender"], width, data["ascender"])
    return data, chars, advances, spacing, width, bounds


def text_width_mm(text: str, font_name: str, target_height: float) -> float:
    _, _, _, _, width, (min_x, min_y, max_x, max_y) = _text_layout(text, font_name)
    scale = target_height / max(max_y - min_y, 1)
    return max(width, max_x - min_x) * scale


def vector_text(text: str, font_name: str, center_x: float, center_y: float, target_height: float, max_width: float) -> str:
    data, chars, advances, spacing, width, bounds = _text_layout(text, font_name)
    min_x, min_y, max_x, max_y = bounds
    ink_height = max(max_y - min_y, 1)
    fit_width = max(width, max_x - min_x, 1)
    scale = min(target_height / ink_height, max_width / fit_width)
    cursor = center_x - (min_x + max_x) * scale / 2
    baseline = center_y + (min_y + max_y) * scale / 2
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


def badge_values(
    name: str, profession: str, shape_name: str, name_font: str, symbol_name: str, auto_enlarge: bool,
    profession_font: str = "Barlow Condensed SemiBold", name2: str = "", name2_font: str = "RUBY — custom SVG font",
    extra_text: str = "", extra_font: str = "Barlow Condensed SemiBold", badge_size: int = 100,
    border_size: int = 100, border_x: float = 0.0, border_y: float = 0.0,
    symbol_size: int = 100, symbol_x: float = 0.0, symbol_y: float = 0.0,
    name_size: int = 100, name_x: float = 0.0, name_y: float = 0.0,
    name2_size: int = 100, name2_x: float = 0.0, name2_y: float = 0.0,
    profession_size: int = 100, profession_x: float = 0.0, profession_y: float = 0.0,
    extra_size: int = 100, extra_x: float = 0.0, extra_y: float = 0.0,
) -> dict:
    shape = SHAPES[shape_name]
    clean_name = _clean_text(name, "NAME", 24, name_font)
    clean_name2 = _clean_optional_text(name2, 24, name2_font)
    clean_profession = _clean_text(profession, "PROFESSION", 32, profession_font)
    clean_extra = _clean_optional_text(extra_text, 32, extra_font)
    base_width = shape["width"]
    body_width = shape.get("body_width", base_width)
    available_name_width = body_width * shape.get("text_width", 0.64 if symbol_name != "No symbol" else 0.78)
    name_height = min(12.0, shape["height"] * 0.30) * name_size / 100
    required_name_width = text_width_mm(clean_name, name_font, name_height)
    badge_scale = badge_size / 100
    if auto_enlarge and required_name_width > available_name_width:
        badge_scale = max(badge_scale, min(required_name_width / available_name_width, max(1.0, 120.0 / base_width)))
    return {
        "name": clean_name,
        "name2": clean_name2,
        "profession": clean_profession,
        "extra_text": clean_extra,
        "shape": shape_name,
        "name_font": name_font,
        "name2_font": name2_font,
        "profession_font": profession_font,
        "extra_font": extra_font,
        "symbol": symbol_name,
        "scale": badge_scale,
        "width": base_width * badge_scale,
        "height": shape["height"] * badge_scale,
        "badge_size": badge_size,
        "border_size": border_size, "border_x": border_x, "border_y": border_y,
        "symbol_size": symbol_size, "symbol_x": symbol_x, "symbol_y": symbol_y,
        "name_size": name_size, "name_x": name_x, "name_y": name_y,
        "name2_size": name2_size, "name2_x": name2_x, "name2_y": name2_y,
        "profession_size": profession_size, "profession_x": profession_x, "profession_y": profession_y,
        "extra_size": extra_size, "extra_x": extra_x, "extra_y": extra_y,
    }


def symbol_markup(values: dict) -> str:
    if values["symbol"] == "No symbol":
        return ""
    paths, (min_x, min_y, max_x, max_y) = _symbol_data(values["symbol"])
    symbol_width = max_x - min_x
    symbol_height = max_y - min_y
    target_size = min(values["height"] * 0.45, values["width"] * 0.21) * values["symbol_size"] / 100
    symbol_scale = target_size / max(symbol_width, symbol_height)
    source_x = (min_x + max_x) / 2
    source_y = (min_y + max_y) / 2
    target_x = values["width"] * 0.79 + values["symbol_x"]
    target_y = values["height"] * 0.51 + values["symbol_y"]
    transform = f'translate({target_x:.5f} {target_y:.5f}) scale({symbol_scale:.7f}) translate({-source_x:.5f} {-source_y:.5f})'
    return "".join(f'<path d="{path}" transform="{transform}" fill-rule="evenodd"/>' for path in paths)


def layer_markup(layer: str, values: dict) -> str:
    if layer in values.get("hidden", set()):
        return ""
    shape = SHAPES[values["shape"]]
    base_path, white_paths = _shape_paths(values["shape"])
    scale = values["scale"]
    transform = f'translate({-shape["min_x"] * scale:.6f} {-shape["min_y"] * scale:.6f}) scale({scale:.7f})'
    has_symbol = values["symbol"] != "No symbol"
    default_text_center = values["width"] * shape.get("text_x", 0.39375 if has_symbol else 0.5)
    body_width = shape.get("body_width", shape["width"]) * scale
    text_width = body_width * shape.get("text_width", 0.625 if has_symbol else 0.78)
    has_second_name = bool(values.get("name2"))
    name_base_height = min(10.0, shape["height"] * 0.23) if has_second_name else min(12.0, shape["height"] * 0.30)
    name_height = name_base_height * scale * values["name_size"] / 100
    profession_height = min(5.7, shape["height"] * 0.16) * scale * values["profession_size"] / 100
    name_center = default_text_center + values["name_x"]
    profession_center = default_text_center + values["profession_x"]
    name_y = values["height"] * (0.27 if has_second_name else 0.40) + values["name_y"]
    name2_height = min(9.0, shape["height"] * 0.21) * scale * values["name2_size"] / 100
    name2_center = default_text_center + values["name2_x"]
    name2_y = values["height"] * 0.48 + values["name2_y"]
    profession_y = values["height"] * (0.69 if has_second_name else 0.66) + values["profession_y"]
    extra_height = min(4.8, shape["height"] * 0.12) * scale * values["extra_size"] / 100
    extra_center = default_text_center + values["extra_x"]
    extra_y = values["height"] * (0.84 if has_second_name else 0.80) + values["extra_y"]

    if layer in ("base", "border", "name", "name2", "profession", "extra_text", "symbol"):
        rounded_markup = _rounding_markup(layer, values)
        if rounded_markup is not None:
            return rounded_markup

    if layer == "base":
        return f'<path d="{base_path}" transform="{transform}" fill-rule="evenodd"/>'
    if layer == "border":
        part_scale = values["border_size"] / 100
        center_x, center_y = values["width"] / 2, values["height"] / 2
        border_transform = (
            f'translate({center_x + values["border_x"]:.6f} {center_y + values["border_y"]:.6f}) '
            f'scale({part_scale:.7f}) translate({-center_x:.6f} {-center_y:.6f}) {transform}'
        )
        return "".join(f'<path d="{path}" transform="{border_transform}" fill-rule="evenodd"/>' for path in white_paths)
    if layer == "name":
        return vector_text(values["name"], values["name_font"], name_center, name_y, name_height, text_width)
    if layer == "name2":
        return vector_text(values["name2"], values["name2_font"], name2_center, name2_y, name2_height, text_width) if values.get("name2") else ""
    if layer == "profession":
        return vector_text(values["profession"], values["profession_font"], profession_center, profession_y, profession_height, text_width)
    if layer == "extra_text":
        return vector_text(values["extra_text"], values["extra_font"], extra_center, extra_y, extra_height, text_width) if values.get("extra_text") else ""
    if layer == "symbol":
        return symbol_markup(values)
    raise ValueError(f"Unknown layer: {layer}")


def make_svg(layer: str, values: dict, colour: str = "#000000") -> str:
    content = layer_markup(layer, values)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{values["width"]:.5f}mm" '
        f'height="{values["height"]:.5f}mm" viewBox="0 0 {values["width"]:.5f} {values["height"]:.5f}">'
        f'<g fill="{colour}" stroke="none">{content}</g></svg>'
    )


def _corner_marker_markup(component: str, values: dict) -> str:
    points = component_corner_points(component, values)
    marker_radius = max(0.75, min(values["width"], values["height"]) * 0.026)
    font_size = marker_radius * 1.25
    markers = []
    for number, (x, y) in enumerate(points, start=1):
        markers.append(
            f'<circle cx="{x:.4f}" cy="{y:.4f}" r="{marker_radius:.4f}" fill="#d62568" '
            'stroke="#fffaf7" stroke-width="0.35"/>'
            f'<text x="{x:.4f}" y="{y + font_size * 0.34:.4f}" text-anchor="middle" '
            f'font-family="Arial,sans-serif" font-size="{font_size:.4f}" font-weight="700" fill="white">{number}</text>'
        )
    return "".join(markers)


def corner_editor_svg(component: str, values: dict) -> str:
    contours = _component_contours(component, values)
    points = [point for contour in contours for point in contour]
    if not points:
        return ""
    min_x = min(point[0] for point in points)
    min_y = min(point[1] for point in points)
    max_x = max(point[0] for point in points)
    max_y = max(point[1] for point in points)
    padding = max(1.8, (max_y - min_y) * 0.22)
    width = max_x - min_x + padding * 2
    height = max_y - min_y + padding * 2
    content = layer_markup(component, values)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{min_x - padding:.4f} {min_y - padding:.4f} {width:.4f} {height:.4f}" '
        'style="display:block;width:100%;height:100%;max-height:245px">'
        f'<rect x="{min_x - padding:.4f}" y="{min_y - padding:.4f}" width="{width:.4f}" height="{height:.4f}" rx="1" fill="#fffaf7"/>'
        f'<g fill="#39343b">{content}</g><g pointer-events="none">{_corner_marker_markup(component, values)}</g></svg>'
    )


def preview_svg(values: dict, base_colour: str, marker_component: str | None = None) -> str:
    white = "#fffaf7"
    layers = [f'<g fill="{base_colour}">{layer_markup("base", values)}</g>']
    for layer in ("border", "name", "name2", "profession", "extra_text", "symbol"):
        markup = layer_markup(layer, values)
        if markup:
            layers.append(f'<g fill="{white}">{markup}</g>')
    if marker_component:
        layers.append(f'<g pointer-events="none">{_corner_marker_markup(marker_component, values)}</g>')
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
