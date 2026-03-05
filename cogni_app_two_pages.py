import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import cv2
import requests

# ESP32 IP ADDRESS
ESP32_IP = "http://192.168.1.90/blink"

# --- Page config ---
st.set_page_config(
    page_title="CogniTrack",
    page_icon="🧠",
    layout="centered"
)

# --- Sidebar page selector ---
page = st.sidebar.selectbox("Select Page", ["Manual / CSV Input", "Real-Time Webcam"])

# --- Initialize session state ---
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(
        columns=["PostureAngle","MouseInteraction","MemoryTest","CO2Level","Temperature","Humidity","FatigueScore","Timestamp"]
    )

# --- Custom CSS ---
st.markdown(
    """
    <style>
    .stApp { background-color: #f0f8ff; }
    .header-container { border-top: 6px solid #4B0082; padding-top:10px; padding-bottom:10px; text-align:center; }
    .header-title { font-size:36px; color:#4B0082; font-weight:bold; }
    .brain-icon { font-size:36px; margin-right:10px; }
    </style>
    """, unsafe_allow_html=True
)

st.markdown(
    """
    <div class="header-container">
        <span class="brain-icon">🧠</span>
        <span class="header-title">CogniTrack – Cognitive Fatigue Tracker</span>
    </div>
    """, unsafe_allow_html=True
)

# --- Fatigue calculation ---
def factor_score(value, thresholds):
    if value <= thresholds[0]:
        return 0
    elif value <= thresholds[1]:
        return 0.5
    else:
        return 1

def air_quality_score(co2, temp, hum):
    co2_score = min(max((co2-400)/1200,0),1)
    temp_score = min(max(abs(temp-22)/10,0),1)
    hum_score = min(max(abs(hum-50)/50,0),1)
    aq_index = (co2_score + temp_score + hum_score)/3

    if aq_index <= 0.2:
        return 0
    elif aq_index <= 0.3:
        return 0.5
    else:
        return 1

def calculate_fatigue(posture, mouse, memory, co2, temp, hum):
    p = factor_score(posture, [20, 40])
    m = factor_score(100 - mouse, [30, 60])
    mem = factor_score(100 - memory, [20, 40])
    aq = air_quality_score(co2, temp, hum)

    total = (p + m + mem + aq)/4 * 100
    return round(total,2)

# --- Send signal to ESP32 ---
def trigger_esp32():
    try:
        requests.get(ESP32_IP)
        st.success("Signal sent to ESP32 🔵")
    except:
        st.error("ESP32 not reachable")

# --- PAGE 1 ---
if page == "Manual / CSV Input":

    st.subheader("Manual Input")

    col1, col2, col3 = st.columns(3)

    posture = col1.number_input("Posture Angle (°)", 0.0, 90.0, 10.0)
    mouse = col2.number_input("Mouse Interaction Score", 0.0, 100.0, 80.0)
    memory = col3.number_input("Memory Test Score", 0.0, 100.0, 90.0)

    col4, col5, col6 = st.columns(3)

    co2 = col4.number_input("CO2 Level (ppm)", 300.0, 5000.0, 500.0)
    temp = col5.number_input("Temperature (°C)", 15.0, 35.0, 22.0)
    humidity = col6.number_input("Humidity (%)", 20.0, 80.0, 50.0)

    if st.button("Calculate Fatigue Score"):

        fatigue_score = calculate_fatigue(posture, mouse, memory, co2, temp, humidity)

        manual_row = {
            "PostureAngle": posture,
            "MouseInteraction": mouse,
            "MemoryTest": memory,
            "CO2Level": co2,
            "Temperature": temp,
            "Humidity": humidity,
            "FatigueScore": fatigue_score,
            "Timestamp": datetime.now()
        }

        st.session_state.history = pd.concat(
            [st.session_state.history, pd.DataFrame([manual_row])],
            ignore_index=True
        )

        # --- Display level ---
        if fatigue_score <= 33:
            st.success(f"🟢 Low Fatigue: {fatigue_score}")

        elif fatigue_score <= 66:
            st.warning(f"🟡 Moderate Fatigue: {fatigue_score}")

        else:
            st.error(f"🔴 High Fatigue: {fatigue_score}")

        # --- ESP32 TRIGGER ---
        if fatigue_score > 70:
            st.warning("⚠️ Fatigue above 70 → Triggering ESP32 LED")
            trigger_esp32()

    # --- Display history ---
    if not st.session_state.history.empty:

        st.subheader("Fatigue History")
        st.write(st.session_state.history)

        st.subheader("Fatigue Score Over Time")
        st.line_chart(
            st.session_state.history[["Timestamp","FatigueScore"]]
            .set_index("Timestamp")
        )

# --- PAGE 2 ---
if page == "Real-Time Webcam":

    st.subheader("Real-Time Webcam Feed")

    run = st.checkbox("Start Webcam")
    frame_placeholder = st.empty()

    if run:
        cap = cv2.VideoCapture(0)

        while run:

            ret, frame = cap.read()

            if not ret:
                st.error("Failed to access webcam")
                break

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_placeholder.image(frame, channels="RGB")

        cap.release()
