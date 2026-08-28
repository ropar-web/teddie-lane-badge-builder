import streamlit as st
import streamlit.components.v1 as components

from badge_engine import FONT_FILES, LAYER_FILES, SHAPES, SYMBOLS, badge_values, clean_file_name, component_corner_points, corner_editor_svg, layer_markup, make_svg, make_zip_pack, preview_svg


st.set_page_config(page_title="Teddie & Lane Badge Builder", page_icon="🏷️", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background: #f8f4f1; color: #322d35; }
    [data-testid="stSidebar"] { background: #fffaf7; border-right: 1px solid #eaded8; }
    .block-container { max-width: 1450px; padding-top: 1.4rem; }
    .badge-title { font-size: 1.85rem; font-weight: 800; letter-spacing: -.03em; margin-bottom: .15rem; }
    .badge-kicker { color: #b17588; font-size: .75rem; font-weight: 800; letter-spacing: .18em; text-transform: uppercase; }
    .preview-card { background: #df6f91; border-radius: 28px; padding: 1.1rem 1.3rem; color: white; margin-bottom: 1rem; }
    .preview-meta { font-weight: 800; font-size: 1.1rem; }
    div.stDownloadButton > button { width: 100%; border-radius: 14px; min-height: 42px; font-weight: 700; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="badge-kicker">Teddie &amp; Lane</div><div class="badge-title">Badge Builder</div>', unsafe_allow_html=True)
st.caption("Exact vector shapes • separate Tinkercad-ready SVG parts • native downloads")

with st.expander("1. Badge content and fonts", expanded=True):
    content_left, content_right = st.columns(2)
    with content_left:
        shape_name = st.selectbox("Badge shape", list(SHAPES))
        symbol_name = st.selectbox("Symbol", list(SYMBOLS))
        base_colour = st.color_picker("Base colour", "#ed7594")
        auto_enlarge = st.toggle("Enlarge proportionally for long names", value=True)
    with content_right:
        name = st.text_input("Name — line 1", value="AMELIA", max_chars=24).upper()
        name_font = st.selectbox("Name line 1 font", list(FONT_FILES), key="name_font")
        name2 = st.text_input("Name — line 2 (optional)", value="", max_chars=24).upper()
        name2_font = st.selectbox("Name line 2 font", list(FONT_FILES), key="name2_font", disabled=not name2)
        profession = st.text_input("Profession", value="ENROLLED NURSE", max_chars=32).upper()
        profession_font = st.selectbox("Profession font", list(FONT_FILES), index=list(FONT_FILES).index("Barlow Condensed SemiBold"), key="profession_font")
        extra_text = st.text_input("Additional text line (optional)", value="", max_chars=32).upper()
        extra_font = st.selectbox("Additional text font", list(FONT_FILES), index=list(FONT_FILES).index("Barlow Condensed SemiBold"), key="extra_font", disabled=not extra_text)

adjustment_options = {"Badge overall": "base"}
if SHAPES[shape_name].get("white"):
    adjustment_options["White border"] = "border"
adjustment_options["Name line 1"] = "name"
if name2:
    adjustment_options["Name line 2"] = "name2"
adjustment_options["Profession"] = "profession"
if extra_text:
    adjustment_options["Additional text"] = "extra_text"
if symbol_name != "No symbol":
    adjustment_options["Symbol"] = "symbol"

with st.expander("2. Size and position controls", expanded=True):
    st.caption("Open a component tab, then change its size and position. Every tab keeps its own values.")
    adjustment_tabs = st.tabs(list(adjustment_options))
    for tab, (adjust_label, adjust_component) in zip(adjustment_tabs, adjustment_options.items()):
        with tab:
            if adjust_component == "base":
                st.slider("Badge overall size (%)", 70, 150, 100, key="badge_size")
                st.caption("The base defines the SVG canvas, so it remains centred. All other parts can move independently.")
            else:
                prefix = {"border": "border", "name": "name", "name2": "name2", "profession": "profession", "extra_text": "extra", "symbol": "symbol"}[adjust_component]
                minimum_size, maximum_size = ((50, 160) if adjust_component in ("border", "symbol") else (40, 180))
                st.slider(f"{adjust_label} size (%)", minimum_size, maximum_size, 100, key=f"{prefix}_size")
                st.slider(f"{adjust_label} left / right (mm)", -25.0, 25.0, 0.0, 0.25, key=f"{prefix}_x")
                st.slider(f"{adjust_label} up / down (mm)", -20.0, 20.0, 0.0, 0.25, key=f"{prefix}_y")

def saved(key, default):
    return st.session_state.get(key, default)

badge_size = saved("badge_size", 100)
border_size, border_x, border_y = saved("border_size", 100), saved("border_x", 0.0), saved("border_y", 0.0)
symbol_size, symbol_x, symbol_y = saved("symbol_size", 100), saved("symbol_x", 0.0), saved("symbol_y", 0.0)
name_size, name_x, name_y = saved("name_size", 100), saved("name_x", 0.0), saved("name_y", 0.0)
name2_size, name2_x, name2_y = saved("name2_size", 100), saved("name2_x", 0.0), saved("name2_y", 0.0)
profession_size, profession_x, profession_y = saved("profession_size", 100), saved("profession_x", 0.0), saved("profession_y", 0.0)
extra_size, extra_x, extra_y = saved("extra_size", 100), saved("extra_x", 0.0), saved("extra_y", 0.0)

values = badge_values(
    name, profession, shape_name, name_font, symbol_name, auto_enlarge,
    profession_font=profession_font, name2=name2, name2_font=name2_font,
    extra_text=extra_text, extra_font=extra_font, badge_size=badge_size,
    border_size=border_size, border_x=border_x, border_y=border_y,
    symbol_size=symbol_size, symbol_x=symbol_x, symbol_y=symbol_y,
    name_size=name_size, name_x=name_x, name_y=name_y,
    name2_size=name2_size, name2_x=name2_x, name2_y=name2_y,
    profession_size=profession_size, profession_x=profession_x, profession_y=profession_y,
    extra_size=extra_size, extra_x=extra_x, extra_y=extra_y,
)

with st.expander("3. Corner and edge editor", expanded=False):
    st.caption("Each component has its own tab and keeps its own rounding settings.")
    component_options = {"Badge shape": "base"}
    if SHAPES[shape_name].get("white"):
        component_options["White border"] = "border"
    component_options["Name line 1"] = "name"
    if name2:
        component_options["Name line 2"] = "name2"
    component_options["Profession"] = "profession"
    if extra_text:
        component_options["Additional text"] = "extra_text"
    if symbol_name != "No symbol":
        component_options["Symbol"] = "symbol"

    corner_tabs = st.tabs(list(component_options))
    for tab, (component_label, component_key) in zip(corner_tabs, component_options.items()):
        with tab:
            component_mode = st.radio(
                "Apply rounding to",
                ["Whole component", "Selected corners"],
                horizontal=True,
                key=f"round_mode_{component_key}",
            )
            st.slider(
                "Round / smooth amount (mm)", 0.0, 3.0, 0.0, 0.1,
                key=f"round_radius_{component_key}",
                help="0 keeps the original SVG exactly. Increase gradually for softer corners and edges.",
            )
            corner_count = len(component_corner_points(component_key, values))
            if component_mode == "Selected corners":
                st.multiselect(
                    "Corners to round",
                    [str(number) for number in range(1, corner_count + 1)],
                    key=f"round_corners_{component_key}",
                    help="Use the numbered corner map below the main preview.",
                )
                st.caption(f"{corner_count} selectable corners found.")
            else:
                st.caption("All detected sharp corners on this component will be softened.")
    corner_map_label = st.selectbox("Numbered corner map component", list(component_options), key="corner_map_component")
    selected_component = component_options[corner_map_label]

rounding = {}
for component in ("base", "border", "name", "name2", "profession", "extra_text", "symbol"):
    saved_mode = st.session_state.get(f"round_mode_{component}", "Whole component")
    saved_corners = st.session_state.get(f"round_corners_{component}", [])
    rounding[component] = {
        "mode": saved_mode,
        "radius": st.session_state.get(f"round_radius_{component}", 0.0),
        "corners": [int(number) - 1 for number in saved_corners],
    }
values["rounding"] = rounding
marker_component = selected_component if rounding[selected_component]["mode"] == "Selected corners" else None

left, right = st.columns([1.5, 1], gap="large")
with left:
    st.markdown(
        f'<div class="preview-card"><div class="badge-kicker" style="color:rgba(255,255,255,.75)">Live preview</div>'
        f'<div class="preview-meta">{values["width"]:.1f} × {values["height"]:.1f} mm badge</div></div>',
        unsafe_allow_html=True,
    )
    svg = preview_svg(values, base_colour)
    components.html(
        '<div style="background:#c85f80;border-radius:30px;padding:36px;display:grid;place-items:center;">'
        + svg
        + "</div>",
        height=460,
        scrolling=False,
    )
    if marker_component:
        st.caption(f"Numbered corner map — {corner_map_label}")
        components.html(
            '<div style="background:#fffaf7;border:1px solid #eaded8;border-radius:18px;padding:14px;display:grid;place-items:center;">'
            + corner_editor_svg(marker_component, values)
            + "</div>",
            height=290,
            scrolling=False,
        )

with right:
    st.subheader("Download all parts")
    folder = f'{clean_file_name(values["name"])}_{clean_file_name(values["profession"])}'
    st.download_button(
        "⬇ Download complete Tinkercad ZIP",
        data=make_zip_pack(values),
        file_name=f"{folder}_TINKERCAD_SVG_PACK.zip",
        mime="application/zip",
        type="primary",
        use_container_width=True,
    )
    st.caption("The ZIP contains the base, white border, name, profession and any symbol as separate aligned files.")

    st.divider()
    st.subheader("Download individual SVGs")
    for layer, file_name in LAYER_FILES.items():
        if not layer_markup(layer, values):
            continue
        label = layer.replace("_", " ").title()
        st.download_button(
            f"Download {label} SVG",
            data=make_svg(layer, values),
            file_name=file_name,
            mime="image/svg+xml",
            use_container_width=True,
            key=f"download-{layer}",
        )

st.divider()
st.subheader("Tinkercad setup")
step1, step2, step3 = st.columns(3)
step1.info(f"**1. Import and align**\n\nImport every SVG at 100% and align their centres. Canvas: {values['width']:.1f} × {values['height']:.1f} mm.")
step2.info("**2. Set the heights**\n\nBase: 2.0 mm. White parts: 0.8 mm tall, placed at Z = 2.0 mm.")
step3.info("**3. Print the colour**\n\nWithout AMS, add one filament change at 2.0 mm for the raised white details.")

st.caption("All uploaded shapes keep their original artwork proportions. Only unused Silhouette canvas whitespace is removed.")
