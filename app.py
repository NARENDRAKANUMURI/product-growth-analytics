import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.express as px
import json
import os

# ================= Page Config =================
st.set_page_config(
    page_title="Product Growth Analytics",
    page_icon="📊",
    layout="wide"
)

# ================= User Database =================
USER_DB = "users.json"

def load_users():
    if os.path.exists(USER_DB):
        with open(USER_DB, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_DB, "w") as f:
        json.dump(users, f)

users = load_users()

# ================= Authentication =================
def login():
    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in users and users[username] == password:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid credentials")


def register():
    st.title("📝 Register")

    new_user = st.text_input("New Username")
    new_pass = st.text_input("New Password", type="password")

    if st.button("Register"):
        if new_user in users:
            st.warning("User already exists")
        else:
            users[new_user] = new_pass
            save_users(users)
            st.success("Registration successful. Please login.")

# ================= Session =================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

menu = st.sidebar.selectbox("Menu", ["Login", "Register"])

if not st.session_state["logged_in"]:

    if menu == "Login":
        login()
    else:
        register()

    st.stop()

# ================= Logout =================
st.sidebar.success(f"Welcome {st.session_state['username']}")

if st.sidebar.button("Logout"):
    st.session_state["logged_in"] = False
    st.rerun()

# ================= Load Data =================
data = pd.read_csv("product_analytics_final (1).csv")
model = joblib.load("conversion_model.pkl")

# ================= Sidebar Controls =================
st.sidebar.title("⚙️ Controls")

group_filter = st.sidebar.selectbox(
    "Select Experiment Group",
    ["All"] + list(data["group"].unique())
)

if group_filter != "All":
    data = data[data["group"] == group_filter]

page = st.sidebar.radio(
    "Navigate",
    ["Dashboard", "Experiment Analysis", "Prediction Tool"]
)

# ================= Dashboard =================
if page == "Dashboard":

    st.title("📊 Product Growth Analytics Dashboard")

    st.markdown("### Key Performance Indicators")

    col1, col2, col3, col4 = st.columns(4)

    total_users = len(data)
    conversion_rate = data["conversion"].mean()
    total_revenue = data["revenue"].sum()
    expected_revenue = (data["conversion_probability"] * data["revenue"]).sum()

    col1.metric("👥 Total Users", total_users)
    col2.metric("📈 Conversion Rate", f"{conversion_rate:.2%}")
    col3.metric("💰 Total Revenue", f"${total_revenue:,.2f}")
    col4.metric("🚀 Expected Revenue", f"${expected_revenue:,.2f}")

    st.markdown("---")

    col5, col6 = st.columns(2)

    conv_chart = data.groupby("group")["conversion"].mean().reset_index()
    fig1 = px.bar(
        conv_chart,
        x="group",
        y="conversion",
        color="group",
        title="Conversion Rate by Group"
    )

    rev_chart = data.groupby("group")["revenue"].mean().reset_index()
    fig2 = px.bar(
        rev_chart,
        x="group",
        y="revenue",
        color="group",
        title="Average Revenue by Group"
    )

    col5.plotly_chart(fig1, use_container_width=True)
    col6.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    col7, col8 = st.columns(2)

    sess_chart = data.groupby("conversion")["sessions"].mean().reset_index()
    fig3 = px.bar(
        sess_chart,
        x="conversion",
        y="sessions",
        title="Sessions vs Conversion"
    )

    time_chart = data.groupby("conversion")["time_spent"].mean().reset_index()
    fig4 = px.bar(
        time_chart,
        x="conversion",
        y="time_spent",
        title="Time Spent vs Conversion"
    )

    col7.plotly_chart(fig3, use_container_width=True)
    col8.plotly_chart(fig4, use_container_width=True)

# ================= Experiment Analysis =================
elif page == "Experiment Analysis":

    st.title("🧪 Experiment Analysis")

    fig = px.histogram(
        data,
        x="revenue",
        color="group",
        nbins=50,
        title="Revenue Distribution by Group"
    )

    st.plotly_chart(fig, use_container_width=True)

    engagement_chart = data.groupby("engagement_level")["revenue"].mean().reset_index()

    fig2 = px.bar(
        engagement_chart,
        x="engagement_level",
        y="revenue",
        color="engagement_level",
        title="Revenue by Engagement Level"
    )

    st.plotly_chart(fig2, use_container_width=True)

# ================= Prediction Tool =================
elif page == "Prediction Tool":

    st.title("🔮 Conversion Prediction Tool")

    col1, col2, col3 = st.columns(3)

    sessions = col1.number_input("Sessions", 1, 20, 5)
    time_spent = col2.number_input("Time Spent", 1.0, 30.0, 10.0)
    revenue = col3.number_input("Revenue", 1.0, 500.0, 50.0)

    if st.button("Predict Conversion"):

        input_data = pd.DataFrame({
            "sessions": [sessions],
            "time_spent": [time_spent],
            "revenue": [revenue]
        })

        try:
            prob = model.predict_proba(input_data)[0][1]
        except:
            pred = model.predict(input_data)[0]
            prob = 0.7 if pred == 1 else 0.3

        st.progress(int(prob * 100))

        if prob > 0.6:
            st.success(f"High Conversion Probability: {prob:.2%}")
        else:
            st.warning(f"Low Conversion Probability: {prob:.2%}")
