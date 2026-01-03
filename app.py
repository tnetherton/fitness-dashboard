import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import MinMaxScaler

# --- CONFIG ---
st.set_page_config(page_title="Squad Fitness", layout="wide")

# --- CUSTOM CSS ---
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
        border-radius: 10px;
        border: 1px solid #ddd;
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
    # 1. LOAD STRENGTH SHEET (Use Index 0 = First Tab)
    # using worksheet=0 is safer than forcing you to match the name perfectly
    df_strength = conn.read(worksheet=0, ttl=0)
    df_strength.columns = df_strength.columns.str.strip()
    
    # 2. LOAD MIND SHEET (Use Index 1 = Second Tab)
    try:
        df_mind = conn.read(worksheet=1, ttl=0)
        df_mind.columns = df_mind.columns.str.strip()
    except Exception:
        # Fallback if tab doesn't exist yet
        df_mind = pd.DataFrame(columns=['Date', 'User', 'Verses Memorized', 'Verse Reference'])

    # --- BENCHMARKS ---
    benchmark_data = {
        'User': ['Average Joe (30s)', 'Fit Phil (30s)', 'Elite Evan (30s)'],
        'Trap Bar DL (5RM Weight)': [275, 365, 495],
        'Bench (Reps @ BW)': [5, 12, 20],
        'Pull-Ups (Reps)': [5, 12, 25],
        'Farmers Carry (Dist ft)': [150, 200, 300],
        'Plank (Seconds)': [100, 150, 240],
        'Broad Jump (Dist in)': [84, 96, 110],
        '800m Run (Seconds)': [165, 150, 125],
        'Verses Memorized': [52, 365, 1000] 
    }
    df_bench = pd.DataFrame(benchmark_data)

except Exception as e:
    st.error(f"⚠️ Error connection to Google Sheets.\nError details: {e}")
    st.stop()

# --- CLEANING & CONSTANTS ---
strength_metrics = [
    'Bench (Reps @ BW)', 'Pull-Ups (Reps)', 'Trap Bar DL (5RM Weight)', 
    'Farmers Carry (Dist ft)', 'Plank (Seconds)', 'Broad Jump (Dist in)', 
    '800m Run (Seconds)'
]

# Ensure numeric columns exist in Strength Sheet
for col in strength_metrics:
    if col not in df_strength.columns:
        df_strength[col] = 0
    else:
        df_strength[col] = pd.to_numeric(df_strength[col], errors='coerce').fillna(0)

# Ensure numeric columns exist in Mind Sheet
if 'Verses Memorized' not in df_mind.columns:
    df_mind['Verses Memorized'] = 0
else:
    df_mind['Verses Memorized'] = pd.to_numeric(df_mind['Verses Memorized'], errors='coerce').fillna(0)

if 'Verse Reference' not in df_mind.columns:
    df_mind['Verse Reference'] = ""

# =========================================================
#  VIEW: HOME
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
#  VIEW: STRENGTH
# =========================================================
elif st.session_state['current_view'] == 'Strength':
    if st.button("← Back to Home"):
        navigate_to("Home")
        st.rerun()
        
    st.title("💪 Strength: Run with Endurance")
    
    users = df_strength['User'].unique().tolist()
    if not users:
        st.warning("No users found in Strength sheet.")
        st.stop()

    me = st.sidebar.selectbox("Select Athlete", users)
    # Filter STRENGTH data
    my_df = df_strength[df_strength['User'] == me].sort_values(by="Date")
    
    if my_df.empty:
        st.info("No strength data logged.")
    else:
        # RADAR
        all_dates = my_df['Date'].astype(str).tolist()
        default_dates = [all_dates[0], all_dates[-1]] if len(all_dates) > 1 else all_dates
        selected_dates = st.multiselect("Compare Dates:", options=all_dates, default=default_dates)
        
        radar_df = my_df[my_df['Date'].astype(str).isin(selected_dates)].copy()
        
        # Normalize
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

        # Trends
        if st.checkbox("📉 Show Trendlines"):
            df_long = my_df.melt(id_vars='Date', value_vars=strength_metrics, var_name='Metric', value_name='Value')
            fig_scatter = px.line(df_long, x='Date', y='Value', color='Metric', markers=True)
            st.plotly_chart(fig_scatter, use_container_width=True)

# =========================================================
#  VIEW: MIND & HEART
# =========================================================
elif st.session_state['current_view'] == 'MindHeart':
    if st.button("← Back to Home"):
        navigate_to("Home")
        st.rerun()
        
    st.title("❤️ Mind & Heart: Abide in My Word")
    
    # We use df_mind here
    if 'User' in df_mind.columns:
        users = df_mind['User'].unique().tolist()
    else:
        users = []
        
    if not users:
        st.info("No logs in 'mind and heart' sheet yet.")
        st.stop()
        
    me = st.sidebar.selectbox("Select Athlete", users)
    my_df = df_mind[df_mind['User'] == me].sort_values(by="Date")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📊 Totals")
        if not my_df.empty:
            total_verses = my_df['Verses Memorized'].sum()
            st.metric("Total Verses Hidden in Heart", int(total_verses))
            st.caption("Benchmark: 52 (Avg) | 365 (Fit) | 1000 (Elite)")
        else:
            st.info("No logs.")

    with col2:
        st.subheader("📖 Verse Log")
        if 'Verse Reference' in my_df.columns:
            # Filter for non-empty verses
            verse_log = my_df[my_df['Verse Reference'].str.len() > 2][['Date', 'Verse Reference', 'Verses Memorized']]
            st.dataframe(verse_log, use_container_width=True, hide_index=True)

    # Visualization
    st.subheader("Consistency Tracker")
    if not my_df.empty and my_df['Verses Memorized'].sum() > 0:
        fig_verses = px.bar(
            my_df, 
            x='Date', 
            y='Verses Memorized', 
            text='Verses Memorized',
            title="New Verses Memorized per Week",
            color_discrete_sequence=['#FF6B6B']
        )
        st.plotly_chart(fig_verses, use_container_width=True)

# =========================================================
#  VIEW: LEADERBOARD
# =========================================================
elif st.session_state['current_view'] == 'Leaderboard':
    if st.button("← Back to Home"):
        navigate_to("Home")
        st.rerun()

    st.title("🏆 Leaderboard")
    
    # 1. Calculate Strength MAX (From Sheet 1)
    df_max_strength = df_strength.groupby('User')[strength_metrics].max().reset_index()
    
    # 2. Calculate Verses TOTAL (From Sheet 2)
    if not df_mind.empty:
        df_sum_verses = df_mind.groupby('User')['Verses Memorized'].sum().reset_index()
    else:
        df_sum_verses = pd.DataFrame(columns=['User', 'Verses Memorized'])
        
    # 3. MERGE THE TWO DATASETS
    # We do an "outer" merge so if someone has logged scripture but not strength (or vice versa), they still appear
    df_merged = pd.merge(df_max_strength, df_sum_verses, on='User', how='outer').fillna(0)
        
    # 4. Handle 800m Run (Min is better)
    if '800m Run (Seconds)' in df_merged.columns:
        # We need to get the MIN run from the original strength df
        df_min_run = df_strength.groupby('User')['800m Run (Seconds)'].min().reset_index()
        # Update the merged df
        # (We map the min values over to the merged df)
        # Simple way: just drop the column and re-merge
        df_merged = df_merged.drop(columns=['800m Run (Seconds)'])
        df_merged = pd.merge(df_merged, df_min_run, on='User', how='left').fillna(0)

    # 5. Combine with Benchmarks
    df_combined = pd.concat([df_merged, df_bench], ignore_index=True)
    
    # 6. UI Selectors
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        all_names = df_combined['User'].unique().tolist()
        player_a = st.selectbox("Athlete A", all_names, index=0)
    with col_sel2:
        default_idx = all_names.index('Fit Phil (30s)') if 'Fit Phil (30s)' in all_names else 0
        player_b = st.selectbox("Athlete B", all_names, index=default_idx)

    df_compare = df_combined[df_combined['User'].isin([player_a, player_b])]

    # 7. PLOTS
    st.divider()
    
    # A. Spiritual Discipline
    st.subheader("⚔️ Spiritual Discipline (Total Verses)")
    if 'Verses Memorized' in df_compare.columns:
        fig_mind = px.bar(
            df_compare, 
            x='User', 
            y='Verses Memorized', 
            color='User', 
            text_auto=True,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_mind, use_container_width=True)

    # B. Strength (MAX)
    st.subheader("🏋️ Strength Comparison")
    
    group_1 = ['Trap Bar DL (5RM Weight)', 'Farmers Carry (Dist ft)']
    df_g1 = df_compare.melt(id_vars='User', value_vars=group_1, var_name='Metric', value_name='Value')
    st.plotly_chart(px.bar(df_g1, x='Metric', y='Value', color='User', barmode='group', text_auto=True), use_container_width=True)
    
    group_2 = ['Bench (Reps @ BW)', 'Pull-Ups (Reps)', 'Broad Jump (Dist in)']
    df_g2 = df_compare.melt(id_vars='User', value_vars=group_2, var_name='Metric', value_name='Value')
    st.plotly_chart(px.bar(df_g2, x='Metric', y='Value', color='User', barmode='group', text_auto=True), use_container_width=True)

    group_3 = ['Plank (Seconds)', '800m Run (Seconds)']
    df_g3 = df_compare.melt(id_vars='User', value_vars=group_3, var_name='Metric', value_name='Value')
    st.plotly_chart(px.bar(df_g3, x='Metric', y='Value', color='User', barmode='group', text_auto=True), use_container_width=True)