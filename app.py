import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.graph_objects as go

# --- CONFIG ---
st.set_page_config(page_title="Squad Fitness", layout="wide")

# --- SESSION STATE SETUP ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

# --- DATA LOADING ---
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Read Data (TTL=0 ensures fresh data)
    df = conn.read(ttl=0)
    # CRITICAL: Clean column names to remove accidental spaces
    df.columns = df.columns.str.strip()
except Exception as e:
    st.error(f"⚠️ Error connection to Google Sheets. Check your secrets.\nError: {e}")
    st.stop()

# --- SIDEBAR: LOGIN ---
st.sidebar.header("User Login")

if 'User' not in df.columns:
    st.error("❌ Critical Error: 'User' column not found.")
    st.stop()

users = df['User'].unique().tolist()
selected_user = st.sidebar.selectbox("Select Athlete", users)

# Check for Password Column
if 'Password' not in df.columns:
    st.warning("⚠️ 'Password' column missing. Bypassing auth.")
    st.session_state['authenticated'] = True
else:
    # Login Form
    with st.sidebar.form("login_form"):
        entered_pass = st.text_input("Enter PIN", type="password")
        if st.form_submit_button("Login"):
            # SAFEGUARD: Check if user actually has rows
            user_df = df[df['User'] == selected_user]
            if user_df.empty:
                st.error("User found in list but has no data rows!")
            else:
                user_row = user_df.iloc[-1]
                # Convert to string to avoid format mismatches
                if str(user_row['Password']) == str(entered_pass):
                    st.session_state['authenticated'] = True
                    st.rerun()
                else:
                    st.session_state['authenticated'] = False
                    st.error("Incorrect PIN")

if st.session_state.get('authenticated', False) and st.sidebar.button("Logout"):
    st.session_state['authenticated'] = False
    st.rerun()

# --- MAIN DASHBOARD ---
if st.session_state['authenticated']:
    st.title(f"🚀 {selected_user}'s Performance Dashboard")
    
    # 1. Filter for User
    user_df = df[df['User'] == selected_user]

    # 2. ROBUSTNESS CHECK: Does the user have data?
    if user_df.empty:
        st.info("👋 Welcome! You don't have any logged workouts yet. Submit a form to see your stats.")
    else:
        # 3. Get latest row safely
        if 'Date' in df.columns:
            user_data = user_df.sort_values(by="Date").iloc[-1]
        else:
            user_data = user_df.iloc[-1]
        
        # 4. CRITICAL: Fill empty cells (NaN) with 0 to prevent crashes
        user_data = user_data.fillna(0)

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
                    radialaxis=dict(visible=True, range=[0, 3])
                ),
                showlegend=False,
                title=title,
                margin=dict(t=40, b=20, l=40, r=40)
            )
            return fig

        # --- DASHBOARD LAYOUT ---
        col1, col2, col3 = st.columns(3)

        with col1:
            # STRENGTH
            strength_map = {
                'Trap Bar DL': 'SCORE_TrapBar',
                'Bench Press': 'SCORE_Bench',
                'Pull-Ups': 'SCORE_Pullups',
                'Farmers Carry': 'SCORE_Carry',
                'Plank': 'SCORE_Plank',
                'Broad Jump': 'SCORE_Jump',
                '800m Run': 'SCORE_Run'
            }
            # Extract values safely
            s_cats = list(strength_map.keys())
            # We already ran .fillna(0) on user_data, so this is safe from NaNs
            s_vals = [user_data.get(col, 0) for col in strength_map.values()]
            st.plotly_chart(make_radar(s_cats, s_vals, "Strength", "red"), use_container_width=True)

        with col2:
            # HEART
            heart_map = {
                'Resting HR': 'Heart_RHR',
                'Zone 2': 'Heart_Zone2_Min'
            }
            h_cats = list(heart_map.keys())
            h_vals = [user_data.get(col, 0) for col in heart_map.values()]
            st.plotly_chart(make_radar(h_cats, h_vals, "Heart", "blue"), use_container_width=True)

        with col3:
            # MIND
            mind_map = {
                'Meditation': 'Mind_Meditation_Min',
                'Sleep': 'Mind_Sleep_Hrs'
            }
            m_cats = list(mind_map.keys())
            m_vals = [user_data.get(col, 0) for col in mind_map.values()]
            st.plotly_chart(make_radar(m_cats, m_vals, "Mind", "green"), use_container_width=True)

        # --- HISTORY TABLE ---
        st.divider()
        st.subheader("History Log")
        display_df = user_df.copy()
        if 'Password' in display_df.columns:
            display_df = display_df.drop(columns=['Password'])
        st.dataframe(display_df, use_container_width=True)

else:
    st.info("👈 Please enter your PIN and click Login.")