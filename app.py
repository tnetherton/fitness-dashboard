import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.graph_objects as go

# --- CONFIG ---
st.set_page_config(page_title="Squad Fitness", layout="wide")

# --- DATA LOADING ---
# Establish connection to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Read Data (TTL=0 means it won't cache, so you see updates instantly)
df = conn.read(ttl=0)

# --- SIDEBAR: LOGIN ---
st.sidebar.header("User Login")
# Get unique users from the sheet
users = df['User'].unique().tolist()
selected_user = st.sidebar.selectbox("Select Athlete", users)

# Simple Password Check (Assuming a 'Password' column exists in your sheet)
# In production for friends, you might just skip this or use a simple hardcoded dict in secrets
entered_pass = st.sidebar.text_input("Enter PIN", type="password")
user_row = df[df['User'] == selected_user].iloc[-1] # Get latest entry for auth check

authenticated = False
if str(user_row['Password']) == entered_pass:
    authenticated = True
else:
    st.sidebar.warning("Incorrect PIN")

# --- MAIN DASHBOARD ---
if authenticated:
    st.title(f"🚀 {selected_user}'s Performance Dashboard")
    
    # Get latest data for the user
    # Logic: Get the row with the most recent Date
    user_data = df[df['User'] == selected_user].sort_values(by="Date").iloc[-1]

    # --- HELPER FUNCTION FOR RADAR PLOTS ---
    def make_radar(categories, values, title, color):
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=title,
            line_color=color
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 3] # Normalized Scale: 0=Start, 1=Standard, 2=Elite, 3=Pro
                )),
            showlegend=False,
            title=title
        )
        return fig

    # --- NORMALIZE DATA (CRITICAL STEP) ---
    # Since '800m Run' is time and 'Deadlift' is weight, you can't plot them on one axis raw.
    # You need to normalize inputs to a score of 0-3 based on your PDF standards.
    # For this MVP, let's assume your Google Sheet columns already contain the "Score" (0-3).
    # If not, you would write a helper function here to convert raw numbers to scores.

    col1, col2, col3 = st.columns(3)

    with col1:
        # STRENGTH (Metrics from your PDF)
        strength_cats = ['Trap Bar DL', 'Bench Press', 'Pull-Ups', 'Farmers Carry', 'Plank', 'Broad Jump', '800m Run']
        # Fetch values safely, defaulting to 0 if missing
        strength_vals = [user_data.get(cat, 0) for cat in strength_cats]
        st.plotly_chart(make_radar(strength_cats, strength_vals, "Strength", "red"), use_container_width=True)
        st.caption("Scale: 1=The Standard, 2=Elite, 3=Pro")

    with col2:
        # HEART
        heart_cats = ['Resting HR', 'VO2 Max', 'Zone 2 Mins']
        heart_vals = [user_data.get(cat, 0) for cat in heart_cats]
        st.plotly_chart(make_radar(heart_cats, heart_vals, "Heart", "blue"), use_container_width=True)

    with col3:
        # MIND
        mind_cats = ['Meditation', 'Sleep', 'Journaling']
        mind_vals = [user_data.get(cat, 0) for cat in mind_cats]
        st.plotly_chart(make_radar(mind_cats, mind_vals, "Mind", "green"), use_container_width=True)

    # Show Raw Data History
    st.divider()
    st.subheader("History Log")
    st.dataframe(df[df['User'] == selected_user])

else:
    st.info("Please log in to view data.")