import streamlit as st
import pandas as pd
from datetime import datetime
import serial
import time

# SERIAL PORT (CHANGE IF NEEDED)
esp = serial.Serial("COM3",115200,timeout=1)
time.sleep(2)

# Page setup
st.set_page_config(
    page_title="CogniTrack",
    page_icon="🧠",
    layout="centered"
)

st.markdown("""
<div style='background-color:#001f4d;padding:20px;border-radius:10px'>
<h1 style='color:white;text-align:center'>🧠 CogniTrack – Cognitive Fatigue Tracker</h1>
</div>
""", unsafe_allow_html=True)

# History
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(
        columns=["PostureAngle","MouseInteraction","MemoryTest","CO2Level","Temperature","Humidity","FatigueScore","Timestamp"]
    )

# Score functions
def factor_score(value, thresholds):

    if value <= thresholds[0]:
        return 0
    elif value <= thresholds[1]:
        return 0.5
    else:
        return 1

def air_quality_score(co2,temp,hum):

    co2_score=min(max((co2-400)/1200,0),1)
    temp_score=min(max(abs(temp-22)/10,0),1)
    hum_score=min(max(abs(hum-50)/50,0),1)

    aq=(co2_score+temp_score+hum_score)/3

    if aq<=0.2:
        return 0
    elif aq<=0.3:
        return 0.5
    else:
        return 1

def calculate_fatigue(posture,mouse,memory,co2,temp,hum):

    p=factor_score(posture,[20,40])
    m=factor_score(100-mouse,[30,60])
    mem=factor_score(100-memory,[20,40])
    aq=air_quality_score(co2,temp,hum)

    total=(p+m+mem+aq)/4*100

    return round(total,2)

# Inputs
st.subheader("Manual Input")

col1,col2,col3=st.columns(3)

posture=col1.number_input("Posture Angle",0.0,90.0,10.0)
mouse=col2.number_input("Mouse Interaction",0.0,100.0,80.0)
memory=col3.number_input("Memory Score",0.0,100.0,90.0)

col4,col5,col6=st.columns(3)

co2=col4.number_input("CO2 ppm",300.0,5000.0,500.0)
temp=col5.number_input("Temperature",15.0,35.0,22.0)
humidity=col6.number_input("Humidity",20.0,80.0,50.0)

if st.button("Calculate Fatigue Score"):

    fatigue_score=calculate_fatigue(posture,mouse,memory,co2,temp,humidity)

    new_row={
        "PostureAngle":posture,
        "MouseInteraction":mouse,
        "MemoryTest":memory,
        "CO2Level":co2,
        "Temperature":temp,
        "Humidity":humidity,
        "FatigueScore":fatigue_score,
        "Timestamp":datetime.now()
    }

    st.session_state.history=pd.concat(
        [st.session_state.history,pd.DataFrame([new_row])],
        ignore_index=True
    )

    if fatigue_score<=33:

        st.success(f"🟢 Low Fatigue: {fatigue_score}")

    elif fatigue_score<=66:

        st.warning(f"🟡 Moderate Fatigue: {fatigue_score}")

    else:

        st.error(f"🔴 High Fatigue: {fatigue_score}")

        # SEND SIGNAL TO ESP32
        try:
            esp.write(b"alert\n")
            st.warning("🚨 ESP32 ALERT TRIGGERED")

        except:
            st.warning("ESP32 not connected")

# History display
if not st.session_state.history.empty:

    st.subheader("Fatigue History")

    st.write(st.session_state.history)

    st.subheader("Fatigue Score Over Time")

    st.line_chart(
        st.session_state.history[["Timestamp","FatigueScore"]].set_index("Timestamp")
    )
