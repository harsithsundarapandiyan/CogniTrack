import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.title("CogniTrack – Cognitive Fatigue Monitoring Dashboard")

st.write("Example dataset:")
st.markdown("[Example1: test_cognitive.txt](test_cognitive.txt)")

# Load example dataset automatically
data = pd.read_csv("test_cognitive.txt", sep="\t")

# Normalize column names (remove spaces, lowercase)
data.columns = data.columns.str.strip().str.replace(" ", "").str.lower()

st.subheader("Dataset Preview")
st.write(data.head())

# Extract variables
posture = data["postureangle"]
mouse = data["mouseinteraction"]
memory = data["memorytest"]
co2 = data["co2level"]

# Normalize values
posture_norm = (posture - posture.min()) / (posture.max() - posture.min())
mouse_norm = 1 - (mouse - mouse.min()) / (mouse.max() - mouse.min())  # assume higher mouse = better
memory_norm = 1 - (memory - memory.min()) / (memory.max() - memory.min())  # higher memory = better
co2_norm = (co2 - co2.min()) / (co2.max() - co2.min())

# Linear combination fatigue score (equal weights)
fatigue_score = (
    0.25 * posture_norm +
    0.25 * mouse_norm +
    0.25 * memory_norm +
    0.25 * co2_norm
)

data["fatigue_score"] = fatigue_score

st.subheader("Fatigue Score Over Time")
st.line_chart(data["fatigue_score"])

# CO2 Alert System (Harvard ranges)
st.subheader("CO₂ Air Quality Alert")
latest_co2 = co2.iloc[-1]
st.write(f"Current CO₂ Level: **{latest_co2} ppm**")

if latest_co2 <= 600:
    st.success("Air quality is good.")
elif latest_co2 <= 1000:
    st.warning("CO₂ slightly elevated. Monitor ventilation.")
elif latest_co2 <= 1500:
    st.warning("CO₂ high. Check CO₂ levels and improve ventilation.")
else:
    st.error("CO₂ very high. Immediate ventilation recommended.")

# Plot Posture Angle
st.subheader("Posture Angle Over Time")
plt.figure()
plt.plot(posture)
plt.xlabel("Time")
plt.ylabel("Posture Angle")
plt.title("Spine Posture Angle Changes")
st.pyplot(plt)

# Plot Mouse Interaction
st.subheader("Mouse Interaction Over Time")
plt.figure()
plt.plot(mouse)
plt.xlabel("Time")
plt.ylabel("Mouse Interaction Score")
plt.title("Mouse Interaction Variation")
st.pyplot(plt)

# Plot Memory Score
st.subheader("Memory Test Score")
plt.figure()
plt.plot(memory)
plt.xlabel("Time")
plt.ylabel("Memory Test Score")
plt.title("Memory Performance Over Time")
st.pyplot(plt)

# Plot CO2 Levels
st.subheader("CO₂ Levels")
plt.figure()
plt.plot(co2)
plt.xlabel("Time")
plt.ylabel("CO₂ ppm")
plt.title("CO₂ Levels vs Cognitive Performance")
st.pyplot(plt)

# Combined Fatigue Visualization
st.subheader("Integrated Fatigue Score")
plt.figure()
plt.plot(data["fatigue_score"])
plt.xlabel("Time")
plt.ylabel("Fatigue Score")
plt.title("Integrated Cognitive Fatigue Score")
st.pyplot(plt)
