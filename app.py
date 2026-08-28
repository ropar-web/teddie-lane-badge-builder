import streamlit as st
import streamlit.components.v1 as components

from badge_engine import FONT_FILES, LAYER_FILES, SHAPES, SYMBOLS, badge_values, clean_file_name, layer_markup, make_svg, make_zip_pack, preview_svg


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

values = badge_values(name, profession, shape_name, name_font, symbol_name, auto_enlarge)

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

st.caption("Uploaded Shape 1 keeps its original artwork proportions. Only the unused Silhouette canvas whitespace is removed.")
