# ✅ Must be first!
import streamlit as st
from datetime import date
from google.cloud import aiplatform
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value
from app1 import show_header

# === Require Login ===
import streamlit as st

if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.error("🔒 You must log in to access this page.")
    st.stop()
# === Page config ===

show_header()

st.title("📅 Predict Wildfire Risk from Past Data")
st.markdown("Enter past environmental data and predict fire risk using Vertex AI model.")

# === Vertex AI Config ===
PROJECT = "tidal-hack25tex-230"
ENDPOINT_ID = "2910210466141700096"
REGION = "us-central1"

# === Vertex AI Predictor ===
def predict_tabular_classification_sample(instance_dict):
    client_options = {"api_endpoint": f"{REGION}-aiplatform.googleapis.com"}
    client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)

    instance = json_format.ParseDict(instance_dict, Value())
    instances = [instance]
    parameters = json_format.ParseDict({}, Value())
    endpoint = client.endpoint_path(project=PROJECT, location=REGION, endpoint=ENDPOINT_ID)
    response = client.predict(endpoint=endpoint, instances=instances, parameters=parameters)
    predictions = response.predictions
    return predictions[0] if predictions else None

# === Input UI ===
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

selected_date = st.date_input("📅 Date", value=date(2024, 3, 1))
ndvi = st.text_input("🌿 NDVI", value="0.4")
temp = st.text_input("🌡️ Temperature (K)", value="283")
humidity = st.text_input("💧 Humidity (kg/kg)", value="0.005")
wind = st.text_input("🌬️ Wind Speed (m/s)", value="4.49")
elevation = st.text_input("⛰️ Elevation (m)", value="44")

if st.button("🚀 Predict Fire Risk"):
    instance_dict = {
        "date": str(selected_date),
        "NDVI": ndvi,
        "Temperature": temp,
        "Humidity": humidity,
        "WindSpeed": wind,
        "Elevation": elevation
    }

    st.subheader("🔎 Input Preview")
    st.json(instance_dict)

    try:
        prediction = predict_tabular_classification_sample(instance_dict)
        st.subheader("🧠 Prediction Result")

        if prediction == "High":
            st.error("🔥 High Fire Risk Detected!")
        elif prediction == "Medium":
            st.warning("⚠️ Medium Fire Risk")
        elif prediction == "Low":
            st.info("🟡 Low Fire Risk")
        else:
            st.success("✅ No Fire Risk")
    except Exception as e:
        st.error(f"❌ Prediction failed: {e}")

st.markdown("---")
st.markdown("<p style='text-align: center; color: #cbd5e1;'>Built with ❤️ for Tidal TAMU Hackathon · Powered by Google Cloud & Gemini. Sometimes this model may provide inaccurate results.</p>", unsafe_allow_html=True)