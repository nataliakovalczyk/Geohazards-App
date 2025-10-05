# Temporal GeoTIFF Viewer — per-layer hue & opacity, alpha gradient, caching
import io, os, base64, re
from pathlib import Path
from datetime import datetime, date

import numpy as np
from PIL import Image
import streamlit as st
import folium
from streamlit_folium import st_folium
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.coords import BoundingBox

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

# ---------- Page ----------
st.set_page_config(page_title="Temporal GeoTIFF Viewer", layout="wide")
st.title("🗺️ Temporal GeoTIFF Viewer")

st.markdown("<div style='height: 80px;'></div><a id='capabilities'></a>", unsafe_allow_html=True)
icon_src = "/Users/nataliakowalczyk/PycharmProjects/Hackathon/marker_icon.png"
if os.path.exists(icon_src):
    custom_icon = CustomIcon(
        icon_image=icon_src,
        icon_size=(28, 36),
        icon_anchor=(14, 36),
    )
else:
    custom_icon = None

# ---------- Parameters ----------
forced_lat = 50.2820
forced_lon = 19.5650
forced_zoom = 12
assumed_crs = "EPSG:2180"
folder = Path("alt")


# ---------- Sidebar (global) ----------
with st.sidebar:
    st.subheader("Display options")
    SHOW_TOASTS = st.checkbox("Notify on load (toasts)", value=True)
    ADD_INFO_MARKERS = st.checkbox("Add info markers on overlays", value=False)

    st.subheader("Rendering base")
    RAW_GRAY = st.checkbox("Raw grayscale (min→max)", value=False,
                           help="Wyłączone: auto-kontrast 2–98 percentyl.")
    SAT = st.slider("Saturation (for colorize)", 0.0, 1.0, 0.9, 0.01)

    st.subheader("Alpha gradient shape")
    A = st.slider("A (black→color end)", 0.05, 0.45, 0.33, 0.01)
    C = st.slider("C (transparent center)", 0.55, 0.95, 0.66, 0.01,
                  help="Alpha=0 w okolicy C; po C wraca do pełnego koloru")

# ---------- Map (Olkusz) ----------
m = folium.Map(
    location=[forced_lat, forced_lon],
    zoom_start=forced_zoom,
    tiles=None,
    control_scale=True
)
folium.TileLayer("OpenStreetMap", name="OpenStreetMap", control=True).add_to(m)
folium.TileLayer("CartoDB positron", name="Carto Light", control=True).add_to(m)

icon_src = "/Users/nataliakowalczyk/PycharmProjects/Hackathon/marker_icon.png"
if os.path.exists(icon_src):
    custom_icon = CustomIcon(
        icon_image=icon_src,
        icon_size=(28, 36),
        icon_anchor=(14, 36),
    )
else:
    custom_icon = None

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
        icon=custom_icon if custom_icon else folium.Icon(color="purple", icon="info-sign")
    ).add_to(m)


# ---------- Helpers (render) ----------
def _stretch_auto(x: np.ndarray) -> np.ndarray:
    x = x.astype(np.float32)
    m = np.isfinite(x)
    if m.any():
        p2, p98 = np.percentile(x[m], [2, 98])
        x = 255.0 * (x - p2) / (p98 - p2 + 1e-9)
    x = np.clip(x, 0, 255).astype(np.uint8)
    return x

def _stretch_raw(x: np.ndarray) -> np.ndarray:
    x = x.astype(np.float32)
    mn, mx = np.nanmin(x), np.nanmax(x)
    x = 255.0 * (x - mn) / (mx - mn + 1e-9)
    return np.clip(x, 0, 255).astype(np.uint8)

def _hsv_from_gray(gray_u8: np.ndarray, hue_deg: float, sat: float) -> np.ndarray:
    v = gray_u8.astype(np.float32) / 255.0
    s = np.float32(sat)
    h = (np.float32(hue_deg) % 360.0) / 60.0
    c = v * s
    x = c * (1.0 - np.abs((h % 2.0) - 1.0))
    m = v - c

    r_ = np.zeros_like(v, dtype=np.float32)
    g_ = np.zeros_like(v, dtype=np.float32)
    b_ = np.zeros_like(v, dtype=np.float32)

    hi = int(np.floor(h))
    if   hi == 0: r_, g_, b_ = c, x, 0.0
    elif hi == 1: r_, g_, b_ = x, c, 0.0
    elif hi == 2: r_, g_, b_ = 0.0, c, x
    elif hi == 3: r_, g_, b_ = 0.0, x, c
    elif hi == 4: r_, g_, b_ = x, 0.0, c
    else:         r_, g_, b_ = c, 0.0, x

    r = (r_ + m) * 255.0
    g = (g_ + m) * 255.0
    b = (b_ + m) * 255.0
    return np.dstack([r, g, b]).clip(0, 255).astype(np.uint8)

def _alpha_gradient_from_gray(gray_u8: np.ndarray, a: float, c: float) -> np.ndarray:
    """
    Piecewise alpha (0..255) over normalized value v in [0..1]:
      [0 .. a]:    alpha ramps 0 -> 1
      [a .. c]:    alpha ramps 1 -> 0   (transparent dip)
      [c .. 1]:    alpha ramps 0 -> 1
    """
    v = gray_u8.astype(np.float32) / 255.0
    alpha = np.zeros_like(v, dtype=np.float32)

    # segment 1: 0..a
    m1 = v <= a
    alpha[m1] = v[m1] / max(a, 1e-6)

    # segment 2: a..c
    m2 = (v > a) & (v <= c)
    alpha[m2] = 1.0 - (v[m2] - a) / max(c - a, 1e-6)

    # segment 3: c..1
    m3 = v > c
    alpha[m3] = (v[m3] - c) / max(1.0 - c, 1e-6)

    return (alpha.clip(0, 1) * 255.0).astype(np.uint8)

def render_rgba_png(data: np.ndarray, raw_gray: bool,
                    hue_deg: float, sat: float,
                    a_pt: float, c_pt: float) -> bytes:
    """Z 1. pasma robimy kolor (#hue/#sat) + alfa-gradient; PNG RGBA."""
    g = data[0]
    gray_u8 = _stretch_raw(g) if raw_gray else _stretch_auto(g)
    rgb = _hsv_from_gray(gray_u8, hue_deg, sat)  # (H,W,3)
    alpha = _alpha_gradient_from_gray(gray_u8, a_pt, c_pt)  # (H,W)
    rgba = np.dstack([rgb, alpha])  # (H,W,4) uint8
    buf = io.BytesIO()
    Image.fromarray(rgba, mode="RGBA").save(buf, format="PNG", optimize=True)
    return buf.getvalue()

def open_any_to_wgs84(ds, assumed_crs_str: str | None):
    src_crs = ds.crs
    if (src_crs is None) and assumed_crs_str and assumed_crs_str.strip():
        src_crs = assumed_crs_str.strip()

    if (src_crs is None) or (str(src_crs).upper() in ("EPSG:4326", "WGS84", "OGC:CRS84")):
        data = ds.read()
        b = ds.bounds
        return data, [[b.bottom, b.left], [b.top, b.right]], str(src_crs)

    dst_crs = "EPSG:4326"
    transform, width, height = calculate_default_transform(
        src_crs, dst_crs, ds.width, ds.height, *ds.bounds
    )
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
    bb = BoundingBox(min(left, right), min(bottom, top), max(left, right), max(bottom, top))
    return data, [[bb.bottom, bb.left], [bb.top, bb.right]], str(src_crs)

def bounds_are_valid(b):
    try:
        s, w = b[0]; n, e = b[1]
        if not all(np.isfinite([s, w, n, e])): return False
        if not (-90 <= s <= 90 and -90 <= n <= 90 and -180 <= w <= 180 and -180 <= e <= 180): return False
        if not (n > s and e > w): return False
        return True
    except Exception:
        return False

def center_of_bounds(bounds):
    (s, w), (n, e) = bounds
    return ((s+n)/2.0, (w+e)/2.0)

# ---------- Cache (PNG + bounds), zależny od render-paramów ----------
@st.cache_data(show_spinner=False)
def cached_png_bounds(path: str, mtime: float, assumed_crs: str,
                      raw_gray: bool, hue_deg: float, sat: float,
                      a_pt: float, c_pt: float):
    with rasterio.open(path) as ds:
        data, bounds, _ = open_any_to_wgs84(ds, assumed_crs)
    png = render_rgba_png(data, raw_gray, hue_deg, sat, a_pt, c_pt)
    data_uri = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
    return {"data_uri": data_uri, "bounds": bounds}

with st.sidebar:
    if st.button("Clear raster cache"):
        st.cache_data.clear()
        st.success("Raster cache cleared.")

# ---------- Discover rasters ----------
temporal_pat = re.compile(r"^(?P<prefix>.+)_(?P<date>\d{8})\.(?:tif|tiff)$", re.IGNORECASE)
temporal_series: dict[str, dict[date, str]] = {}
static_rasters: list[dict] = []

if folder.exists():
    rasters = []
    for ext in ("*.tif", "*.tiff", "*.TIF", "*.TIFF"):
        rasters.extend(folder.glob(ext))
    for p in rasters:
        m = temporal_pat.match(p.name)
        if m:
            series = m.group("prefix").lower()
            d = datetime.strptime(m.group("date"), "%Y%m%d").date()
            temporal_series.setdefault(series, {})[d] = p.as_posix()
        else:
            static_rasters.append({"name": p.stem, "path": p.as_posix()})

if not temporal_series and not static_rasters:
    st.error(f"No .tif/.tiff files in '{folder}'.")
    st.stop()

# ---------- UI state for per-layer controls ----------
if "enabled_static" not in st.session_state:
    st.session_state.enabled_static = []

if "static_layer_params" not in st.session_state:
    st.session_state.static_layer_params = {}  # name -> {"hue":..., "opacity":...}

if "temporal_params" not in st.session_state:
    st.session_state.temporal_params = {"hue": None, "opacity": None}

# Prepare static names/lookup
static_names = [it["name"] for it in static_rasters]
name_to_path = {it["name"]: it["path"] for it in static_rasters}

# ---------- Small popover to choose static layers ----------
col = st.columns(1)[0]
with col:
    if static_names:
        with st.popover("➕ Add static layers"):
            chosen = st.multiselect(
                "Choose static rasters to load",
                options=static_names,
                default=st.session_state.enabled_static,
            )
            st.session_state.enabled_static = chosen

enabled_static = st.session_state.enabled_static

# ---------- Build map ----------
m = folium.Map(location=[forced_lat, forced_lon], zoom_start=forced_zoom, tiles=None)
folium.TileLayer("OpenStreetMap", name="OpenStreetMap", attr='© OpenStreetMap contributors').add_to(m)
folium.TileLayer("CartoDB positron", name="Carto Light", attr='© CartoDB').add_to(m)

# ---------- Determine defaults per-layer (hue/opacity) ----------
def ensure_defaults_for_layers(static_enabled_names, has_temporal: bool):
    # ile warstw aktywnych w sumie (statyczne + temporalna)
    total = len(static_enabled_names) + (1 if has_temporal else 0)
    if total <= 0:
        return

    # rozkład hue i opacity wg reguły: hue = 360/N * m; opacity = 1/N
    hue_step = 360.0 / total
    default_opacity = 1.0 / total

    # statics: m = 1..len
    for idx, nm in enumerate(static_enabled_names, start=1):
        params = st.session_state.static_layer_params.get(nm, {})
        if "hue" not in params or params["hue"] is None:
            params["hue"] = hue_step * idx
        if "opacity" not in params or params["opacity"] is None:
            params["opacity"] = default_opacity
        st.session_state.static_layer_params[nm] = params

    # temporal: m = total (ostatnia warstwa)
    if has_temporal:
        tparams = st.session_state.temporal_params
        if tparams.get("hue") is None:
            tparams["hue"] = hue_step * total
        if tparams.get("opacity") is None:
            tparams["opacity"] = default_opacity
        st.session_state.temporal_params = tparams

# Call once to ensure defaults exist
ensure_defaults_for_layers(enabled_static, has_temporal=bool(temporal_series))

# ---------- Per-layer controls UI ----------
if enabled_static:
    st.markdown("#### Static layer styles")
    for nm in enabled_static:
        p = st.session_state.static_layer_params.get(nm, {"hue": 180.0, "opacity": 0.5})
        col1, col2, col3 = st.columns([2, 3, 3])
        with col1:
            st.caption(f"**{nm}**")
        with col2:
            p["hue"] = st.slider(f"Hue · {nm}", 0, 360, int(p["hue"]), key=f"hue_{nm}")
        with col3:
            p["opacity"] = st.slider(f"Opacity · {nm}", 0.0, 1.0, float(p["opacity"]), 0.01, key=f"op_{nm}")
        st.session_state.static_layer_params[nm] = p

# ---------- Add selected static overlays ----------
static_bounds = []
for nm in enabled_static:
    path = name_to_path.get(nm)
    if not path:
        continue
    try:
        if os.path.exists(path):
            p = st.session_state.static_layer_params.get(nm, {"hue": 180.0, "opacity": 0.5})
            mtime = os.path.getmtime(path)
            payload = cached_png_bounds(
                path, mtime, assumed_crs,
                RAW_GRAY, float(p["hue"]), float(SAT),
                float(A), float(C)
            )
            folium.raster_layers.ImageOverlay(
                image=payload["data_uri"],
                bounds=payload["bounds"],
                opacity=float(p["opacity"]),  # per-layer opacity
                name=f"Static · {nm}",
                interactive=True
            ).add_to(m)

            if ADD_INFO_MARKERS and bounds_are_valid(payload["bounds"]):
                c_lat, c_lon = center_of_bounds(payload["bounds"])
                folium.Marker(
                    [c_lat, c_lon],
                    tooltip=f"Static · {nm}",
                    popup=folium.Popup(f"<b>Static</b><br>{nm}", max_width=260),
                    icon=folium.Icon(color="green", icon="info-sign")
                ).add_to(m)

            if SHOW_TOASTS:
                st.toast(f"Loaded static: {nm}", icon="✅")

            static_bounds.append(payload["bounds"])
    except Exception as e:
        st.error(f"Static load error '{path}': {e}")

# ---------- Temporal overlay ----------
if temporal_series:
    all_series = sorted(temporal_series.keys())
    default_series = st.session_state.get("series", all_series[0])
    dates_for_default = sorted(temporal_series[default_series].keys())
    default_date = st.session_state.get("date", max(dates_for_default))
    if default_date not in dates_for_default:
        default_date = max(dates_for_default)

    sel_path = temporal_series[default_series][default_date]

    # UI for temporal parameters (hue/opacity)
    st.markdown("---")
    c1, c2 = st.columns([1, 3])
    with c1:
        series = st.selectbox(
            "Series (prefix before last underscore):",
            options=all_series,
            index=all_series.index(st.session_state.get("series", all_series[0])),
            key="series"
        )
    with c2:
        dates_options = sorted(temporal_series[series].keys())
        st.select_slider(
            "Date",
            options=dates_options,
            value=(st.session_state.get("date") if st.session_state.get("date") in dates_options else max(dates_options)),
            format_func=lambda d: d.isoformat(),
            key="date"
        )
    # read current temporal params (ensure defaults were set earlier)
    tp = st.session_state.temporal_params
    tcol1, tcol2 = st.columns(2)
    with tcol1:
        tp["hue"] = st.slider("Hue · temporal", 0, 360, int(tp.get("hue") or 180), key="hue_temporal")
    with tcol2:
        tp["opacity"] = st.slider("Opacity · temporal", 0.0, 1.0, float(tp.get("opacity") or 0.5), 0.01, key="op_temporal")
    st.session_state.temporal_params = tp

    try:
        if os.path.exists(sel_path):
            mtime = os.path.getmtime(sel_path)
            payload = cached_png_bounds(
                sel_path, mtime, assumed_crs,
                RAW_GRAY, float(tp["hue"]), float(SAT),
                float(A), float(C)
            )

            folium.raster_layers.ImageOverlay(
                image=payload["data_uri"],
                bounds=payload["bounds"],
                opacity=float(tp["opacity"]),
                name=f"{series.upper()} — {st.session_state['date'].isoformat()}",
                interactive=True
            ).add_to(m)

            if ADD_INFO_MARKERS and bounds_are_valid(payload["bounds"]):
                c_lat, c_lon = center_of_bounds(payload["bounds"])
                folium.Marker(
                    [c_lat, c_lon],
                    tooltip=f"{series.upper()} — {st.session_state['date'].isoformat()}",
                    popup=folium.Popup(
                        f"<b>{series.upper()}</b><br>Date: {st.session_state['date'].isoformat()}",
                        max_width=260
                    ),
                    icon=folium.Icon(color="blue", icon="info-sign")
                ).add_to(m)

            if SHOW_TOASTS:
                st.toast(f"Loaded temporal: {series.upper()} — {st.session_state['date'].isoformat()}", icon="🛰️")

            if bounds_are_valid(payload["bounds"]) and not static_bounds:
                m.fit_bounds(payload["bounds"])
    except Exception as e:
        st.error(f"Temporal load error '{sel_path}': {e}")
else:
    if static_bounds:
        m.fit_bounds(static_bounds[0])

# ---------- Render map ----------
folium.LayerControl(collapsed=False).add_to(m)
st_folium(m, height=720, width=None, returned_objects=[])

# --- Notes:
# - PNG jest RGBA (z alfą wg gradientu), a dodatkowo ImageOverlay ma per-layer opacity.
# - Cache zależy od: mtime, RAW_GRAY, hue, SAT, A, C. Zmiana sliderów przebuduje jedynie tę warstwę.
