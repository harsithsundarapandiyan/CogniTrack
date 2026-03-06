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

st.markdown(
"""
<div style="background-color:#001f4d;color:white;padding:20px;text-align:center;border-radius:8px;">
<h1>🧠 CogniTrack – Cognitive Fatigue Tracker</h1>
</div>
""",
unsafe_allow_html=True
)

# --- Initialize history ---
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(
        columns=["PostureAngle","MouseInteraction","MemoryTest","CO2Level",
                 "Temperature","Humidity","FatigueScore","Timestamp"]
    )

# ----------------------------
# Functions
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
# Manual Inputs
# ----------------------------
st.subheader("Manual Input")
col1,col2,col3 = st.columns(3)
posture = col1.number_input("Posture Angle (°)",0.0,90.0,40.0)
mouse = col2.number_input("Mouse Interaction Score",0.0,100.0,20.0)
memory = col3.number_input("Memory Test Score",0.0,100.0,90.0)

col4,col5,col6 = st.columns(3)
co2 = col4.number_input("CO₂ Level (ppm)",300.0,5000.0,500.0)
temp = col5.number_input("Temperature (°C)",15.0,35.0,22.0)
humidity = col6.number_input("Humidity (%)",20.0,80.0,50.0)

# ----------------------------
# Button to calculate fatigue
# ----------------------------
if st.button("Calculate Fatigue Score"):
    fatigue_score = calculate_fatigue(posture, mouse, memory, co2, temp, humidity)
    st.session_state.history = pd.concat([st.session_state.history, pd.DataFrame([{
        "PostureAngle":posture,
        "MouseInteraction":mouse,
        "MemoryTest":memory,
        "CO2Level":co2,
        "Temperature":temp,
        "Humidity":humidity,
        "FatigueScore":fatigue_score,
        "Timestamp":datetime.now()
    }])], ignore_index=True)

    st.write(f"**Latest Fatigue Score: {fatigue_score}**")
    show_fatigue_gauge(fatigue_score)

    # Individual Alerts
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

    # High Fatigue Alert
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
# Example1 Button
# ----------------------------
st.subheader("Load Example Data")
if st.button("Example1 – test_cognitive.txt"):
    df = pd.DataFrame({
        "PostureAngle":[40,55,70,85],
        "MouseInteraction":[60,45,30,20],
        "MemoryTest":[70,60,50,40],
        "CO2Level":[500,800,1200,1500],
        "Temperature":[25,26,27,28],
        "Humidity":[50,55,60,65]
    })
    df["FatigueScore"] = df.apply(
        lambda r: calculate_fatigue(
            r["PostureAngle"],
            r["MouseInteraction"],
            r["MemoryTest"],
            r["CO2Level"],
            r["Temperature"],
            r["Humidity"]
        ), axis=1
    )
    df["Timestamp"] = datetime.now()
    st.session_state.history = pd.concat([st.session_state.history, df], ignore_index=True)
    last_score = df.iloc[-1]["FatigueScore"]
    show_fatigue_gauge(last_score)

# ----------------------------
# Display history
# ----------------------------
if not st.session_state.history.empty:
    st.subheader("Fatigue Score History")
    st.write(st.session_state.history)

    st.subheader("Fatigue Score Over Time")
    st.line_chart(st.session_state.history[["Timestamp","FatigueScore"]].set_index("Timestamp"))
