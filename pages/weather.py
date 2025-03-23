import smtplib
from email.mime.text import MIMEText
import streamlit as st
# 🌍 Imports
import vertexai
import os
import uuid
from google.cloud import storage
from vertexai.generative_models import (
    GenerationConfig,
    GenerativeModel,
)
import streamlit as st
from streamlit.commands.page_config import Layout

if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.error("🔒 You must log in to access this page.")
    st.stop()
# === Project Configuration ===
PROJECT_ID = "tidal-hack25tex-230"
REGION = "us-central1"
BUCKET_NAME = "exported_model_9"  # Replace with your Cloud Storage bucket

# === Initialize Vertex AI ===
vertexai.init(project=PROJECT_ID, location=REGION)

# === Set up Gemini model ===
model = GenerativeModel("gemini-1.5-flash-002")
def save_text_report_to_gcs_and_email(report_text, recipient_email):
    try:
        # Unique file name
        unique_filename = f"weather_report_{uuid.uuid4().hex[:8]}.txt"

        # Save file locally
        with open(unique_filename, "w") as f:
            f.write(report_text)

        # Upload to GCS
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(unique_filename)
        blob.upload_from_filename(unique_filename)
        st.info(f"✅ Weather report saved to GCS: {BUCKET_NAME}/{unique_filename}")

        # ==== Email the report ====
        # Create MIME email
        msg = MIMEText(report_text)
        msg['Subject'] = "📩 Your AI Weather Report"
        msg['From'] = "your mail"  # Use your name/email
        msg['To'] = recipient_email

        # SMTP credentials (use Gmail App Password)
        sender_email = "your mail"
        sender_password = " your code"  # Gmail app password

        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
            st.success(f"📧 Weather report emailed to {recipient_email}")

    except Exception as e:
        st.warning(f"❌ Failed to upload or send email: {e}")
def get_weather_news_from_gemini(location: str):
    try:
        prompt = f"Give me a general weather news report for {location} like a TV weather reporter."
        response = model.generate_content(
            prompt,
            generation_config=GenerationConfig(temperature=0.7),
        )
        return response.text or "⚠️ Gemini returned no content."
    except Exception as e:
        return f"❌ Error generating weather report: {e}"

# === US States List ===
us_states = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware",
    "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
    "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana",
    "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina",
    "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina",
    "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia",
    "Wisconsin", "Wyoming"
]

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
st.markdown("<div class='main-title'>🌦️ AI Weather News Reporter</div>", unsafe_allow_html=True)
st.markdown("<div class='subtext'>Get realistic weather updates with Gemini + Google Cloud ✨</div>", unsafe_allow_html=True)

# === UI ===
st.markdown("### 📍 Select a US State")
location = st.selectbox("", us_states, index=4)


if st.button("📝 Generate Weather Report"):
    with st.spinner("🧠 Gemini is thinking..."):
        try:
            report = get_weather_news_from_gemini(location)
            st.markdown("### 📰 Your Weather Report")
            st.markdown(f"<div class='report-box'>{report}</div>", unsafe_allow_html=True)

            # Send to the logged-in user
            recipient_email = st.session_state.get("user_email", "sender mail")
            save_text_report_to_gcs_and_email(report, recipient_email)

        except Exception as e:
            st.error(f"❌ Failed to generate report: {e}")
