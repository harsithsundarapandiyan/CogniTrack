import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

# --- Page config ---
st.set_page_config(
    page_title="CogniTrack",
    page_icon="🧠",
    layout="centered"
)

# --- Custom CSS for header ---
st.markdown("""
<style>
.stApp { background-color: #f0f8ff; }
.header-container { border-top: 6px solid #001f54; padding-top:10px; padding-bottom:10px; text-align:center; background-color:#001f54; color:white; }
.header-title { font-size:36px; font-weight:bold; }
.header-icon { font-size:36px; margin-right:10px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-container">
    <span class="header-icon">🧠🖱️</span>
    <span class="header-title">CogniTrack – Cognitive Fatigue Tracker</span>
</div>
""", unsafe_allow_html=True)

# --- Initialize session state ---
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(
        columns=["PostureAngle","MouseInteraction","MemoryTest","CO2Level","Temperature","Humidity","FatigueScore","Timestamp"]
    )

# --- Factor scoring functions ---
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

# --- Tabs ---
tab1, tab2 = st.tabs(["Manual Input / Upload", "Factor Analysis"])

# --- Tab 1: Manual Input and CSV ---
with tab1:
    st.subheader("Manual Input")
    col1, col2, col3 = st.columns(3)
    posture = col1.number_input("Posture Angle (°)", min_value=0.0, max_value=90.0, value=10.0)
    mouse = col2.number_input("Mouse Interaction Score", min_value=0.0, max_value=100.0, value=80.0)
    memory = col3.number_input("Memory Test Score", min_value=0.0, max_value=100.0, value=90.0)

    col4, col5, col6 = st.columns(3)
    co2 = col4.number_input("CO2 Level (ppm)", min_value=300.0, max_value=5000.0, value=500.0)
    temp = col5.number_input("Temperature (°C)", min_value=15.0, max_value=35.0, value=22.0)
    humidity = col6.number_input("Humidity (%)", min_value=20.0, max_value=80.0, value=50.0)

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
        st.session_state.history = pd.concat([st.session_state.history, pd.DataFrame([manual_row])], ignore_index=True)

        if fatigue_score <= 33:
            st.success(f"🟢 Low Fatigue: {fatigue_score}")
        elif fatigue_score <= 66:
            st.warning(f"🟡 Moderate Fatigue: {fatigue_score}")
        else:
            st.error(f"🔴 High Fatigue: {fatigue_score}")

    st.subheader("Upload CSV Data")
    uploaded_file = st.file_uploader(
        "Upload CSV with columns: PostureAngle,MouseInteraction,MemoryTest,CO2Level,Temperature,Humidity",
        type="csv"
    )
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            required_cols = ["PostureAngle","MouseInteraction","MemoryTest","CO2Level","Temperature","Humidity"]
            if all(col in df.columns for col in required_cols):
                df["FatigueScore"] = df.apply(
                    lambda r: calculate_fatigue(r["PostureAngle"], r["MouseInteraction"], r["MemoryTest"],
                                                r["CO2Level"], r["Temperature"], r["Humidity"]), axis=1
                )
                df["Timestamp"] = datetime.now()
                st.session_state.history = pd.concat([st.session_state.history, df], ignore_index=True)
            else:
                st.warning("CSV missing required columns!")
        except Exception as e:
            st.error(f"Error reading CSV: {e}")

    if not st.session_state.history.empty:
        st.subheader("Fatigue History")
        st.write(st.session_state.history)
        st.subheader("Fatigue Score Over Time")
        st.line_chart(st.session_state.history[["Timestamp","FatigueScore"]].set_index("Timestamp"))

# --- Tab 2: Factor Analysis ---
with tab2:
    st.subheader("Factor Analysis: Contribution to Fatigue Score")
    if len(st.session_state.history) < 2:
        st.info("Add at least 2 rows of data (manual input or CSV) to perform factor analysis.")
    else:
        df_factors = st.session_state.history.copy()
        X = df_factors[["PostureAngle","MouseInteraction","MemoryTest","CO2Level","Temperature","Humidity"]]
        y = df_factors["FatigueScore"]

        model = LinearRegression()
        model.fit(X, y)
        coeffs = pd.Series(model.coef_, index=X.columns).sort_values(key=abs, ascending=False)

        st.bar_chart(coeffs)
        st.write("Regression Coefficients (sorted by magnitude):")
        st.write(coeffs)
