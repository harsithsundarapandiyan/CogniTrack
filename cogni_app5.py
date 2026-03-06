import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

# --- Page config ---
st.set_page_config(
    page_title="CogniTrack",
    page_icon="🧠",
    layout="centered"
)

st.title("CogniTrack – Cognitive Fatigue Monitoring Dashboard")

# --- Load example dataset ---
st.subheader("Example Dataset")
st.markdown("[Example1: test_cognitive.txt](test_cognitive.txt)")

# Load CSV
data = pd.read_csv("test_cognitive.txt", sep="\t")

# Normalize columns (remove spaces, lowercase)
data.columns = data.columns.str.strip().str.lower().str.replace(" ", "")

# Show preview
st.subheader("Dataset Preview")
st.write(data.head())

# ----------------------------
# Fatigue calculation functions
# ----------------------------
def normalize(value, min_val, max_val):
    return min(max((value - min_val) / (max_val - min_val), 0), 1)

def posture_score(angle):
    if angle < 20: return 0
    elif angle < 40: return 0.5
    else: return 1

def mouse_score(mouse):
    fatigue = 100 - mouse
    if fatigue < 30: return 0
    elif fatigue < 60: return 0.5
    else: return 1

def memory_score(memory):
    fatigue = 100 - memory
    if fatigue < 20: return 0
    elif fatigue < 40: return 0.5
    else: return 1

def air_quality_score(co2, temp, hum):
    co2_score = normalize(co2, 400, 2000)
    temp_score = normalize(abs(temp-22),0,10)
    hum_score = normalize(abs(hum-50),0,50)
    return (co2_score + temp_score + hum_score)/3

def air_quality_alert(co2):
    if co2 <= 600: return "Good"
    elif co2 <= 1000: return "Moderate"
    elif co2 <= 1500: return "Poor"
    else: return "Very Poor"

def calculate_fatigue(posture, mouse, memory, co2, temp, hum):
    p = posture_score(posture)
    m = mouse_score(mouse)
    mem = memory_score(memory)
    aq = air_quality_score(co2, temp, hum)
    return round((0.30*p + 0.25*m + 0.25*mem + 0.20*aq)*100,2)

# ----------------------------
# Plotly Gauge
# ----------------------------
def show_fatigue_gauge(fatigue_score):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=fatigue_score,
        title={'text': "Fatigue Score (%)"},
        gauge={
            'axis': {'range':[0,100]},
            'bar': {'color':'darkblue'},
            'steps': [
                {'range':[0,33],'color':'green'},
                {'range':[33,66],'color':'yellow'},
                {'range':[66,70],'color':'orange'},
                {'range':[70,100],'color':'red'}
            ],
        }
    ))
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------
# Button to calculate fatigue
# ----------------------------
st.subheader("Calculate Fatigue from Latest Entry")
if st.button("Calculate Fatigue Score"):

    posture = data["postureangle"].iloc[-1]
    mouse = data["mouseinteraction"].iloc[-1]
    memory = data["memorytest"].iloc[-1]
    co2 = data["co2level"].iloc[-1]
    temp = data["temperature"].iloc[-1]
    hum = data["humidity"].iloc[-1]

    fatigue_score = calculate_fatigue(posture, mouse, memory, co2, temp, hum)

    st.write(f"**Latest Fatigue Score: {fatigue_score}**")
    show_fatigue_gauge(fatigue_score)

    # --- Individual Alerts ---
    if posture > 40:
        st.warning("🪑 Posture Alert: Strong slouch detected")
    elif posture > 20:
        st.info("🪑 Posture Alert: Mild slouch detected")

    if mouse < 40:
        st.warning("🖱️ Mouse Interaction Alert: Very slow")
    elif mouse < 70:
        st.info("🖱️ Mouse Interaction Alert: Slightly slow")

    if memory < 60:
        st.warning("🧠 Memory Alert: Performance dropping")
    elif memory < 80:
        st.info("🧠 Memory Alert: Slight drop detected")

    aq_alert = air_quality_alert(co2)
    if aq_alert == "Good":
        st.success("🌿 Air Quality: Good")
    elif aq_alert == "Moderate":
        st.info("🌿 Air Quality: Moderate")
    elif aq_alert == "Poor":
        st.warning("🌿 Air Quality: Poor")
    else:
        st.error("🌿 Air Quality: Very Poor")

    # --- High Fatigue Alert ---
    if fatigue_score > 70:
        st.error(f"🚨 HIGH FATIGUE DETECTED: {fatigue_score} – TAKE A BREAK IMMEDIATELY!!")
        st.markdown(
            """
            <div style="background-color:#ffcccc;padding:20px;border-radius:10px;
            text-align:center;font-size:22px;font-weight:bold;color:#990000;">
            🔥 HIGH FATIGUE DETECTED – TAKE A BREAK IMMEDIATELY!!
            </div>
            """,
            unsafe_allow_html=True
        )

# ----------------------------
# Display history
# ----------------------------
st.subheader("Fatigue Score History")
data["fatigue_score"] = data.apply(
    lambda r: calculate_fatigue(
        r["postureangle"], r["mouseinteraction"], r["memorytest"],
        r["co2level"], r["temperature"], r["humidity"]
    ), axis=1
)
st.line_chart(data["fatigue_score"])
