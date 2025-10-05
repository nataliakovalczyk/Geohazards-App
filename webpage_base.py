# Olkusz Mining Data Web App
# ------------------------------------------
# This Streamlit app presents an interactive map of the Olkusz region,
# focused on visualizing geohazards and mining-related environmental changes.
#
# Features:
# - Custom color palette and branding (top bar, logo, background)
# - Multiple map base layers (OpenStreetMap, CartoDB, Stamen Terrain)
# - Custom markers for key sites with informative popups
# - Responsive, styled UI sections: Home, Overview, Capabilities, Contact
# - Placeholder for future interactive map layer controls
# - Fixed top navigation bar and custom footer with team info and links
# - All assets (icons, images) loaded as base64 for compatibility
#
# Developed for NASA Space Apps Hackathon by team ITB.

import base64
import streamlit as st
import folium
from folium.features import CustomIcon
from streamlit_folium import st_folium

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

# ---------- Map (Olkusz) ----------
st.markdown("<div style='height: 80px;'></div><a id='capabilities'></a>", unsafe_allow_html=True)

# Create the map with multiple base layers
m = folium.Map(
    location=[50.2820, 19.5650],
    zoom_start=12,
    tiles=None,
    control_scale=True
)

# Add base layers
folium.TileLayer("OpenStreetMap", name="OpenStreetMap", control=True).add_to(m)
folium.TileLayer("CartoDB positron", name="Carto Light", control=True).add_to(m)
folium.TileLayer(
    "Stamen Terrain",  # Use built-in provider name
    name="Terrain",
    control=True
).add_to(m)

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

# Add layer control (checkboxes for base layers)
folium.LayerControl(collapsed=False).add_to(m)

# Render the map
map_html = st_folium(m, height=600, width=None, returned_objects=[])

# Overlay the layer control window: center right over the map
st.markdown("""
<style>
.map-layer-window {
    position: absolute;
    top: 100%;
    right: 60px;
    transform: translateY(-50%);
    width: 260px;
    background: #fff8f0ee;
    border-radius: 18px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.10);
    padding: 1.5rem 1.2rem 1.2rem 1.2rem;
    z-index: 99999;
    border: 1px solid #f37e26;
}
@media (max-width: 900px) {
    .map-layer-window {
        position: static;
        width: 100%;
        margin: 1rem 0;
        transform: none;
        right: 0;
        top: auto;
    }
}
</style>
<div class="map-layer-window">
  <h4 style="margin-top:0;color:#30172c;">Warstwy mapy</h4>
  <form>
    <input type="checkbox" id="interferometry" disabled>
    <label for="interferometry">Interferometry</label><br>
    <input type="checkbox" id="ndwi" disabled>
    <label for="ndwi">NDWI index</label><br>
    <input type="checkbox" id="hillshade" disabled>
    <label for="hillshade">HillShade</label>
  </form>
  <div style="font-size:0.95em;color:#888;margin-top:0.7em;">(Placeholder: interaktywność wkrótce)</div>
</div>
""", unsafe_allow_html=True)

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