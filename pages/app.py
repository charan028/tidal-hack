# ✅ Must be first!
import streamlit as st

from app1 import show_header

# === Require Login ===

if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.error("🔒 You must log in to access this page.")
    
    st.stop()
# === Page config ===

show_header()
# 🌍 Imports
import folium
from streamlit_folium import st_folium
import ee
from datetime import datetime, timedelta
from google.cloud import aiplatform
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value
from streamlit.components.v1 import html

# === Initialize Earth Engine ===
try:
    ee.Initialize(project='tidal-hack25tex-230')
except Exception as e:
    st.error(f"❌ Earth Engine init failed: {e}")

# === Vertex AI Config ===
PROJECT_ID = "tidal-hack25tex-230"
REGION = "us-central1"
ENDPOINT_ID = "2910210466141700096"

# === Vertex AI Prediction ===
def predict_tabular_classification(instance_dict):
    client_options = {"api_endpoint": f"{REGION}-aiplatform.googleapis.com"}
    client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)

    instance = json_format.ParseDict(instance_dict, Value())
    instances = [instance]
    parameters = json_format.ParseDict({}, Value())

    endpoint = client.endpoint_path(project=PROJECT_ID, location=REGION, endpoint=ENDPOINT_ID)
    response = client.predict(endpoint=endpoint, instances=instances, parameters=parameters)
    predictions = response.predictions
    return predictions[0] if predictions else None

# === Combined Heat/Cold Map ===
def get_combined_temperature_map():
    bounds = ee.Geometry.Rectangle([-125, 24, -66.5, 49])
    date = ee.Date("2024-03-01")

    image = ee.ImageCollection("NASA/GLDAS/V021/NOAH/G025/T3H") \
        .filterDate(date, date.advance(1, 'hour')) \
        .select('Tair_f_inst') \
        .mean()

    vis_params = {
        'min': 250,
        'max': 320,
        'palette': ['blue', 'cyan', 'green', 'yellow', 'orange', 'red']
    }
    map_id_dict = image.visualize(**vis_params).getMapId()
    tile_url = map_id_dict['tile_fetcher'].url_format

    temp_map = folium.Map(location=[39, -98], zoom_start=4)
    folium.TileLayer(tiles=tile_url, attr='GLDAS Tair', name='Temp Overlay', overlay=True, control=True).add_to(temp_map)
    folium.LayerControl().add_to(temp_map)
    return temp_map

# === Feature Extractor ===
def extract_features(lat, lon, date):
    point = ee.Geometry.Point([lon, lat])
    ndvi_image = ee.ImageCollection("COPERNICUS/S2_SR") \
        .filterBounds(point) \
        .filterDate(date, date.advance(2, 'day')) \
        .map(lambda img: img.normalizedDifference(['B8', 'B4']).rename('NDVI')) \
        .mean()

    ndvi_val = ndvi_image.reduceRegion(ee.Reducer.mean(), point, 30).getInfo().get('NDVI', None)
    climate = ee.ImageCollection("NASA/GLDAS/V021/NOAH/G025/T3H") \
        .filterBounds(point) \
        .filterDate(date, date.advance(1, 'day')) \
        .select(['Tair_f_inst', 'Wind_f_inst', 'Qair_f_inst']) \
        .mean() \
        .reduceRegion(ee.Reducer.mean(), point, 1000) \
        .getInfo()

    elevation = ee.Image("USGS/SRTMGL1_003") \
        .reduceRegion(ee.Reducer.mean(), point, 30) \
        .getInfo().get('elevation', None)

    return {
        'NDVI': ndvi_val,
        'Temperature': climate.get('Tair_f_inst', None),
        'Humidity': climate.get('Qair_f_inst', None),
        'WindSpeed': climate.get('Wind_f_inst', None),
        'Elevation': elevation
    }

# === UI ===
# === Streamlit Custom Theme Styling ===
st.markdown(
    """
    <style>
        body {
            background-image: url('https://images.unsplash.com/photo-1572204097183-e1ab140342ed?q=80&w=2670&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D');
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
            background-position: center;
        }
        .main-title {
            font-size: 42px;
            font-weight: 700;
            text-align: center;
            color: #4ade80;
            margin-bottom: 0.5rem;
        }
        .subtext {
            text-align: center;
            font-size: 18px;
            color: #94a3b8;
            margin-bottom: 2rem;
        }
        .report-box {
            background-color: rgba(30, 41, 59, 0.85);
            padding: 1rem;
            border-radius: 12px;
            color: #f8fafc;
            font-size: 18px;
            line-height: 1.6;
        }
        .stApp {
            padding: 2rem;
            background-color: rgba(0, 0, 0, 0.5);
        }
        @media only screen and (max-width: 768px) {
            .main-title {
                font-size: 28px;
            }
            .report-box {
                font-size: 16px;
            }
        }
    </style>
    """,
    unsafe_allow_html=True
)
st.markdown("""
<h1 style='text-align: center;'>🔥 Wildfire Risk + USA Temperature Map</h1>
<p style='text-align: center;'>Click on a location to predict wildfire risk. View a unified USA temperature map overlaying heat and cold zones.</p>
""", unsafe_allow_html=True)

# 🔥 Combined Temperature Map
st.subheader("🌡️ Combined Temperature Overlay (Heat + Cold)")
try:
    temp_map = get_combined_temperature_map()
    st_folium(temp_map, height=500, width=700)
except Exception as e:
    st.error(f"❌ Failed to load temperature map: {e}")

# 🔥 Wildfire Prediction
st.subheader("🧠 Wildfire Prediction")

m = folium.Map(location=[39, -98], zoom_start=4)
map_data = st_folium(m,height=500, width=700, key="map")

if map_data and map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    st.success(f"📍 Selected Location: ({lat:.2f}, {lon:.2f})")

    if st.button("🚀 Predict Wildfire Risk"):
        with st.spinner("🔄 Fetching and predicting..."):
            try:
                date = ee.Date("2024-03-01")
                features = extract_features(lat, lon, date)
                st.write("📊 Extracted Features:", features)

                if any(v is None for v in features.values()):
                    st.warning("⚠️ Missing data. Try another location.")
                else:
                    input_dict = {
                        "date": "2024-03-01",
                        "NDVI": str(features["NDVI"]),
                        "Temperature": str(features["Temperature"]),
                        "Humidity": str(features["Humidity"]),
                        "WindSpeed": str(features["WindSpeed"]),
                        "Elevation": str(features["Elevation"])
                    }
                    prediction = predict_tabular_classification(input_dict)

                    st.subheader("📍 Prediction Result")
                    if prediction == "High":
                        st.error("🔥 High Fire Risk Detected!")
                    elif prediction == "Medium":
                        st.warning("⚠️ Medium Fire Risk")
                    elif prediction == "Low":
                        st.info("🔵 Low Fire Risk")
                    else:
                        st.success("✅ No Fire Risk")

            except Exception as e:
                st.error(f"❌ Prediction error: {e}")
else:
    st.info("🗺 Click on the map above to start wildfire prediction.")

st.markdown("---")
st.markdown("<p style='text-align: center; color: #cbd5e1;'>Built with ❤️ for Tidal TAMU Hackathon · Powered by Google Cloud & Gemini Sometimes this model may provide innacurate results</p>", unsafe_allow_html=True)
