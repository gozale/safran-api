import io

import requests
import streamlit as st
from PIL import Image

API_URL = "http://localhost:8000"  # Update if deployed

st.set_page_config(page_title="Safran Image Classifier", layout="centered")
st.title("Image Classifier")

# Initialize login state
if "jwt_token" not in st.session_state:
    st.session_state.jwt_token = None

# --- Logout ---
if st.session_state.jwt_token:
    st.sidebar.success("✅ Logged in")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.jwt_token = None
        st.rerun()

# --- Show Login/Register if not logged in ---
if not st.session_state.jwt_token:
    st.header("🔐 Access")
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        email = st.text_input("📧 Email", key="login_email")
        password = st.text_input("🔑 Password", type="password", key="login_pass")

        if st.button("Login"):
            response = requests.post(f"{API_URL}/login", json={"email": email, "password": password})
            if response.status_code == 200:
                st.session_state.jwt_token = response.json()["access_token"]
                st.success("Logged in!")
                st.rerun()
            else:
                st.error(response.json().get("detail", "Login failed"))

    with tab2:
        reg_email = st.text_input("📧 Email", key="reg_email")
        reg_password = st.text_input("🔑 Password", type="password", key="reg_pass")

        if st.button("Register"):
            response = requests.post(f"{API_URL}/register", json={"email": reg_email, "password": reg_password})
            if response.status_code == 201:
                st.success("Registered successfully! Please login.")
            else:
                st.error(response.json().get("detail", "Registration failed"))

# --- Main Features if logged in ---
if st.session_state.jwt_token:
    token = st.session_state.jwt_token
    st.header("📤 Upload & Predict")
    files = st.file_uploader("Upload image(s)", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True)

    if st.button("Predict"):
        if not files:
            st.warning("Upload at least one image.")
        else:
            for file in files:
                response = requests.post(
                    f"{API_URL}/predict",
                    headers={"Authorization": f"Bearer {token}"},
                    files={"file": (file.name, file.getvalue(), file.type)}
                )
                if response.status_code == 200:
                    result = response.json()["result"]
                    st.image(Image.open(file), caption=f"{file.name} → {result}", width=250)
                    st.success(f"`{file.name}` classified as `{result}`")
                else:
                    st.error(f"Error with `{file.name}`: {response.text}")

    st.divider()
    st.header("📜 Prediction History")

    if st.button("🔄 Load My Predictions"):
        response = requests.get(f"{API_URL}/predictions", headers={"Authorization": f"Bearer {token}"})
        if response.status_code == 200:
            predictions = response.json()
            if not predictions:
                st.info("No predictions found.")
            for pred in predictions:
                st.markdown(
                    f"**ID:** {pred['id']} | **File:** {pred['input_data']['filename']} | **Result:** {pred['output_data']['result']}")
                image_url = f"{API_URL}/predictions/{pred['id']}/image"
                img = requests.get(image_url, headers={"Authorization": f"Bearer {token}"})
                if img.status_code == 200:
                    st.image(Image.open(io.BytesIO(img.content)), width=200)
                else:
                    st.warning("🔒 Image not available")
        else:
            st.error("Failed to fetch predictions.")

    st.divider()
    st.header("📊 Prediction Statistics")

    if st.button("📈 View Stats"):
        response = requests.get(f"{API_URL}/stats", headers={"Authorization": f"Bearer {token}"})
        if response.status_code == 200:
            stats = response.json().get("stats", {})

            if not stats:
                st.info("ℹ️ No prediction statistics available yet.")
            else:
                st.subheader("📌 Predictions per Class")
                cols = st.columns(len(stats))  # Create a column per class
                for i, (label, count) in enumerate(stats.items()):
                    cols[i].metric(label.capitalize(), count)
        else:
            st.error("❌ Failed to fetch stats.")
