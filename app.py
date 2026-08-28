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

with st.sidebar:
    st.header("Badge details")
    name = st.text_input("Name", value="AMELIA", max_chars=24).upper()
    profession = st.text_input("Profession", value="ENROLLED NURSE", max_chars=32).upper()
    shape_name = st.selectbox("Badge shape", list(SHAPES))
    name_font = st.selectbox("Name font", [name for name in FONT_FILES if name != "Barlow Condensed SemiBold"])
    symbol_name = st.selectbox("Symbol", list(SYMBOLS))
    auto_enlarge = st.toggle("Enlarge proportionally for long names", value=True)
    base_colour = st.color_picker("Base colour", "#ed7594")

    with st.expander("Fine-tune size and position"):
        st.caption("The preview and downloaded SVG files use these exact adjustments.")
        symbol_size = st.slider("Symbol size (%)", 50, 160, 100, disabled=symbol_name == "No symbol")
        symbol_x = st.slider("Symbol left / right (mm)", -20.0, 20.0, 0.0, 0.5, disabled=symbol_name == "No symbol")
        symbol_y = st.slider("Symbol up / down (mm)", -15.0, 15.0, 0.0, 0.5, disabled=symbol_name == "No symbol")
        name_size = st.slider("Name size (%)", 60, 140, 100)
        name_x = st.slider("Name left / right (mm)", -15.0, 15.0, 0.0, 0.5)
        name_y = st.slider("Name up / down (mm)", -10.0, 10.0, 0.0, 0.5)
        profession_size = st.slider("Profession size (%)", 60, 140, 100)
        profession_x = st.slider("Profession left / right (mm)", -15.0, 15.0, 0.0, 0.5)
        profession_y = st.slider("Profession up / down (mm)", -10.0, 10.0, 0.0, 0.5)

values = badge_values(
    name, profession, shape_name, name_font, symbol_name, auto_enlarge,
    symbol_size=symbol_size, symbol_x=symbol_x, symbol_y=symbol_y,
    name_size=name_size, name_x=name_x, name_y=name_y,
    profession_size=profession_size, profession_x=profession_x, profession_y=profession_y,
)

with st.sidebar:
    with st.expander("Corner & edge editor", expanded=False):
        st.caption("Edit one component at a time. Every component remembers its own settings.")
        component_options = {"Badge shape": "base"}
        if SHAPES[shape_name].get("white"):
            component_options["White border"] = "border"
        component_options["Name text"] = "name"
        component_options["Profession text"] = "profession"
        if symbol_name != "No symbol":
            component_options["Symbol"] = "symbol"

        component_label = st.selectbox("Selected component", list(component_options))
        selected_component = component_options[component_label]
        mode = st.radio(
            "Apply rounding to",
            ["Whole component", "Selected corners"],
            horizontal=True,
            key=f"round_mode_{selected_component}",
        )
        radius = st.slider(
            "Round / smooth amount (mm)",
            0.0,
            3.0,
            0.0,
            0.1,
            key=f"round_radius_{selected_component}",
            help="0 keeps the original SVG exactly. Increase gradually for softer corners and edges.",
        )
        corner_count = len(component_corner_points(selected_component, values))
        if mode == "Selected corners":
            corner_choices = [str(number) for number in range(1, corner_count + 1)]
            st.multiselect(
                "Corners to round",
                corner_choices,
                key=f"round_corners_{selected_component}",
                help="The matching numbers appear on the live preview.",
            )
            st.caption(f"{corner_count} selectable corners found. Choose their numbers in the preview.")
        else:
            st.caption("All detected corners and sharp edge changes on this component will be softened.")

rounding = {}
for component in ("base", "border", "name", "profession", "symbol"):
    saved_mode = st.session_state.get(f"round_mode_{component}", "Whole component")
    saved_corners = st.session_state.get(f"round_corners_{component}", [])
    rounding[component] = {
        "mode": saved_mode,
        "radius": st.session_state.get(f"round_radius_{component}", 0.0),
        "corners": [int(number) - 1 for number in saved_corners],
    }
values["rounding"] = rounding
marker_component = selected_component if mode == "Selected corners" else None

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
        st.caption(f"Numbered corner map — {component_label}")
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
