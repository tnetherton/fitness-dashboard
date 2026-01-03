import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import MinMaxScaler

# --- CONFIG ---
st.set_page_config(page_title="Squad Fitness", layout="wide")

# --- CUSTOM CSS (For Sleek Buttons & Typography) ---
st.markdown("""
<style>
    .big-quote {
        font-size: 24px;
        font-style: italic;
        text-align: center;
        color: #555;
        margin-bottom: 40px;
    }
    .verse-ref {
        font-size: 14px;
        text-align: center;
        color: #888;
        margin-top: -20px;
        margin-bottom: 40px;
    }
    .nav-label {
        font-size: 18px;
        font-style: italic;
        color: #444;
        text-align: center;
        margin-top: 10px;
    }
    div.stButton > button {
        width: 100%;
        height: 60px;
        font-size: 20px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE NAVIGATION ---
if 'current_view' not in st.session_state:
    st.session_state['current_view'] = 'Home'

def navigate_to(view):
    st.session_state['current_view'] = view

# --- DATA LOADING ---
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df = conn.read(ttl=0)
    df.columns = df.columns.str.strip()
    
    # --- BENCHMARKS (Updated with Verse Goal) ---
    benchmark_data = {
        'User': ['Average Joe (30s)', 'Fit Phil (30s)', 'Elite Evan (30s)'],
        'Trap Bar DL (5RM Weight)': [275, 365, 495],
        'Bench (Reps @ BW)': [5, 12, 20],
        'Pull-Ups (Reps)': [5, 12, 25],
        'Farmers Carry (Dist ft)': [150, 200, 300],
        'Plank (Seconds)': [100, 150, 240],
        'Broad Jump (Dist in)': [84, 96, 110],
        '800m Run (Seconds)': [165, 150, 125],
        'Verses Memorized': [1, 3, 5] # Weekly Goal Benchmark
    }
    df_bench = pd.DataFrame(benchmark_data)

except Exception as e:
    st.error(f"⚠️ Error connection to Google Sheets.\nError: {e}")
    st.stop()

# --- CONSTANTS ---
strength_metrics = [
    'Bench (Reps @ BW)', 'Pull-Ups (Reps)', 'Trap Bar DL (5RM Weight)', 
    'Farmers Carry (Dist ft)', 'Plank (Seconds)', 'Broad Jump (Dist in)', 
    '800m Run (Seconds)'
]
mind_metrics = ['Verses Memorized']

# Ensure columns exist
all_metrics = strength_metrics + mind_metrics
for col in all_metrics:
    if col not in df.columns:
        df[col] = 0
    else:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# Ensure Text Column exists
if 'Verse Reference' not in df.columns:
    df['Verse Reference'] = ""

# =========================================================
#  VIEW: HOME (Landing Page)
# =========================================================
if st.session_state['current_view'] == 'Home':
    st.title("🛡️ The Full Armor")
    st.markdown('<div class="big-quote">"Love the Lord your God with all your heart and with all your soul and with all your mind and with all your strength."</div>', unsafe_allow_html=True)
    st.markdown('<div class="verse-ref">Mark 12:30 / Deut 6:5</div>', unsafe_allow_html=True)
    
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💪 STRENGTH"):
            navigate_to("Strength")
        st.markdown('<div class="nav-label">"Run with endurance"</div>', unsafe_allow_html=True)
        
    with col2:
        if st.button("❤️ MIND & HEART"):
            navigate_to("MindHeart")
        st.markdown('<div class="nav-label">"Abide in my word"</div>', unsafe_allow_html=True)

    with col3:
        if st.button("🏆 LEADERBOARD"):
            navigate_to("Leaderboard")
        st.markdown('<div class="nav-label">"Iron sharpens iron"</div>', unsafe_allow_html=True)

# =========================================================
#  VIEW: STRENGTH (Original Radar & Trends)
# =========================================================
elif st.session_state['current_view'] == 'Strength':
    if st.button("← Back to Home"):
        navigate_to("Home")
        st.rerun()
        
    st.title("💪 Strength: Run with Endurance")
    
    # User Select
    users = df['User'].unique().tolist()
    me = st.sidebar.selectbox("Select Athlete", users)
    my_df = df[df['User'] == me].sort_values(by="Date")
    
    if my_df.empty:
        st.info("No data logged.")
    else:
        # RADAR LOGIC
        all_dates = my_df['Date'].astype(str).tolist()
        default_dates = [all_dates[0], all_dates[-1]] if len(all_dates) > 1 else all_dates
        selected_dates = st.multiselect("Compare Dates:", options=all_dates, default=default_dates)
        
        radar_df = my_df[my_df['Date'].astype(str).isin(selected_dates)].copy()
        
        # Normalize for Plotting
        scaler = MinMaxScaler()
        scaler.fit(my_df[strength_metrics])
        radar_scaled = scaler.transform(radar_df[strength_metrics])
        radar_df_norm = pd.DataFrame(radar_scaled, columns=strength_metrics)
        radar_df_norm['Date'] = radar_df['Date'].values

        fig_radar = go.Figure()
        for i, date in enumerate(selected_dates):
            row_norm = radar_df_norm[radar_df_norm['Date'].astype(str) == date].iloc[0]
            row_raw = radar_df[radar_df['Date'].astype(str) == date].iloc[0]
            
            fig_radar.add_trace(go.Scatterpolar(
                r=row_norm[strength_metrics],
                theta=strength_metrics,
                fill='toself' if i == len(selected_dates)-1 else 'none',
                name=f"{date}",
                hoverinfo='text',
                text=[f"{m}: {val}" for m, val in zip(strength_metrics, row_raw[strength_metrics])]
            ))

        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=False, range=[0, 1.1])),
            margin=dict(t=20, b=20, l=40, r=40)
        )
        st.plotly_chart(fig_radar, use_container_width=True)

        if st.checkbox("📉 Show Trendlines"):
            df_long = my_df.melt(id_vars='Date', value_vars=strength_metrics, var_name='Metric', value_name='Value')
            fig_scatter = px.line(df_long, x='Date', y='Value', color='Metric', markers=True)
            st.plotly_chart(fig_scatter, use_container_width=True)

# =========================================================
#  VIEW: MIND & HEART (Scripture Tracking)
# =========================================================
elif st.session_state['current_view'] == 'MindHeart':
    if st.button("← Back to Home"):
        navigate_to("Home")
        st.rerun()
        
    st.title("❤️ Mind & Heart: Abide in My Word")
    
    users = df['User'].unique().tolist()
    me = st.sidebar.selectbox("Select Athlete", users)
    my_df = df[df['User'] == me].sort_values(by="Date")
    
    # 1. VISUALIZATION: Bar Graph of Verses Memorized Over Time
    st.subheader("📖 Memorization Consistency")
    if not my_df.empty and my_df['Verses Memorized'].sum() > 0:
        fig_verses = px.bar(
            my_df, 
            x='Date', 
            y='Verses Memorized', 
            text='Verses Memorized',
            title="New Verses Memorized per Week",
            color_discrete_sequence=['#4C78A8'] # Muted Blue
        )
        fig_verses.update_traces(textposition='auto')
        st.plotly_chart(fig_verses, use_container_width=True)
    else:
        st.info("No scripture data logged yet. Add 'Verses Memorized' to your sheet.")

    # 2. DATA TABLE: The Word
    st.subheader("📜 My Sword (Verse Log)")
    if 'Verse Reference' in my_df.columns:
        # Filter for rows that actually have a verse
        verse_log = my_df[my_df['Verse Reference'].str.len() > 2][['Date', 'Verse Reference', 'Verses Memorized']]
        st.dataframe(verse_log, use_container_width=True, hide_index=True)

# =========================================================
#  VIEW: LEADERBOARD
# =========================================================
elif st.session_state['current_view'] == 'Leaderboard':
    if st.button("← Back to Home"):
        navigate_to("Home")
        st.rerun()

    st.title("🏆 Leaderboard")
    
    # Prepare Data (Max for Strength, Sum/Max for Verses)
    df_max = df.groupby('User')[strength_metrics].max().reset_index()
    
    # For verses, we might want TOTAL verses memorized (Sum)
    if 'Verses Memorized' in df.columns:
        df_sum_verses = df.groupby('User')['Verses Memorized'].sum().reset_index()
        df_max = pd.merge(df_max, df_sum_verses, on='User')
        
    # Handle 800m Run (Min is better)
    if '800m Run (Seconds)' in df.columns:
        df_min_run = df.groupby('User')['800m Run (Seconds)'].min().reset_index()
        df_max['800m Run (Seconds)'] = df_min_run['800m Run (Seconds)']

    df_combined = pd.concat([df_max, df_bench], ignore_index=True)
    
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        all_names = df_combined['User'].unique().tolist()
        player_a = st.selectbox("Athlete A", all_names, index=0)
    with col_sel2:
        default_idx = all_names.index('Average Joe (30s)') if 'Average Joe (30s)' in all_names else 0
        player_b = st.selectbox("Athlete B", all_names, index=default_idx)

    df_compare = df_combined[df_combined['User'].isin([player_a, player_b])]

    st.subheader("⚔️ Spiritual Discipline Comparison")
    if 'Verses Memorized' in df_compare.columns:
        fig_mind = px.bar(
            df_compare, 
            x='User', 
            y='Verses Memorized', 
            color='User', 
            text_auto=True,
            title="Total Verses Memorized"
        )
        st.plotly_chart(fig_mind, use_container_width=True)

    st.subheader("🏋️ Strength Comparison")
    # Group 1: Heavy
    group_1 = ['Trap Bar DL (5RM Weight)', 'Farmers Carry (Dist ft)']
    df_g1 = df_compare.melt(id_vars='User', value_vars=group_1, var_name='Metric', value_name='Value')
    st.plotly_chart(px.bar(df_g1, x='Metric', y='Value', color='User', barmode='group', text_auto=True), use_container_width=True)
    
    # Group 2: Bodyweight
    group_2 = ['Bench (Reps @ BW)', 'Pull-Ups (Reps)', 'Broad Jump (Dist in)']
    df_g2 = df_compare.melt(id_vars='User', value_vars=group_2, var_name='Metric', value_name='Value')
    st.plotly_chart(px.bar(df_g2, x='Metric', y='Value', color='User', barmode='group', text_auto=True), use_container_width=True)

    # Group 3: Time
    group_3 = ['Plank (Seconds)', '800m Run (Seconds)']
    df_g3 = df_compare.melt(id_vars='User', value_vars=group_3, var_name='Metric', value_name='Value')
    st.plotly_chart(px.bar(df_g3, x='Metric', y='Value', color='User', barmode='group', text_auto=True), use_container_width=True)