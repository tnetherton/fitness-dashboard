import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import MinMaxScaler

# --- CONFIG ---
st.set_page_config(page_title="Squad Fitness", layout="wide")

# --- NAVIGATION ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["My Progress", "Leaderboard"])

# --- DATA LOADING ---
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df = conn.read(ttl=0)
    df.columns = df.columns.str.strip() # Clean whitespace
    
    # --- BENCHMARKS (Hardcoded for Leaderboard) ---
    benchmark_data = {
        'User': ['Average Joe (30s)', 'Fit Phil (30s)', 'Elite Evan (30s)'],
        'Trap Bar DL (5RM Weight)': [275, 365, 495],
        'Bench (Reps @ BW)': [5, 12, 20],         # Adjusted for Reps
        'Pull-Ups (Reps)': [5, 12, 25],
        'Farmers Carry (Dist ft)': [150, 200, 300],
        'Plank (Seconds)': [100, 150, 240],
        'Broad Jump (Dist in)': [84, 96, 110],
        '800m Run (Seconds)': [165, 150, 125]     # Lower is better
    }
    df_bench = pd.DataFrame(benchmark_data)

except Exception as e:
    st.error(f"⚠️ Error connection to Google Sheets.\nError: {e}")
    st.stop()

# --- CONSTANTS: Define the 7 Body Metrics ---
# These MUST match your Google Sheet headers exactly
body_metrics = [
    'Bench (Reps @ BW)',
    'Pull-Ups (Reps)', 
    'Trap Bar DL (5RM Weight)', 
    'Farmers Carry (Dist ft)', 
    'Plank (Seconds)', 
    'Broad Jump (Dist in)', 
    '800m Run (Seconds)'
]

# Ensure columns exist and are numeric
for col in body_metrics:
    if col not in df.columns:
        df[col] = 0
    else:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# --- PAGE 1: MY PROGRESS (RADAR + SCATTER) ---
if page == "My Progress":
    st.title("💪 Body Metrics Radar")
    
    # 1. User Selector
    users = df['User'].unique().tolist()
    if not users:
        st.warning("No users found.")
        st.stop()
        
    me = st.sidebar.selectbox("Select Athlete", users)
    
    # 2. Filter & Sort Data
    my_df = df[df['User'] == me].sort_values(by="Date")
    
    if my_df.empty:
        st.info("No data logged yet.")
    else:
        # --- A. DATE SELECTOR (For Radar Comparison) ---
        # Default to First (Baseline) and Last (Current)
        all_dates = my_df['Date'].astype(str).tolist()
        default_dates = [all_dates[0], all_dates[-1]] if len(all_dates) > 1 else all_dates
        
        selected_dates = st.multiselect(
            "Select Dates to Compare on Radar:", 
            options=all_dates, 
            default=default_dates
        )
        
        # Filter data for radar
        radar_df = my_df[my_df['Date'].astype(str).isin(selected_dates)].copy()

        # --- B. RADAR CHART (NORMALIZED) ---
        # We normalize data 0-1 just for PLOTTING so the shape looks right,
        # but we show RAW values in the hover text.
        
        # 1. Create Scaler based on the User's Max history (so chart fills up as they grow)
        scaler = MinMaxScaler()
        # Fit scaler on ALL user data to keep scale consistent across dates
        scaler.fit(my_df[body_metrics]) 
        
        # Transform the selected rows
        radar_scaled = scaler.transform(radar_df[body_metrics])
        radar_df_norm = pd.DataFrame(radar_scaled, columns=body_metrics)
        radar_df_norm['Date'] = radar_df['Date'].values # Add dates back

        # Draw Chart
        fig_radar = go.Figure()

        for i, date in enumerate(selected_dates):
            # Get normalized values for shape
            row_norm = radar_df_norm[radar_df_norm['Date'].astype(str) == date].iloc[0]
            # Get RAW values for hover
            row_raw = radar_df[radar_df['Date'].astype(str) == date].iloc[0]
            
            fig_radar.add_trace(go.Scatterpolar(
                r=row_norm[body_metrics], # Plot Normalized
                theta=body_metrics,
                fill='toself' if i == len(selected_dates)-1 else 'none', # Only fill the newest one
                name=f"{date}",
                hoverinfo='text', # Custom Tooltip
                text=[f"{m}: {val}" for m, val in zip(body_metrics, row_raw[body_metrics])] # Show RAW
            ))

        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=False, range=[0, 1.1]) # Hide axis numbers since they are 0-1
            ),
            title="Body Shape (Comparing Dates)",
            margin=dict(t=40, b=20, l=40, r=40)
        )
        st.plotly_chart(fig_radar, use_container_width=True)
        st.caption("ℹ️ Chart shape is normalized relative to your history. Hover over points to see RAW values.")

        # --- C. SCATTER PLOT TOGGLE ---
        st.divider()
        if st.checkbox("📉 Show Trendlines (Scatter Plots)", value=False):
            st.subheader("Raw Trends Over Time")
            # Create a long-form dataframe for scatter plotting all at once
            df_long = my_df.melt(id_vars='Date', value_vars=body_metrics, var_name='Metric', value_name='Value')
            
            fig_scatter = px.line(
                df_long, 
                x='Date', 
                y='Value', 
                color='Metric', 
                markers=True,
                title="All Body Metrics History"
            )
            fig_scatter.update_layout(height=600)
            st.plotly_chart(fig_scatter, use_container_width=True)

# --- PAGE 2: LEADERBOARD ---
elif page == "Leaderboard":
    st.title("🏆 Leaderboard")
    
    # 1. Prepare "Max" Data
    df_max = df.groupby('User')[body_metrics].max().reset_index()
    
    # Handle 800m Run (Min is better)
    if '800m Run (Seconds)' in df.columns:
        df_min_run = df.groupby('User')['800m Run (Seconds)'].min().reset_index()
        df_max['800m Run (Seconds)'] = df_min_run['800m Run (Seconds)']

    # 2. Combine with Benchmarks
    df_combined = pd.concat([df_max, df_bench], ignore_index=True)

    # 3. Selectors
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        all_names = df_combined['User'].unique().tolist()
        player_a = st.selectbox("Athlete A (You)", all_names, index=0)
    with col_sel2:
        default_idx = all_names.index('Average Joe (30s)') if 'Average Joe (30s)' in all_names else 0
        player_b = st.selectbox("Athlete B (Opponent)", all_names, index=default_idx)

    # 4. Filter
    df_compare = df_combined[df_combined['User'].isin([player_a, player_b])]

    # 5. Plot All 7 Metrics
    st.subheader("Head-to-Head Comparison")
    
    # Melt all 7 metrics into one big chart (or you can split them like before)
    # Splitting is better because of scale differences (Reps vs Lbs)
    
    # GROUP 1: Heavy Weights / Distance
    group_1 = ['Trap Bar DL (5RM Weight)', 'Farmers Carry (Dist ft)']
    df_g1 = df_compare.melt(id_vars='User', value_vars=group_1, var_name='Metric', value_name='Value')
    fig1 = px.bar(df_g1, x='Metric', y='Value', color='User', barmode='group', text_auto=True, title="Heavy Lifts & Carries")
    st.plotly_chart(fig1, use_container_width=True)
    
    # GROUP 2: Bodyweight / Reps / Inches
    group_2 = ['Bench (Reps @ BW)', 'Pull-Ups (Reps)', 'Broad Jump (Dist in)']
    df_g2 = df_compare.melt(id_vars='User', value_vars=group_2, var_name='Metric', value_name='Value')
    fig2 = px.bar(df_g2, x='Metric', y='Value', color='User', barmode='group', text_auto=True, title="Bodyweight Power & Reps")
    st.plotly_chart(fig2, use_container_width=True)

    # GROUP 3: Time (Seconds)
    group_3 = ['Plank (Seconds)', '800m Run (Seconds)']
    df_g3 = df_compare.melt(id_vars='User', value_vars=group_3, var_name='Metric', value_name='Value')
    fig3 = px.bar(df_g3, x='Metric', y='Value', color='User', barmode='group', text_auto=True, title="Endurance (Seconds)")
    st.plotly_chart(fig3, use_container_width=True)