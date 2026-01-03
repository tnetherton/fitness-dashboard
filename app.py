import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.graph_objects as go

# --- CONFIG ---
st.set_page_config(page_title="Squad Fitness", layout="wide")

# --- SESSION STATE SETUP ---
# This "remembers" if you are logged in across reruns
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

# --- DATA LOADING ---
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl=0) 

# --- SIDEBAR: LOGIN ---
st.sidebar.header("User Login")

# Get unique users
if 'User' in df.columns:
    users = df['User'].unique().tolist()
    selected_user = st.sidebar.selectbox("Select Athlete", users)
else:
    st.error("Column 'User' not found in Google Sheet.")
    st.stop()

entered_pass = st.sidebar.text_input("Enter PIN", type="password")

# THE NEW LOGIN BUTTON LOGIC
if st.sidebar.button("Login"):
    # Get the specific user's row
    user_row = df[df['User'] == selected_user].iloc[-1]
    
    # Check password (ensure both are strings to avoid type errors)
    if str(user_row['Password']) == str(entered_pass):
        st.session_state['authenticated'] = True
        st.rerun() # Force app to reload immediately with new state
    else:
        st.session_state['authenticated'] = False
        st.sidebar.error("Incorrect PIN")

# Add a Logout button for convenience
if st.session_state['authenticated']:
    if st.sidebar.button("Logout"):
        st.session_state['authenticated'] = False
        st.rerun()

# --- MAIN DASHBOARD ---
if st.session_state['authenticated']:
    st.title(f"🚀 {selected_user}'s Performance Dashboard")
    
    # Get latest data
    user_data = df[df['User'] == selected_user].sort_values(by="Date").iloc[-1]

    # --- RADAR FUNCTION ---
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
                    range=[0, 3] # Fixed Scale: 0 to 3
                )),
            showlegend=False,
            title=title,
            margin=dict(t=40, b=0, l=40, r=40) # Tighter margins
        )
        return fig

    col1, col2, col3 = st.columns(3)

    with col1:
        # STRENGTH: Map the display names to the 'SCORE' columns in your Excel
        strength_map = {
            'Trap Bar DL': 'SCORE: Trap Bar',
            'Bench Press': 'SCORE: Bench',
            'Pull-Ups': 'SCORE: Pull-Ups',
            'Farmers Carry': 'SCORE: Carry',
            'Plank': 'SCORE: Plank',
            'Broad Jump': 'SCORE: Jump',
            '800m Run': 'SCORE: Run'
        }
        strength_cats = list(strength_map.keys())
        # Use .get() to avoid crashing if a column is missing
        strength_vals = [user_data.get(col, 0) for col in strength_map.values()]
        
        st.plotly_chart(make_radar(strength_cats, strength_vals, "Strength", "red"), use_container_width=True)
        st.caption("Scale: 1=Standard, 2=Elite, 3=Pro")

    with col2:
        # HEART (Placeholder columns - ensure these exist in Sheet or update names)
        heart_cats = ['Resting HR', 'VO2 Max', 'Zone 2 Mins']
        heart_vals = [user_data.get(cat, 0) for cat in heart_cats]
        st.plotly_chart(make_radar(heart_cats, heart_vals, "Heart", "blue"), use_container_width=True)

    with col3:
        # MIND (Placeholder columns)
        mind_cats = ['Meditation', 'Sleep', 'Journaling']
        mind_vals = [user_data.get(cat, 0) for cat in mind_cats]
        st.plotly_chart(make_radar(mind_cats, mind_vals, "Mind", "green"), use_container_width=True)

    st.divider()
    st.subheader("History Log")
    st.dataframe(df[df['User'] == selected_user])

else:
    st.info("👈 Please enter your PIN and click Login to view data.")