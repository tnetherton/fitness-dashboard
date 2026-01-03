It is great news that you got `secrets.toml` working! That is the professional way to handle data connections.

Here is the **final, polished `app.py**`.

* It reads from **Secrets**.
* It includes the **Quarterly Consistency Tracker** (instead of weekly).
* It keeps the global navigation and robust error handling.

**Action:** Replace your entire `app.py` with this code.

```python
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import MinMaxScaler

# --- CONFIG ---
st.set_page_config(page_title="Squad Fitness", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""<style>.big-quote {font-size: 24px;font-style: italic;text-align: center;color: #555;margin-bottom: 40px;}.verse-ref {font-size: 14px;text-align: center;color: #888;margin-top: -20px;margin-bottom: 40px;}.nav-label {font-size: 18px;font-style: italic;color: #444;text-align: center;margin-top: 10px;}div.stButton > button {width: 100%;height: 60px;font-size: 20px;font-weight: bold;border-radius: 10px;border: 1px solid #ddd;}</style>""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'current_view' not in st.session_state:
    st.session_state['current_view'] = 'Home'

def navigate_to(view):
    st.session_state['current_view'] = view

# --- DATA LOADING ---
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # 1. READ URLS FROM SECRETS
    strength_url = st.secrets["gsheets"]["strength_url"]
    mind_url = st.secrets["gsheets"]["mind_url"]

    # 2. LOAD STRENGTH
    df_strength = conn.read(spreadsheet=strength_url, ttl=0)
    df_strength.columns = df_strength.columns.str.strip()
    
    # 3. LOAD MIND
    try:
        df_mind = conn.read(spreadsheet=mind_url, ttl=0)
        df_mind.columns = df_mind.columns.str.strip()
    except Exception:
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
    st.error(f"⚠️ Connection Error. Check your secrets.toml file.\nDetails: {e}")
    st.stop()

# --- CLEANING & METRICS ---
if 'User' in df_strength.columns:
    df_strength['User'] = df_strength['User'].astype(str).str.strip()
if 'User' in df_mind.columns:
    df_mind['User'] = df_mind['User'].astype(str).str.strip()

strength_metrics = [
    'Bench (Reps @ BW)', 'Pull-Ups (Reps)', 'Trap Bar DL (5RM Weight)', 
    'Farmers Carry (Dist ft)', 'Plank (Seconds)', 'Broad Jump (Dist in)', 
    '800m Run (Seconds)'
]

for col in strength_metrics:
    if col not in df_strength.columns:
        df_strength[col] = 0
    else:
        df_strength[col] = pd.to_numeric(df_strength[col], errors='coerce').fillna(0)

if 'Verses Memorized' not in df_mind.columns:
    df_mind['Verses Memorized'] = 0
else:
    df_mind['Verses Memorized'] = pd.to_numeric(df_mind['Verses Memorized'], errors='coerce').fillna(0)

if 'Verse Reference' not in df_mind.columns:
    df_mind['Verse Reference'] = ""


# --- GLOBAL USER SELECTION ---
users_strength = set(df_strength['User'].unique()) if 'User' in df_strength.columns else set()
users_mind = set(df_mind['User'].unique()) if 'User' in df_mind.columns else set()
all_users = sorted(list(users_strength.union(users_mind)))

if not all_users:
    st.warning("No users found in database.")
    st.stop()

st.sidebar.title("Navigation")
me = st.sidebar.selectbox("Select Athlete", all_users, key="athlete_selector")


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
        st.button("💪 STRENGTH", on_click=navigate_to, args=("Strength",))
        st.markdown('<div class="nav-label">"Run with endurance"</div>', unsafe_allow_html=True)
        
    with col2:
        st.button("❤️ MIND & HEART", on_click=navigate_to, args=("MindHeart",))
        st.markdown('<div class="nav-label">"Abide in my word"</div>', unsafe_allow_html=True)

    with col3:
        st.button("🏆 LEADERBOARD", on_click=navigate_to, args=("Leaderboard",))
        st.markdown('<div class="nav-label">"Iron sharpens iron"</div>', unsafe_allow_html=True)

# =========================================================
#  VIEW: STRENGTH
# =========================================================
elif st.session_state['current_view'] == 'Strength':
    st.button("← Back to Home", on_click=navigate_to, args=("Home",))
    st.title("💪 Strength: Run with Endurance")
    st.caption(f"Viewing Data for: {me}")
    
    my_df = df_strength[df_strength['User'] == me].sort_values(by="Date")
    
    if my_df.empty:
        st.info(f"No strength data logged for {me} yet.")
    else:
        all_dates = my_df['Date'].astype(str).tolist()
        default_dates = [all_dates[0], all_dates[-1]] if len(all_dates) > 1 else all_dates
        selected_dates = st.multiselect("Compare Dates:", options=all_dates, default=default_dates)
        
        if selected_dates:
            radar_df = my_df[my_df['Date'].astype(str).isin(selected_dates)].copy()
            scaler = MinMaxScaler()
            scaler.fit(my_df[strength_metrics])
            radar_scaled = scaler.transform(radar_df[strength_metrics])
            radar_df_norm = pd.DataFrame(radar_scaled, columns=strength_metrics)
            radar_df_norm['Date'] = radar_df['Date'].values

            fig_radar = go.Figure()
            for i, date in enumerate(selected_dates):
                row_norm_data = radar_df_norm[radar_df_norm['Date'].astype(str) == date]
                row_raw_data = radar_df[radar_df['Date'].astype(str) == date]
                if not row_norm_data.empty and not row_raw_data.empty:
                    fig_radar.add_trace(go.Scatterpolar(
                        r=row_norm_data.iloc[0][strength_metrics],
                        theta=strength_metrics,
                        fill='toself' if i == len(selected_dates)-1 else 'none',
                        name=f"{date}",
                        hoverinfo='text',
                        text=[f"{m}: {val}" for m, val in zip(strength_metrics, row_raw_data.iloc[0][strength_metrics])]
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
#  VIEW: MIND & HEART
# =========================================================
elif st.session_state['current_view'] == 'MindHeart':
    st.button("← Back to Home", on_click=navigate_to, args=("Home",))
    st.title("❤️ Mind & Heart: Abide in My Word")
    st.caption(f"Viewing Data for: {me}")
    
    my_df = df_mind[df_mind['User'] == me].sort_values(by="Date")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("📊 Totals")
        if not my_df.empty:
            total_verses = my_df['Verses Memorized'].sum()
            st.metric("Total Verses Hidden in Heart", int(total_verses))
            st.caption("Benchmark: 52 (Avg) | 365 (Fit) | 1000 (Elite)")
        else:
            st.info(f"No scripture logs for {me}.")
            st.metric("Total Verses Hidden in Heart", 0)

    with col2:
        st.subheader("📖 Verse Log")
        if not my_df.empty and 'Verse Reference' in my_df.columns:
            verse_log = my_df[my_df['Verse Reference'].astype(str).str.len() > 2][['Date', 'Verse Reference', 'Verses Memorized']]
            st.dataframe(verse_log, use_container_width=True, hide_index=True)
        else:
             st.write("No verses recorded.")

    # --- UPDATED: QUARTERLY CHART ---
    st.subheader("Consistency Tracker (Quarterly)")
    if not my_df.empty and my_df['Verses Memorized'].sum() > 0:
        # Convert Date to Datetime
        my_df['Date'] = pd.to_datetime(my_df['Date'])
        # Create Quarter Column (e.g. 2025Q1)
        my_df['Quarter'] = my_df['Date'].dt.to_period('Q').astype(str)
        
        # Group by Quarter
        df_quarterly = my_df.groupby('Quarter')['Verses Memorized'].sum().reset_index()

        fig_verses = px.bar(
            df_quarterly, 
            x='Quarter', 
            y='Verses Memorized', 
            text='Verses Memorized',
            title="Verses Memorized per Quarter",
            color_discrete_sequence=['#FF6B6B']
        )
        st.plotly_chart(fig_verses, use_container_width=True)

# =========================================================
#  VIEW: LEADERBOARD
# =========================================================
elif st.session_state['current_view'] == 'Leaderboard':
    st.button("← Back to Home", on_click=navigate_to, args=("Home",))
    st.title("🏆 Leaderboard")
    
    df_max_strength = df_strength.groupby('User')[strength_metrics].max().reset_index()
    if not df_mind.empty:
        df_sum_verses = df_mind.groupby('User')['Verses Memorized'].sum().reset_index()
    else:
        df_sum_verses = pd.DataFrame(columns=['User', 'Verses Memorized'])
        
    df_merged = pd.merge(df_max_strength, df_sum_verses, on='User', how='outer').fillna(0)
    if '800m Run (Seconds)' in df_merged.columns:
        df_min_run = df_strength.groupby('User')['800m Run (Seconds)'].min().reset_index()
        df_merged = df_merged.drop(columns=['800m Run (Seconds)'])
        df_merged = pd.merge(df_merged, df_min_run, on='User', how='left').fillna(0)

    df_combined = pd.concat([df_merged, df_bench], ignore_index=True)
    
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        all_names = df_combined['User'].unique().tolist()
        player_a = st.selectbox("Athlete A", all_names, index=0)
    with col_sel2:
        default_idx = all_names.index('Fit Phil (30s)') if 'Fit Phil (30s)' in all_names else 0
        player_b = st.selectbox("Athlete B", all_names, index=default_idx)

    df_compare = df_combined[df_combined['User'].isin([player_a, player_b])]

    st.divider()
    st.subheader("⚔️ Spiritual Discipline (Total Verses)")
    if 'Verses Memorized' in df_compare.columns:
        fig_mind = px.bar(df_compare, x='User', y='Verses Memorized', color='User', text_auto=True, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_mind, use_container_width=True)

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