import streamlit as st
import streamlit.components.v1 as components
from touch_editor import touch_badge_editor

from badge_engine import (
    FONT_FILES, LAYER_FILES, SHAPES, SYMBOLS, badge_values, clean_file_name,
    component_corner_points, corner_editor_svg, layer_markup, make_svg,
    make_zip_pack, preview_svg,
)


st.set_page_config(page_title="Teddie & Lane Badge Builder", page_icon="🏷️", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background: #f8f4f1; color: #322d35; }
    .block-container { max-width: 1120px; padding-top: .8rem; }
    .badge-title { font-size: 1.7rem; font-weight: 800; letter-spacing: -.03em; margin-bottom: .1rem; }
    .badge-kicker { color: #b17588; font-size: .72rem; font-weight: 800; letter-spacing: .16em; text-transform: uppercase; }
    .sticky-preview { position: sticky; top: .35rem; z-index: 50; background: #f8f4f1; padding: .25rem 0 .6rem; }
    .preview-shell { background: #c85f80; border-radius: 22px; padding: 12px 18px 15px; box-shadow: 0 8px 22px rgba(80,32,50,.22); }
    .preview-head { color: white; display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:6px; }
    .preview-head strong { font-size: 1rem; }
    .preview-head span { font-size: .82rem; opacity:.86; white-space:nowrap; }
    .preview-art { height: 215px; display:grid; place-items:center; overflow:hidden; }
    .preview-art svg { width:100% !important; height:100% !important; max-height:205px !important; filter:none !important; }
    div.stDownloadButton > button { width: 100%; border-radius: 14px; min-height: 42px; font-weight: 700; }
    div[data-testid="stExpander"] { border-radius: 16px; background:#fffaf7; }
    @media (max-width: 700px) {
      .block-container { padding-left:.75rem; padding-right:.75rem; }
      .sticky-preview { top:.1rem; }
      .preview-shell { border-radius:18px; padding:9px 10px 11px; }
      .preview-art { height:165px; }
      .preview-art svg { max-height:158px !important; }
      .preview-head strong { font-size:.9rem; }
      .preview-head span { font-size:.74rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


COMPONENT_PREFIX = {
    "base": "base", "border": "border", "name": "name", "name2": "name2",
    "profession": "profession", "extra_text": "extra", "symbol": "symbol",
}
DEFAULTS = {
    "base": {"size": 100},
    "border": {"size": 100, "x": 0.0, "y": 0.0},
    "name": {"size": 100, "x": 0.0, "y": 0.0},
    "name2": {"size": 100, "x": 0.0, "y": 0.0},
    "profession": {"size": 100, "x": 0.0, "y": 0.0},
    "extra_text": {"size": 100, "x": 0.0, "y": 0.0},
    "symbol": {"size": 100, "x": 0.0, "y": 0.0},
}


def cfg(component, field):
    return st.session_state.get(f"cfg_{component}_{field}", DEFAULTS[component][field])


def reset_component(component):
    prefix = COMPONENT_PREFIX[component]
    for field, value in DEFAULTS[component].items():
        st.session_state[f"cfg_{component}_{field}"] = value
        st.session_state.pop(f"edit_{prefix}_{field}", None)
    st.session_state[f"cfg_round_mode_{component}"] = "Whole component"
    st.session_state[f"cfg_round_radius_{component}"] = 0.0
    st.session_state[f"cfg_round_corners_{component}"] = []
    for field in ("mode", "radius", "corners"):
        st.session_state.pop(f"edit_round_{field}_{component}", None)


# Save the currently rendered editor widgets before a different component opens.
for component, prefix in COMPONENT_PREFIX.items():
    for field in DEFAULTS[component]:
        widget_key = f"edit_{prefix}_{field}"
        if widget_key in st.session_state:
            st.session_state[f"cfg_{component}_{field}"] = st.session_state[widget_key]
    for field in ("mode", "radius", "corners"):
        widget_key = f"edit_round_{field}_{component}"
        if widget_key in st.session_state:
            st.session_state[f"cfg_round_{field}_{component}"] = st.session_state[widget_key]


font_names = list(FONT_FILES)
default_small_font = "Barlow Condensed SemiBold"
CONTENT_DEFAULTS = {
    "content_name": "AMELIA", "content_name2": "", "content_profession": "ENROLLED NURSE",
    "content_extra": "", "content_shape": next(iter(SHAPES)), "content_symbol": next(iter(SYMBOLS)),
    "content_colour": "#ed7594", "content_auto": True, "content_name_font": font_names[0],
    "content_name2_font": font_names[0], "content_profession_font": default_small_font,
    "content_extra_font": default_small_font,
    "touch_mode": False,
}
for key, value in CONTENT_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

name = st.session_state.get("content_name", "AMELIA").upper()
name2 = st.session_state.get("content_name2", "").upper()
profession = st.session_state.get("content_profession", "ENROLLED NURSE").upper()
extra_text = st.session_state.get("content_extra", "").upper()
shape_name = st.session_state.get("content_shape", next(iter(SHAPES)))
symbol_name = st.session_state.get("content_symbol", next(iter(SYMBOLS)))
base_colour = st.session_state.get("content_colour", "#ed7594")
auto_enlarge = st.session_state.get("content_auto", True)
name_font = st.session_state.get("content_name_font", font_names[0])
name2_font = st.session_state.get("content_name2_font", font_names[0])
profession_font = st.session_state.get("content_profession_font", default_small_font)
extra_font = st.session_state.get("content_extra_font", default_small_font)

values = badge_values(
    name, profession, shape_name, name_font, symbol_name, auto_enlarge,
    profession_font=profession_font, name2=name2, name2_font=name2_font,
    extra_text=extra_text, extra_font=extra_font, badge_size=int(cfg("base", "size")),
    border_size=int(cfg("border", "size")), border_x=float(cfg("border", "x")), border_y=float(cfg("border", "y")),
    symbol_size=int(cfg("symbol", "size")), symbol_x=float(cfg("symbol", "x")), symbol_y=float(cfg("symbol", "y")),
    name_size=int(cfg("name", "size")), name_x=float(cfg("name", "x")), name_y=float(cfg("name", "y")),
    name2_size=int(cfg("name2", "size")), name2_x=float(cfg("name2", "x")), name2_y=float(cfg("name2", "y")),
    profession_size=int(cfg("profession", "size")), profession_x=float(cfg("profession", "x")), profession_y=float(cfg("profession", "y")),
    extra_size=int(cfg("extra_text", "size")), extra_x=float(cfg("extra_text", "x")), extra_y=float(cfg("extra_text", "y")),
)

rounding = {}
for component in COMPONENT_PREFIX:
    rounding[component] = {
        "mode": st.session_state.get(f"cfg_round_mode_{component}", "Whole component"),
        "radius": float(st.session_state.get(f"cfg_round_radius_{component}", 0.0)),
        "corners": [int(number) - 1 for number in st.session_state.get(f"cfg_round_corners_{component}", [])],
    }
values["rounding"] = rounding
hidden_components = set(st.session_state.get("hidden_components", []))

# Typing/replacing content restores that layer, but an intentionally deleted
# unchanged layer stays hidden until the user presses Restore.
restore_when_changed = {
    "name": name,
    "name2": name2,
    "profession": profession,
    "extra_text": extra_text,
    "symbol": symbol_name,
    "border": shape_name,
}
for component, current_content in restore_when_changed.items():
    previous_key = f"previous_content_{component}"
    previous_content = st.session_state.get(previous_key)
    is_present = bool(current_content) and current_content != "No symbol"
    if is_present and previous_content != current_content:
        hidden_components.discard(component)
    st.session_state[previous_key] = current_content
st.session_state["hidden_components"] = sorted(hidden_components)
values["hidden"] = hidden_components


st.markdown('<div class="badge-kicker">Teddie &amp; Lane</div><div class="badge-title">Badge Builder</div>', unsafe_allow_html=True)
st.toggle("Touch edit directly on preview", key="touch_mode")

if st.session_state["touch_mode"]:
    st.caption("Tap or choose a part, drag it to move, or drag the square handle to resize.")
    labels = {
        "base": "Badge overall", "border": "White border", "name": "Name line 1",
        "name2": "Name line 2", "profession": "Profession", "extra_text": "Additional text", "symbol": "Symbol",
    }
    touch_layers = []
    for layer in LAYER_FILES:
        markup = layer_markup(layer, values)
        if not markup:
            continue
        touch_layers.append({
            "id": layer, "label": labels[layer], "markup": markup,
            "fill": base_colour if layer == "base" else "#fffaf7",
            "size": float(cfg(layer, "size")),
            "minSize": 70 if layer == "base" else 40,
            "maxSize": 150 if layer == "base" else 180,
            "x": float(cfg(layer, "x")) if "x" in DEFAULTS[layer] else 0.0,
            "y": float(cfg(layer, "y")) if "y" in DEFAULTS[layer] else 0.0,
        })
    touch_result = touch_badge_editor(
        width=values["width"], height=values["height"], background="#b95f7d",
        layers=touch_layers, key="touch_badge_canvas", default=None,
    )
    if touch_result and touch_result.get("nonce") != st.session_state.get("last_touch_nonce"):
        st.session_state["last_touch_nonce"] = touch_result.get("nonce")
        changed_component = touch_result.get("component")
        if touch_result.get("action") == "delete" and changed_component != "base":
            hidden_components.add(changed_component)
            st.session_state["hidden_components"] = sorted(hidden_components)
        elif touch_result.get("action") == "update" and changed_component in COMPONENT_PREFIX:
            for field in ("size", "x", "y"):
                if field in touch_result and field in DEFAULTS[changed_component]:
                    st.session_state[f"cfg_{changed_component}_{field}"] = touch_result[field]
                    st.session_state.pop(f"edit_{COMPONENT_PREFIX[changed_component]}_{field}", None)
        st.rerun()
else:
    st.caption("Edit below—the preview stays visible while you make changes.")
    svg = preview_svg(values, base_colour)
    st.markdown(
        f'<div class="sticky-preview"><div class="preview-shell">'
        f'<div class="preview-head"><strong>LIVE PREVIEW</strong><span>{values["width"]:.1f} × {values["height"]:.1f} mm</span></div>'
        f'<div class="preview-art">{svg}</div></div></div>',
        unsafe_allow_html=True,
    )

if hidden_components:
    st.warning("Hidden parts: " + ", ".join(layer.replace("_", " ").title() for layer in sorted(hidden_components)))
    if st.button("Restore all deleted parts", use_container_width=True):
        st.session_state["hidden_components"] = []
        st.rerun()


with st.expander("1. Text, shape and fonts", expanded=True):
    left, right = st.columns(2)
    with left:
        st.selectbox("Badge shape", list(SHAPES), key="content_shape")
        st.selectbox("Symbol", list(SYMBOLS), key="content_symbol")
        st.color_picker("Base colour", key="content_colour")
        st.toggle("Enlarge proportionally for long names", key="content_auto")
    with right:
        st.text_input("Name — line 1", max_chars=24, key="content_name")
        st.selectbox("Name line 1 font", font_names, key="content_name_font")
        st.text_input("Name — line 2 (optional)", max_chars=24, key="content_name2")
        st.selectbox("Name line 2 font", font_names, key="content_name2_font", disabled=not name2)
        st.text_input("Profession", max_chars=32, key="content_profession")
        st.selectbox("Profession font", font_names, key="content_profession_font")
        st.text_input("Additional text (optional)", max_chars=32, key="content_extra")
        st.selectbox("Additional text font", font_names, key="content_extra_font", disabled=not extra_text)
        if "Consolas" not in FONT_FILES:
            st.caption("To enable exact Consolas, upload your licensed file as Consolas.ttf beside app.py.")


component_options = {"Badge overall": "base"}
if SHAPES[shape_name].get("white") and "border" not in hidden_components:
    component_options["White border"] = "border"
if "name" not in hidden_components:
    component_options["Name line 1"] = "name"
if name2 and "name2" not in hidden_components:
    component_options["Name line 2"] = "name2"
if "profession" not in hidden_components:
    component_options["Profession"] = "profession"
if extra_text and "extra_text" not in hidden_components:
    component_options["Additional text"] = "extra_text"
if symbol_name != "No symbol" and "symbol" not in hidden_components:
    component_options["Symbol"] = "symbol"
if st.session_state.get("edit_component_choice") not in component_options:
    st.session_state["edit_component_choice"] = next(iter(component_options))

with st.expander("2. Edit size, position and corners", expanded=True):
    component_label = st.selectbox("Component to edit", list(component_options), key="edit_component_choice")
    component = component_options[component_label]
    prefix = COMPONENT_PREFIX[component]

    st.markdown(f"**{component_label} — size and position**")
    if component == "base":
        st.number_input("Overall size (%)", min_value=70, max_value=150, step=1, value=int(cfg(component, "size")), key=f"edit_{prefix}_size")
        st.caption("The badge base is the SVG canvas and remains centred.")
    else:
        size_col, x_col, y_col = st.columns(3)
        with size_col:
            st.number_input("Size (%)", min_value=40, max_value=180, step=1, value=int(cfg(component, "size")), key=f"edit_{prefix}_size")
        with x_col:
            st.number_input("Left / right (mm)", min_value=-25.0, max_value=25.0, step=0.25, value=float(cfg(component, "x")), key=f"edit_{prefix}_x")
        with y_col:
            st.number_input("Up / down (mm)", min_value=-20.0, max_value=20.0, step=0.25, value=float(cfg(component, "y")), key=f"edit_{prefix}_y")

    st.divider()
    st.markdown(f"**{component_label} — corner rounding**")
    round_mode = st.radio(
        "Round",
        ["Whole component", "Selected corners"],
        horizontal=True,
        index=0 if rounding[component]["mode"] == "Whole component" else 1,
        key=f"edit_round_mode_{component}",
    )
    st.number_input(
        "Corner rounding amount (mm)", min_value=0.0, max_value=8.0, step=0.25,
        value=float(rounding[component]["radius"]), key=f"edit_round_radius_{component}",
        help="Try 2–4 mm first so the change is easy to see. Set to 0 for the exact original outline.",
    )
    corner_count = len(component_corner_points(component, values))
    if round_mode == "Selected corners":
        selected_default = [str(number + 1) for number in rounding[component]["corners"] if number < corner_count]
        st.multiselect(
            "Corner numbers", [str(number) for number in range(1, corner_count + 1)],
            default=selected_default, key=f"edit_round_corners_{component}",
        )
        st.caption("Choose the numbers from the enlarged corner map below.")
        components.html(
            '<div style="background:#fffaf7;border:1px solid #eaded8;border-radius:16px;padding:10px;">'
            + corner_editor_svg(component, values) + "</div>",
            height=280,
            scrolling=False,
        )
    elif corner_count == 0:
        st.info("This component is already a smooth curve, so it has no sharp corners to round.")
    else:
        st.caption(f"{corner_count} detected corners will be rounded. Try 2–4 mm for an obvious preview change.")

    st.button("Reset this component", use_container_width=True, on_click=reset_component, args=(component,))


st.subheader("Download")
folder = f'{clean_file_name(values["name"])}_{clean_file_name(values["profession"])}'
st.download_button(
    "⬇ Download complete Tinkercad ZIP",
    data=make_zip_pack(values),
    file_name=f"{folder}_TINKERCAD_SVG_PACK.zip",
    mime="application/zip",
    type="primary",
    use_container_width=True,
)
st.caption("Every visible part is exported as a separate, aligned SVG.")

with st.expander("Download individual SVG files"):
    for layer, file_name in LAYER_FILES.items():
        if not layer_markup(layer, values):
            continue
        label = layer.replace("_", " ").title()
        st.download_button(
            f"Download {label} SVG", data=make_svg(layer, values), file_name=file_name,
            mime="image/svg+xml", use_container_width=True, key=f"download-{layer}",
        )

with st.expander("Tinkercad setup"):
    st.markdown(
        f"1. Import every SVG at 100% and align their centres. Canvas: **{values['width']:.1f} × {values['height']:.1f} mm**.\n\n"
        "2. Set the base to **2.0 mm** high.\n\n"
        "3. Set white parts to **0.8 mm** high and place them at **Z = 2.0 mm**.\n\n"
        "4. Without AMS, add one filament change at **2.0 mm**."
    )

st.caption("Uploaded shapes retain their original artwork proportions.")
