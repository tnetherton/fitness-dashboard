import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.graph_objects as go

# --- CONFIG ---
st.set_page_config(page_title="Squad Fitness", layout="wide")

# --- SESSION STATE SETUP ---
# Initialize session state for authentication if it doesn't exist
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

# --- DATA LOADING ---
# Establish connection to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Read Data (TTL=0 means it won't cache, so you see updates instantly)
    df = conn.read(ttl=0)
except Exception as e:
    st.error(f"⚠️ Error connection to Google Sheets. Make sure your secrets.toml is correct and the Sheet is public. \n Error details: {e}")
    st.stop()

# --- SIDEBAR: LOGIN ---
st.sidebar.header("User Login")

# 1. Critical Check: Ensure 'User' column exists
if 'User' not in df.columns:
    st.error(f"❌ Critical Error: Could not find a 'User' column in your Google Sheet.\nFound columns: {df.columns.tolist()}")
    st.stop()

# 2. User Selection
users = df['User'].unique().tolist()
selected_user = st.sidebar.selectbox("Select Athlete", users)

# 3. Password Logic (Defensive)
# If 'Password' column is missing, we bypass authentication to prevent crashing.
if 'Password' not in df.columns:
    st.sidebar.warning("⚠️ 'Password' column not found in Sheet. Bypassing login.")
    st.session_state['authenticated'] = True # Auto-login if no password col
else:
    # The column exists, so we show the PIN field
    entered_pass = st.sidebar.text_input("Enter PIN", type="password")
    
    if st.sidebar.button("Login"):
        # Get the latest row for this user
        user_row = df[df['User'] == selected_user].iloc[-1]
        
        # Check PIN (convert both to string to be safe against formatting diffs)
        real_pass = str(user_row['Password'])
        
        if real_pass == str(entered_pass):
            st.session_state['authenticated'] = True
            st.rerun() # Force reload to update the main page
        else:
            st.session_state['authenticated'] = False
            st.sidebar.error("Incorrect PIN")

# 4. Logout Button
if st.session_state['authenticated'] and 'Password' in df.columns:
    if st.sidebar.button("Logout"):
        st.session_state['authenticated'] = False
        st.rerun()

# --- MAIN DASHBOARD ---
if st.session_state['authenticated']:
    st.title(f"🚀 {selected_user}'s Performance Dashboard")
    
    # Get latest data for the user (Sorting by Date to get the most recent entry)
    if 'Date' in df.columns:
        user_data = df[df['User'] == selected_user].sort_values(by="Date").iloc[-1]
    else:
        # Fallback if Date is missing
        user_data = df[df['User'] == selected_user].iloc[-1]

    # --- RADAR CHART FUNCTION ---
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
                    range=[0, 3] # Fixed Scale: 0 (Start) to 3 (Pro)
                )),
            showlegend=False,
            title=title,
            margin=dict(t=40, b=20, l=40, r=40)
        )
        return fig

    # --- DASHBOARD LAYOUT ---
    col1, col2, col3 = st.columns(3)

    with col1:
        # STRENGTH
        # Map the display names to the 'SCORE' columns from the Excel template
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
        
        # Safely get values, defaulting to 0 if the column doesn't exist yet
        strength_vals = [user_data.get(col, 0) for col in strength_map.values()]
        
        st.plotly_chart(make_radar(strength_cats, strength_vals, "Strength", "red"), use_container_width=True)
        st.caption("Standards: 1=The Standard, 2=Elite, 3=Pro")

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

    # --- HISTORY TABLE ---
    st.divider()
    st.subheader("History Log")
    # Show the user's data, dropping the technical 'Password' column for privacy
    display_df = df[df['User'] == selected_user].copy()
    if 'Password' in display_df.columns:
        display_df = display_df.drop(columns=['Password'])
        
    st.dataframe(display_df, use_container_width=True)

else:
    # Not authenticated
    if 'Password' in df.columns:
        st.info("👈 Please enter your PIN and click Login to view data.")
    else:
        st.info("Please select a user.")