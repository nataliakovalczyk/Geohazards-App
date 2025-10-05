# Geohazards-App

**Project for NASA Space Apps Hackathon**

---

## Overview

**Geohazards-App** is an interactive web application designed to visualize and analyze geohazards and environmental changes in the Olkusz region (Poland) using satellite data. The app leverages radar (InSAR) and optical imagery to monitor the effects of mining activities, groundwater changes, and related risks. It provides an intuitive interface for exploring static and temporal raster layers, adjusting visualization parameters, and learning about the context and team behind the project.

---

## Features

- **Interactive Map**: Explore the Olkusz region with multiple base layers (OpenStreetMap, CartoDB, Stamen Terrain).
- **Raster Overlays**: Visualize NDWI, BSM, and other geospatial indicators as overlays.
- **Temporal Analysis**: Load and compare raster data from different dates to observe changes over time.
- **Custom Layer Controls**: Adjust hue, saturation, and transparency for each raster layer using intuitive sliders.
- **Markers & Info Popups**: Key sites and geohazard locations are marked with informative popups.
- **Alpha Gradient & Colorization**: Advanced rendering options for better visual distinction of layers.
- **Caching**: Efficient raster caching for fast and responsive user experience.
- **Team & Project Info**: Learn about the team and the context of the project directly in the app.

---

## Directory Structure

```
Repo/Geohazards-App/
├── webpage_base.py
├── working_layers.py
├── webpage_sliders.py
├── logo.png
├── icon.png
├── background.png
├── home.png
├── alt/
│   ├── ndwi_diff.tif
│   ├── ndwi_before.tif
│   ├── ndwi_after.tif
│   ├── bsm_after.tif
│   ├── bsm_before.tif
│   ├── bsm_diff.tif
│   └── ... (other raster and PNG files)
└── README.md
```

---

## Getting Started

1. **Clone the repository**  
   ```bash
   git clone https://github.com/yourusername/Geohazards-App.git
   cd Geohazards-App
   ```

2. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```
   *(If `requirements.txt` is missing, install: `streamlit folium streamlit-folium rasterio numpy Pillow`)*

3. **Prepare data**  
   Place your raster files (GeoTIFF, PNG, etc.) in the `data/` directory or update the paths in the scripts accordingly.

4. **Run the app**  
   ```bash
   streamlit run webpage_base.py
   ```
   or any other main script, e.g. `working_layers.py`, `webpage_sliders.py`.

5. **Access the app**  
   Open your browser and go to the local or network URL provided by Streamlit (e.g., `http://localhost:8501`).

---

## Team

- Natalia Kowalczyk
- Karolina Kucharz
- Gabriela Nicole Acosta Rivas
- Aleksander Kopyto
- Tomasz Dąbrowa

---

## Acknowledgements

- NASA Space Apps Challenge
- AGH University of Science and Technology
- OpenStreetMap, CartoDB, Stamen Design

---

## License

This project is for educational and hackathon purposes.

---