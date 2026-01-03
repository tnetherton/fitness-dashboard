import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIG ---
st.set_page_config(page_title="Squad Fitness", layout="wide")

# --- DATA LOADING ---
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # 1. Load User Data
    # Note: Ensure your Sheet has 'User' and 'Date' columns
    df = conn.read(ttl=0)
    df.columns = df.columns.str.strip() # Clean whitespace
    
    # 2. Hardcoded Benchmarks (Or load from a separate CSV/Sheet tab if you prefer)
    # I included the "Population Data" you requested here directly for simplicity
    benchmark_data = {
        'User': ['Average Joe (30s)', 'Fit Phil (30s)', 'Elite Evan (30s)'],
        'Trap Bar DL': [275, 365, 495],
        'Bench Press': [185, 225, 315],
        'Pull-Ups': [5, 12, 25],
        'Farmers Carry': [150, 200, 300], # Feet
        'Plank': [100, 150, 240],         # Seconds
        'Broad Jump': [84, 96, 110],      # Inches
        '800m Run': [165, 150, 125]       # Seconds (Lower is better)
    }
    df_bench = pd.DataFrame(benchmark_data)
    
except Exception as e:
    st.error(f"⚠️ Error connection to Google Sheets.\nError: {e}")
    st.stop()

# --- HELPER: CLEAN RAW DATA ---
# We need to make sure the columns are numeric for plotting
metric_cols = [
    'Trap Bar DL', 'Bench Press', 'Pull-Ups', 
    'Farmers Carry', 'Plank', 'Broad Jump', '800m Run'
]

# Ensure cols exist, if not create them with 0
for col in metric_cols:
    if col not in df.columns:
        df[col] = 0
    else:
        # Force numeric, turning errors (like "2:00") into NaN then 0
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# --- NAVIGATION ---
# Simple Sidebar Nav
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["My Progress", "Leaderboard"])

# --- PAGE 1: MY PROGRESS (RAW VALUES) ---
if page == "My Progress":
    st.title("📈 My Progress (Raw Stats)")
    
    # 1. User Selector
    users = df['User'].unique().tolist()
    if not users:
        st.warning("No users found.")
        st.stop()
        
    me = st.sidebar.selectbox("Select Athlete", users)
    
    # 2. Filter Data
    my_df = df[df['User'] == me].sort_values(by="Date")
    
    if my_df.empty:
        st.info("No data logged yet.")
    else:
        # 3. Line Charts for Raw Values
        st.subheader("Strength Progress (Lbs)")
        fig_strength = px.line(my_df, x='Date', y=['Trap Bar DL', 'Bench Press'], markers=True)
        st.plotly_chart(fig_strength, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Bodyweight Power")
            fig_bw = px.line(my_df, x='Date', y=['Pull-Ups', 'Broad Jump', 'Farmers Carry'], markers=True)
            st.plotly_chart(fig_bw, use_container_width=True)
            
        with col2:
            st.subheader("Endurance (Seconds)")
            # Note: Run time going DOWN is good, Plank time going UP is good.
            fig_time = px.line(my_df, x='Date', y=['Plank', '800m Run'], markers=True)
            st.plotly_chart(fig_time, use_container_width=True)

        st.caption("Note: 800m Run is in Seconds. Lower is better.")

# --- PAGE 2: LEADERBOARD ---
elif page == "Leaderboard":
    st.title("🏆 Leaderboard & Comparison")
    
    # 1. Prepare "Max" Data for Real Users
    # Group by User and take the MAX of each metric column
    # (For 800m run, we technically want MIN, but let's stick to MAX for simplicity logic first, 
    # or handle it separately)
    df_max = df.groupby('User')[metric_cols].max().reset_index()
    
    # Handle 800m Run: We actually want the MINIMUM time, not max
    if '800m Run' in df.columns:
        df_min_run = df.groupby('User')['800m Run'].min().reset_index()
        # Update the max df with the min run times
        df_max['800m Run'] = df_min_run['800m Run']

    # 2. Combine with Benchmark Data
    # This creates a master list of Real Guys + Average Joe
    df_combined = pd.concat([df_max, df_bench], ignore_index=True)

    # 3. Comparison Selectors
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        # Default to first user in list
        all_names = df_combined['User'].unique().tolist()
        player_a = st.selectbox("Athlete A (You)", all_names, index=0)
    with col_sel2:
        # Default to "Average Joe" if available, else last user
        default_index = all_names.index('Average Joe (30s)') if 'Average Joe (30s)' in all_names else 1
        player_b = st.selectbox("Athlete B (Opponent)", all_names, index=default_index)

    # 4. Filter for selected 2 people
    df_compare = df_combined[df_combined['User'].isin([player_a, player_b])]

    # 5. Side-by-Side Bar Charts
    # We split them into categories so the scales don't look crazy
    
    st.divider()
    
    # --- Strength Comparison ---
    st.subheader("🏋️ Strength (Lbs)")
    # Melt data for Plotly: Turns wide columns into long format for grouping
    df_strength = df_compare.melt(id_vars='User', value_vars=['Trap Bar DL', 'Bench Press'], var_name='Lift', value_name='Lbs')
    
    fig1 = px.bar(df_strength, x='Lift', y='Lbs', color='User', barmode='group', text_auto=True)
    fig1.update_layout(yaxis_title="Weight (lbs)")
    st.plotly_chart(fig1, use_container_width=True)

    # --- Reps & Distance Comparison ---
    st.subheader("🤸 Athletics (Reps/Inches/Feet)")
    df_athletics = df_compare.melt(id_vars='User', value_vars=['Pull-Ups', 'Broad Jump', 'Farmers Carry'], var_name='Event', value_name='Score')
    
    fig2 = px.bar(df_athletics, x='Event', y='Score', color='User', barmode='group', text_auto=True)
    st.plotly_chart(fig2, use_container_width=True)

    # --- Time Comparison ---
    st.subheader("⏱️ Endurance (Seconds)")
    df_time = df_compare.melt(id_vars='User', value_vars=['Plank', '800m Run'], var_name='Event', value_name='Seconds')
    
    fig3 = px.bar(df_time, x='Event', y='Seconds', color='User', barmode='group', text_auto=True)
    st.plotly_chart(fig3, use_container_width=True)
    
    st.info("💡 800m Run: Shorter bar is usually better (less time), but this chart shows raw seconds.")