# gotowy podstawowy interfejs strony, trzeba popodstawiać wartwy

import io, os, base64
import numpy as np
from PIL import Image
import streamlit as st
import folium
from streamlit_folium import st_folium
import rasterio
from rasterio.io import MemoryFile
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.coords import BoundingBox
import base64
import streamlit as st
import folium
from folium.features import CustomIcon
from streamlit_folium import st_folium
import numpy as np
import io, os, base64
import numpy as np
from PIL import Image
import streamlit as st
import folium
from streamlit_folium import st_folium
import rasterio
from rasterio.coords import BoundingBox
import colorsys

# ---------- Palette (for internal use) ----------
PALETTE = {
    "purple": "#30172c",
    "orange": "#f37e26",
    "beige":  "#f8edde",
    "green":  "#1d7e85",
    "red":    "#e13f51",
}

# ---------- Page & theme ----------
st.set_page_config(page_title="Olkusz Mining data", layout="wide")

# ---------- Assets as Base64 (works locally & on Streamlit Cloud) ----------
def load_b64(path: str) -> str | None:
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None

logo_b64 = load_b64("logo.png")
icon_b64 = load_b64("icon.png")

# If we have base64, use a data URL; otherwise folium will try to load from path/URL
icon_src = f"data:image/png;base64,{icon_b64}" if icon_b64 else "icon.png"

background_b64 = load_b64("background.png")
if background_b64:
    st.markdown(
        f"""
        <style>
        html, body, [data-testid="stAppViewContainer"] {{
            background: url("data:image/png;base64,{background_b64}") no-repeat center center fixed !important;
            background-size: cover !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# ---------- CSS + Fixed Top Bar ----------
st.markdown(f"""
<style>
:root {{
  --purple: {PALETTE["purple"]};
  --orange: {PALETTE["orange"]};
  --beige:  {PALETTE["beige"]};
  --green:  {PALETTE["green"]};
  --red:    {PALETTE["red"]};
}}
html, body, [data-testid="stAppViewContainer"] {{
  /* background: var(--beige) !important;  <-- REMOVED THIS LINE */
  color: var(--purple) !important;
  margin: 0;
  padding: 0;
  font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
  scroll-behavior: smooth;
}}
header[data-testid="stHeader"] {{ display: none; }}
footer {{ visibility: hidden; }}
section.main > div:first-child {{
  padding-top: 64px !important;
}}
[data-testid="stAppViewContainer"] .main > div:first-child {{
  padding-top: 64px !important;
}}
.leaflet-popup-content {{
  color: var(--purple);
  font-family: inherit;
}}
.fixed-top-bar {{
  position: fixed;
  inset: 0 0 auto 0;
  height: 75px;
  background-color: var(--purple);
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 2rem;
  z-index: 9999;
  box-shadow: 0 2px 5px rgba(0,0,0,.2);
}}
.fixed-top-bar .brand {{
  display: flex;
  align-items: center;
  gap: .75rem;
}}
.fixed-top-bar .brand img {{
  height: 45px;
  width: auto;
  display: block;
}}
.fixed-top-bar .nav-center, .fixed-top-bar .nav-right {{
  display: flex;
  gap: 1.5rem;
  align-items: center;
}}
.fixed-top-bar .nav-btn {{
  background: none;
  border: none;
  color: white;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  padding: 8px 24px;
  border-radius: 999px;
  transition: background 0.2s, color 0.2s;
  text-decoration: none;
  outline: none;
}}
.fixed-top-bar .nav-btn:hover {{
  background: var(--orange);
  color: var(--purple);
}}
.fixed-top-bar .nav-btn-join {{
  background: white !important;
  color: var(--purple) !important;
  border: none;
  font-weight: 600;
  padding: 8px 24px;
  border-radius: 999px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}}
.fixed-top-bar .nav-btn-join:hover {{
  background: var(--orange) !important;
  color: var(--purple) !important;
}}
.fullscreen-home-img {{
  width: 100vw;
  height: 100vh;
  object-fit: cover;
  display: block;
  pointer-events: none;
  user-select: none;
  margin: 0;
  padding: 0;
  border: none;
}}
[data-testid="stVerticalBlock"] > div:first-child {{
  padding: 0 !important;
  margin: 0 !important;
}}
</style>
<div class="fixed-top-bar">
  <div class="brand">
    {"<img src='data:image/png;base64," + logo_b64 + "' alt='Logo'/>" if logo_b64 else ""}
  </div>
  <div class="nav-center">
    <a href="#home" class="nav-btn" id="home-btn">Home</a>
    <a href="#overview" class="nav-btn">Overview</a>
    <a href="#capabilities" class="nav-btn">Capabilities</a>
  </div>
  <div class="nav-right">
    <a href="#contact" class="nav-btn">Contact</a>
    <button class="nav-btn nav-btn-join">Join</button>
  </div>
</div>

""", unsafe_allow_html=True)

# ---------- Home Section ----------
home_img_b64 = load_b64("home.png")
if home_img_b64:
    st.markdown(
        f"""
        <style>
        .fullscreen-home-img {{
            width: 100%;
            max-width: 100vw;
            height: auto;
            display: block;
            pointer-events: none;
            user-select: none;
            margin: 0;
            padding: 0;
            border: none;
        }}
        </style>
        <a id='home'></a>
        <img id='fullscreen-home-img' class='fullscreen-home-img' src='data:image/png;base64,{home_img_b64}' draggable='false'/>
        """,
        unsafe_allow_html=True
    )
else:
    st.info("Home image not found.")

# ---------- Overview Section ----------
st.markdown("""
<div style="height: 80px;"></div>
<div style="
    max-width: 900px;
    margin: 48px auto 0 auto;
    padding: 2.5rem 2rem;
    background: #f8edde;
    border-radius: 24px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.04);
">
  <section id="overview" style="padding: 0; margin: 0;">
    <h2 style="color:#30172c;">Who We Are</h2>
    <p><strong>ITB</strong> is a research team specializing in the use of satellite data — radar data enhanced with optical imagery — to study the environmental effects of mine closures.</p>
    <h3 style="color:#f37e26;">The Problem</h3>
    <p>The closure of the Olkusz–Pomorzany mine in 2020 caused rising groundwater levels and the formation of sinkholes where water began to accumulate. These phenomena pose risks to people, infrastructure, and the environment. Continuous, objective monitoring of surface changes is essential.</p>
    <h3 style="color:#1d7e85;">Our Solution</h3>
    <ul>
      <li>Use of <strong>radar data (InSAR)</strong> to detect and analyze ground deformation and historical displacement.</li>
      <li>Application of <strong>optical data</strong> to automatically calculate <strong>NDVI</strong> and <strong>Bare Soil Marker</strong> indicators, tracking vegetation and soil exposure.</li>
      <li>Presentation of results as <strong>risk maps</strong> and <strong>decision-support reports</strong>.</li>
    </ul>
    <h3 style="color:#e13f51;">Who Benefits</h3>
    <p>Geologists, local governments, and emergency services (e.g., for land-use plan updates), as well as property valuation experts and infrastructure planners.</p>
    <h3 style="color:#30172c;">Benefits</h3>
    <ul>
      <li>Early detection of environmental and structural hazards.</li>
      <li>Objective, large-scale surface monitoring over time.</li>
      <li>Automated assessment of key environmental indicators.</li>
    </ul>
    <h3 style="color:#f37e26;">Current Limitations</h3>
    <p>Processing radar data is resource-intensive. Without access to cloud computing environments, each interferogram must be processed manually, which limits automation for individual analyses.</p>
  </section>
</div>
""", unsafe_allow_html=True)

# ---------- Sites (Olkusz) ----------
sites = [
    (
        "Podwodnica",
        50.2938563, 19.4831411,
        "Obwodnica miejscowości Bolesław, która wskutek likwidacji odwodnień Zakładów Górniczo-Hutniczych \"Bolesław\" jest regularnie podtapiana. Jest to świadectwo na podnoszące się zwierciadło wód podziemnych. (Warstwy: Altymetria, NDWI)"
    ),
    (
        "Jezioro Bolesławskie",
        50.2773134, 19.5117006,
        "Jezioro antropogeniczne powstałe w wyniku likwidacji odwodnień Zakładów Górniczo-Hutniczych \"Bolesław\". Akwen powstał kilkanaście lat wcześniej niż przewidziały prognozy. (Warstwy: NDWI)"
    ),
    (
        "Zapadliska w miejscowości Hutki",
        50.3036844, 19.4996411,
        "Jeden z wielu przykładów zapadlisk pojawiających się na terenach pogórniczych wskutek zawadniania terenu i spadku stateczności podłoża (Warstwy: Interferometria)"
    ),
    (
        "Rzeka Sztoła",
        50.2747467, 19.3708628,
        "Rzeka, która zanikła przez wyłączenie pomp odwadniających kopalnię Pomorzany, które były pośrednim źródłem zasilania rzeki. (Warstwy: NDWI)"
    ),
]

#------ Helpers ------
def to_png_hsla(data: np.ndarray, raw_gray: bool, hue: float, sat: float, alpha: float) -> bytes:
    bands, H, W = data.shape

    def stretch(b):
        x = b.astype(np.float32)
        m = np.isfinite(x)
        if m.any():
            p2, p98 = np.percentile(x[m], [2, 98])
            x = 255.0 * (x - p2) / (p98 - p2 + 1e-9)
        x = np.clip(x, 0, 255).astype(np.uint8)
        return x

    if bands == 1:
        g = data[0].astype(np.float32)
        if raw_gray:
            mn, mx = np.nanmin(g), np.nanmax(g)
            g = 255.0 * (g - mn) / (mx - mn + 1e-9)
            g = np.clip(g, 0, 255).astype(np.uint8)
        else:
            g = stretch(g)
        img_arr = np.zeros((H, W, 4), dtype=np.uint8)
        for i in range(H):
            for j in range(W):
                v = g[i, j] / 255.0
                # vivid color: lightness=0.5, saturation=sat
                r, g2, b = colorsys.hls_to_rgb(hue, 0.5, sat)
                # alpha zależy od saturation i slidera alpha
                a = int(255 * sat * alpha) if g[i, j] != 0 else 0
                img_arr[i, j, 0] = int(r * 255 * v)
                img_arr[i, j, 1] = int(g2 * 255 * v)
                img_arr[i, j, 2] = int(b * 255 * v)
                img_arr[i, j, 3] = a
        img = Image.fromarray(img_arr, mode="RGBA")
    else:
        if raw_gray:
            g = data[0].astype(np.float32)
            mn, mx = np.nanmin(g), np.nanmax(g)
            g = 255.0 * (g - mn) / (mx - mn + 1e-9)
            g = np.clip(g, 0, 255).astype(np.uint8)
            img_arr = np.stack([g, g, g, np.where(g == 0, 0, int(255 * sat * alpha))], axis=-1).astype(np.uint8)
            img = Image.fromarray(img_arr, mode="RGBA")
        else:
            r = stretch(data[0])
            g_ = stretch(data[1] if bands >= 2 else data[0])
            b = stretch(data[2] if bands >= 3 else data[0])
            mask = ((r == 0) & (g_ == 0) & (b == 0))
            alpha_arr = np.where(mask, 0, int(255 * sat * alpha)).astype(np.uint8)
            img_arr = np.dstack([r, g_, b, alpha_arr])
            img = Image.fromarray(img_arr, mode="RGBA")

    buf = io.BytesIO(); img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()

def bounds_are_valid(b):
    try:
        s, w = b[0]; n, e = b[1]
        if not all(np.isfinite([s, w, n, e])): return False
        if not (-90 <= s <= 90 and -90 <= n <= 90 and -180 <= w <= 180 and -180 <= e <= 180): return False
        if not (n > s and e > w): return False
        return True
    except Exception:
        return False
    
def open_any_to_wgs84(ds, assumed_crs_str: str | None):
    src_crs = ds.crs
    if (src_crs is None) and assumed_crs_str and assumed_crs_str.strip():
        src_crs = assumed_crs_str.strip()

    if (src_crs is None) or (str(src_crs).upper() in ("EPSG:4326", "WGS84", "OGC:CRS84")):
        data = ds.read()
        b = ds.bounds
        return data, [[b.bottom, b.left], [b.top, b.right]], str(src_crs)

    # reprojection to EPSG:4326
    dst_crs = "EPSG:4326"
    transform, width, height = calculate_default_transform(src_crs, dst_crs, ds.width, ds.height, *ds.bounds)
    data = np.zeros((ds.count, height, width), dtype=ds.dtypes[0])
    for i in range(1, ds.count + 1):
        reproject(
            source=rasterio.band(ds, i),
            destination=data[i - 1],
            src_transform=ds.transform,
            src_crs=src_crs,
            dst_transform=transform,
            dst_crs=dst_crs,
            resampling=Resampling.bilinear,
        )
    left = transform.c; top = transform.f
    right = left + transform.a * width
    bottom = top + transform.e * height
    from rasterio.coords import BoundingBox
    bb = BoundingBox(min(left, right), min(bottom, top), max(left, right), max(bottom, top))
    return data, [[bb.bottom, bb.left], [bb.top, bb.right]], str(src_crs)

# ---- List your raster file paths here ----
layer_paths = [
    "/Users/nataliakowalczyk/PycharmProjects/Hackathon/ndwi_diff.tif",
    "/Users/nataliakowalczyk/PycharmProjects/Hackathon/ndwi_before.tif",
    "/Users/nataliakowalczyk/PycharmProjects/Hackathon/ndwi_after.tif",
    "/Users/nataliakowalczyk/PycharmProjects/Hackathon/bsm_after.tif",
    "/Users/nataliakowalczyk/PycharmProjects/Hackathon/bsm_before.tif",
    "/Users/nataliakowalczyk/PycharmProjects/Hackathon/bsm_diff.tif",
]

assumed_crs = "EPSG:2180"
raw_gray = False

# ---------- Map (Olkusz) ----------
st.markdown("<div style='height: 80px;'></div><a id='capabilities'></a>", unsafe_allow_html=True)

# Create the map with multiple base layers
m = folium.Map(
    location=[50.2920, 19.5146],
    zoom_start=13,
    tiles=None,
    control_scale=True
)

# Add base layers
folium.TileLayer("OpenStreetMap", name="OpenStreetMap", control=True).add_to(m)
folium.TileLayer("CartoDB positron", name="Carto Light", control=True).add_to(m)

custom_icon = CustomIcon(
    icon_image=icon_src,
    icon_size=(28, 36),   # width, height
    icon_anchor=(14, 36), # half of width, height
)

for name, la, lo, summary in sites:
    popup_html = f"""
    <div style="color:var(--purple);font-family:system-ui;">
      <b>{name}</b><br/>{summary}
    </div>
    """
    folium.Marker(
        [la, lo],
        tooltip=name,
        popup=folium.Popup(popup_html, max_width=280),
        icon=custom_icon
    ).add_to(m)

# ---- Layer controls ----
layer_settings = {}
N = len(layer_paths)
for idx, path in enumerate(layer_paths):
    name = os.path.basename(path)
    # Evenly distribute hue (0.0 ... 1.0)
    hue_init = idx / N
    # Transparency: 1/N (opacity), so transparency = 1.0 / N
    alpha_init = 1.0 / N
    layer_settings[path] = {
        "show": True,
        "hue": st.session_state.get(f"hue_{name}", hue_init),
        "sat": st.session_state.get(f"sat_{name}", 1.0),
        "alpha": st.session_state.get(f"alpha_{name}", alpha_init)
    }

with st.expander("Layer controls", expanded=True):
    for path in layer_paths:
        name = os.path.basename(path)
        col1, col2, col3, col4 = st.columns([1, 2, 2, 2])
        with col1:
            show = st.checkbox(f"{name}", value=layer_settings[path]["show"], key=f"show_{name}")
        with col2:
            hue_val = st.slider(f"Hue: {name}", 0.0, 1.0, layer_settings[path]["hue"], 0.01, key=f"hue_{name}")
        with col3:
            sat_val = st.slider(f"Saturation: {name}", 0.0, 1.0, layer_settings[path]["sat"], 0.01, key=f"sat_{name}")
        with col4:
            alpha_val = st.slider(f"Transparency: {name}", 0.0, 1.0, layer_settings[path]["alpha"], 0.01, key=f"alpha_{name}")
        layer_settings[path] = {
            "show": show,
            "hue": hue_val,
            "sat": sat_val,
            "alpha": alpha_val
        }

# ---- Load & draw raster overlays ----
try:
    rasters = []
    for path in layer_paths:
        if os.path.exists(path):
            with rasterio.open(path) as ds:
                data, auto_bounds, crs_str = open_any_to_wgs84(ds, assumed_crs)
            rasters.append((os.path.basename(path), data, auto_bounds, crs_str))

    if rasters:
        for name, data, auto_bounds, crs_str in rasters:
            path = next(p for p in layer_settings if os.path.basename(p) == name)
            if not layer_settings[path]["show"]:
                continue
            chosen_bounds = auto_bounds
            hue = layer_settings[path]["hue"]
            sat = layer_settings[path]["sat"]
            alpha = layer_settings[path]["alpha"]
            png = to_png_hsla(data, raw_gray=raw_gray, hue=hue, sat=sat, alpha=alpha)
            data_uri = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
            folium.raster_layers.ImageOverlay(
                image=data_uri, bounds=chosen_bounds, opacity=1.0, name=name, interactive=True
            ).add_to(m)
except Exception as e:
    st.error(f"Błąd ładowania warstw rastrowych: {e}")


# Render the map
map_html = st_folium(m, height=600, width=None, returned_objects=[])

# # Overlay the layer control window: center right over the map
# st.markdown("""
# <style>
# .map-layer-window {
#     position: absolute;
#     top: 100%;
#     right: 60px;
#     transform: translateY(-50%);
#     width: 260px;
#     background: #fff8f0ee;
#     border-radius: 18px;
#     box-shadow: 0 2px 12px rgba(0,0,0,0.10);
#     padding: 1.5rem 1.2rem 1.2rem 1.2rem;
#     z-index: 99999;
#     border: 1px solid #f37e26;
# }
# @media (max-width: 900px) {
#     .map-layer-window {
#         position: static;
#         width: 100%;
#         margin: 1rem 0;
#         transform: none;
#         right: 0;
#         top: auto;
#     }
# }
# </style>
# <div class="map-layer-window">
#   <h4 style="margin-top:0;color:#30172c;">Warstwy mapy</h4>
#   <form>
#     <input type="checkbox" id="interferometry" disabled>
#     <label for="interferometry">Interferometry</label><br>
#     <input type="checkbox" id="ndwi" disabled>
#     <label for="ndwi">NDWI index</label><br>
#     <input type="checkbox" id="hillshade" disabled>
#     <label for="hillshade">HillShade</label>
#   </form>
#   <div style="font-size:0.95em;color:#888;margin-top:0.7em;">(Placeholder: interaktywność wkrótce)</div>
# </div>
# """, unsafe_allow_html=True)

# ...existing code...

# ---------- Footer ----------
st.markdown(f"""
<a id="contact"></a>
<style>
.custom-footer {{
  width: 100vw;
  background: {PALETTE["purple"]};
  color: white;
  padding: 2.5rem 0 2rem 0;
  margin: 0;
  text-align: center;
  font-size: 1.08rem;
  font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
  position: relative;
  left: 50%;
  right: 50%;
  margin-left: -50vw;
  margin-right: -50vw;
}}
.custom-footer a {{
  color: {PALETTE["orange"]};
  text-decoration: underline;
  word-break: break-all;
}}
.custom-footer .team-title {{
  font-weight: 600;
  margin-top: 1.5rem;
  margin-bottom: 0.5rem;
  font-size: 1.1rem;
  letter-spacing: 1px;
}}
.custom-footer .team-list {{
  margin: 0.5rem 0 0 0;
  padding: 0;
  list-style: none;
  font-size: 1rem;
}}
</style>
<div class="custom-footer">
  <div>
    We are a team that mostly originated from AGH University.<br>
    We have met on the Arctic Winter School 2025.<br>
    And we are excited to work together!
  </div>
  <div style="margin:1.2rem 0 0.5rem 0;">
    <a href="https://www.spaceappschallenge.org/2025/find-a-team/itb/" target="_blank">
      https://www.spaceappschallenge.org/2025/find-a-team/itb/
    </a>
  </div>
  <div style="margin:0.5rem 0 0.5rem 0;">
    <b>Network URL:</b>
    <a href="http://10.200.8.205:8502" target="_blank">
      http://10.200.8.205:8502
    </a>
  </div>
  <div class="team-title">TEAM MEMBERS</div>
  <ul class="team-list">
    <li>Natalia Kowalczyk</li>
    <li>Karolina Kucharz</li>
    <li>Gabriela Nicole Acosta Rivas</li>
    <li>Aleksander Kopyto</li>
    <li>Tomasz Dąbrowa</li>
    <li>Magdalena Nowak</li>
  </ul>
</div>
""", unsafe_allow_html=True)