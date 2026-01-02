# 🏋️ Squad Fitness Tracker

A private fitness dashboard for our group to track progress across three focus areas: **Mind, Heart, and Strength**. 

This application visualizes our weekly performance using "Daisy Plots" (Radar Charts) to identify baselines and goals based on our custom performance standards.

## 🏗 Architecture

* **Frontend:** [Streamlit](https://streamlit.io/) (Python)
* **Database:** Google Sheets (Acts as a lightweight relational DB)
* **Data Entry:** Google Forms (Linked to the Sheet for mobile-friendly input)
* **Visualization:** Plotly (Interactive Polar/Radar charts)

## 🚀 Local Development Setup

Prerequisites: Python 3.8+ installed.

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/squad-fitness.git](https://github.com/YOUR_USERNAME/squad-fitness.git)
    cd squad-fitness
    ```

2.  **Create a virtual environment:**
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # Mac/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Secrets:**
    * Create a folder `.streamlit` in the root directory.
    * Create a file `.streamlit/secrets.toml`.
    * Add the Google Sheet connection string (ask admin for the link):
    ```toml
    [connections.gsheets]
    spreadsheet = "YOUR_GOOGLE_SHEET_URL"
    ```

5.  **Run the App:**
    ```bash
    streamlit run app.py
    ```

## 📊 Scoring System

The "Strength" metrics are normalized on a 0-3 scale to ensure the radar chart is readable. Raw data is entered, and the Google Sheet calculates the score automatically based on the [Performance Standards] PDF.

| Score | Level | Description |
| :--- | :--- | :--- |
| **0** | Baseline | Starting point |
| **1** | The Standard | Healthy athletic baseline |
| **2** | Elite | High performance |
| **3** | Be A Pro | Exceptional strength |

### Strength Metrics Tracked
* **Trap Bar Deadlift:** Scored vs Bodyweight (1.5x, 1.75x, 2x)
* **Bench Press:** Scored by Reps at BW (10, 15, 20)
* **Pull-Ups:** Scored by Reps (10, 15, 20)
* **Farmer's Carry:** Distance with BW (175, 225, 250 ft)
* **Plank:** Duration (2:00, 2:30, 3:00)
* **Broad Jump:** Distance vs Height (H, H+12", H+24")
* **800m Run:** Time (3:15, 3:00, 2:45)

## 📱 Mobile Usage

For data entry at the gym, use the **Google Form link** pinned to the group chat. Do not try to enter data via the Streamlit dashboard on mobile, as it is optimized for desktop viewing and analysis.