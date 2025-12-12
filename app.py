import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from PIL import Image
import io
import base64
from gutHealth_agent import get_gut_health_advice

# Page config
st.set_page_config(page_title="GutGuardian AI", page_icon="🌿", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    .big-title { font-size: 2.8em; color: #2e7d32; text-align: center; margin-bottom: 0.5em; }
    .subtitle { text-align: center; color: #555; margin-bottom: 2em; }
    .stButton > button { background-color: #4caf50; color: white; border-radius: 8px; padding: 0.5em 1em; }
    .stButton > button:hover { background-color: #388e3c; }
    section[data-testid="stSidebar"] { min-width: 400px; max-width: 400px; }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="big-title">🌿 GutGuardian</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Chat for Personalized Natural Remedies</p>', unsafe_allow_html=True)

# Initialize logs
if "symptom_logs" not in st.session_state:
    st.session_state.symptom_logs = []
if "food_logs" not in st.session_state:
    st.session_state.food_logs = []
if "exercise_logs" not in st.session_state:
    st.session_state.exercise_logs = []
if "water_logs" not in st.session_state:
    st.session_state.water_logs = []
if "sleep_logs" not in st.session_state:
    st.session_state.sleep_logs = []

# Herb image URLs (high-quality, free from Unsplash)
REMEDY_IMAGES = {
    "Ginger": "https://images.unsplash.com/photo-1607451915261-7e0c4e8b2a4c?auto=format&fit=crop&w=800&q=80",
    "Peppermint": "https://images.unsplash.com/photo-1559591935-5d4a2de6a0ed?auto=format&fit=crop&w=800&q=80",
    "Fennel": "https://images.unsplash.com/photo-1624372513586-0d5f7e5f0b6b?auto=format&fit=crop&w=800&q=80",
    "Turmeric": "https://images.unsplash.com/photo-1615485290694-2e80e45e9c0c?auto=format&fit=crop&w=800&q=80",
    "Chamomile": "https://images.unsplash.com/photo-1622045634657-9d2b6b9f3c1d?auto=format&fit=crop&w=800&q=80",
    "Aloe Vera": "https://images.unsplash.com/photo-1546552729-9f0b4e9e8e8e?auto=format&fit=crop&w=800&q=80",
    "Slippery Elm": "https://images.unsplash.com/photo-1583258292670-5e5e3b3f2f3e?auto=format&fit=crop&w=800&q=80",
    "Dandelion": "https://images.unsplash.com/photo-1583258292670-5e5e3b3f2f3e?auto=format&fit=crop&w=800&q=80",
    # Add more as needed
}

# Helper: Image to base64
def image_to_base64(img):
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# Helper: Summarize recent logs for AI
def get_recent_logs_summary():
    summary = "\nRecent User Logs (last 5 each):\n"
    
    if st.session_state.symptom_logs:
        df_sym = pd.DataFrame(st.session_state.symptom_logs).tail(5)
        summary += "Symptoms:\n"
        for _, row in df_sym.iterrows():
            summary += f"- {row['Date']}: {row['Symptom']} (Severity {row['Severity']}/10) — {row['Notes']}\n"
    else:
        summary += "Symptoms: None logged yet.\n"
    
    if st.session_state.food_logs:
        df_food = pd.DataFrame(st.session_state.food_logs).tail(5)
        summary += "Food Intake:\n"
        for _, row in df_food.iterrows():
            photo_desc = f" (Photo: {row['Photo Desc']})" if row.get('Photo Desc') else ""
            summary += f"- {row['Date']}: {row['Meal']} — {row['Foods']}{photo_desc} ({row['Notes']})\n"
    else:
        summary += "Food Intake: None logged yet.\n"
    
    if st.session_state.exercise_logs:
        df_ex = pd.DataFrame(st.session_state.exercise_logs).tail(5)
        summary += "Exercise:\n"
        for _, row in df_ex.iterrows():
            summary += f"- {row['Date']}: {row['Type']} ({row['Duration']} min, Intensity {row['Intensity']}/10) — {row['Notes']}\n"
    else:
        summary += "Exercise: None logged yet.\n"
    
    if st.session_state.water_logs:
        df_water = pd.DataFrame(st.session_state.water_logs).tail(5)
        summary += "Water Intake:\n"
        for _, row in df_water.iterrows():
            summary += f"- {row['Date']}: {row['Amount']} ml — {row['Notes']}\n"
    else:
        summary += "Water Intake: None logged yet.\n"
    
    if st.session_state.sleep_logs:
        df_sleep = pd.DataFrame(st.session_state.sleep_logs).tail(5)
        summary += "Sleep:\n"
        for _, row in df_sleep.iterrows():
            summary += f"- {row['Date']}: {row['Duration']} hours (Quality {row['Quality']}/10) — {row['Notes']}\n"
    else:
        summary += "Sleep: None logged yet.\n"
    
    return summary

# === SIDEBAR: Profile + Collapsible Trackers ===
with st.sidebar:
    st.header("👤 Your Profile")
    age = st.number_input("Age", min_value=1, max_value=120, value=None, placeholder="e.g., 35")
    allergies = st.text_input("Allergies", placeholder="e.g., chamomile, dairy")
    
    st.markdown("---")

    with st.expander("🍽️ Log Food Intake", expanded=False):
        with st.form("food_form", clear_on_submit=True):
            meal = st.selectbox("Meal", ["Breakfast", "Lunch", "Dinner", "Snack"])
            foods = st.text_input("Foods", placeholder="e.g., pasta, cheese")
            photo = st.file_uploader("Upload Photo (optional)", type=["png", "jpg", "jpeg"])
            photo_desc = ""
            if photo:
                img = Image.open(photo)
                st.image(img, caption="Meal photo", width=200)
                photo_desc = st.text_input("Describe photo (for AI)", placeholder="e.g., creamy pasta")
            food_notes = st.text_area("Notes", height=80)
            if st.form_submit_button("Log Meal"):
                entry = {
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Meal": meal,
                    "Foods": foods,
                    "Notes": food_notes,
                    "Photo Desc": photo_desc if photo_desc else "No description"
                }
                if photo:
                    entry["Photo Base64"] = image_to_base64(img)
                st.session_state.food_logs.append(entry)
                st.success("Meal logged!")

    with st.expander("🤢 Log Symptom", expanded=False):
        with st.form("symptom_form", clear_on_submit=True):
            symptom = st.selectbox("Symptom", ["Bloating", "Constipation", "Diarrhea", "Gas", "Heartburn", "Nausea", "Abdominal Pain", "Irregular Bowels", "Other"])
            if symptom == "Other":
                symptom = st.text_input("Custom Symptom")
            severity = st.slider("Severity", 1, 10, 5)
            sym_notes = st.text_area("Notes", height=80)
            if st.form_submit_button("Log Symptom"):
                entry = {
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Symptom": symptom,
                    "Severity": severity,
                    "Notes": sym_notes
                }
                st.session_state.symptom_logs.append(entry)
                st.success("Symptom logged!")

    with st.expander("🏃 Log Exercise", expanded=False):
        with st.form("exercise_form", clear_on_submit=True):
            ex_type = st.selectbox("Type", ["Walking", "Yoga", "Running", "Strength Training", "Pilates", "Cycling", "Swimming", "Other"])
            if ex_type == "Other":
                ex_type = st.text_input("Custom Exercise")
            duration = st.number_input("Duration (min)", min_value=1, value=30)
            intensity = st.slider("Intensity", 1, 10, 5)
            ex_notes = st.text_area("Notes", height=80)
            if st.form_submit_button("Log Exercise"):
                entry = {
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Type": ex_type,
                    "Duration": duration,
                    "Intensity": intensity,
                    "Notes": ex_notes
                }
                st.session_state.exercise_logs.append(entry)
                st.success("Exercise logged!")

    with st.expander("💧 Log Water Intake", expanded=False):
        with st.form("water_form", clear_on_submit=True):
            amount = st.number_input("Amount (ml)", min_value=50, value=500, step=50)
            water_notes = st.text_area("Notes (optional)", height=80)
            if st.form_submit_button("Log Water"):
                entry = {
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Amount": amount,
                    "Notes": water_notes
                }
                st.session_state.water_logs.append(entry)
                st.success(f"{amount} ml logged!")

    with st.expander("😴 Log Sleep", expanded=False):
        with st.form("sleep_form", clear_on_submit=True):
            duration = st.number_input("Sleep Duration (hours)", min_value=0.0, max_value=24.0, value=7.0, step=0.5)
            quality = st.slider("Sleep Quality", 1, 10, 6)
            sleep_notes = st.text_area("Notes", height=80, placeholder="e.g., woke up twice")
            if st.form_submit_button("Log Sleep"):
                entry = {
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Duration": duration,
                    "Quality": quality,
                    "Notes": sleep_notes
                }
                st.session_state.sleep_logs.append(entry)
                st.success(f"{duration} hours logged!")

    st.markdown("---")
    st.warning("Not medical advice. Consult a doctor.")
    st.caption("Data is session-only")

# === MAIN CHAT AREA ===
if any([st.session_state.symptom_logs, st.session_state.food_logs, st.session_state.exercise_logs, 
        st.session_state.water_logs, st.session_state.sleep_logs]):
    with st.expander("📊 View Log History & Trends", expanded=False):
        dfs = []
        if st.session_state.symptom_logs:
            df = pd.DataFrame(st.session_state.symptom_logs)
            df["Type"] = "Symptom"
            dfs.append(df)
        if st.session_state.food_logs:
            df = pd.DataFrame(st.session_state.food_logs)
            df["Type"] = "Food"
            dfs.append(df)
        if st.session_state.exercise_logs:
            df = pd.DataFrame(st.session_state.exercise_logs)
            df["Type"] = "Exercise"
            dfs.append(df)
        if st.session_state.water_logs:
            df = pd.DataFrame(st.session_state.water_logs)
            df["Type"] = "Water"
            dfs.append(df)
        if st.session_state.sleep_logs:
            df = pd.DataFrame(st.session_state.sleep_logs)
            df["Type"] = "Sleep"
            dfs.append(df)
        
        combined = pd.concat(dfs, ignore_index=True, sort=False) if dfs else pd.DataFrame()
        combined = combined.sort_values("Date", ascending=False)
        st.dataframe(combined.drop(columns=["Photo Base64"], errors="ignore"), use_container_width=True)
        
        # Photos
        food_with_photo = [log for log in st.session_state.food_logs if "Photo Base64" in log]
        if food_with_photo:
            st.subheader("Recent Meal Photos")
            cols = st.columns(3)
            for i, log in enumerate(food_with_photo[-6:]):
                with cols[i % 3]:
                    img_bytes = base64.b64decode(log["Photo Base64"])
                    img = Image.open(io.BytesIO(img_bytes))
                    st.image(img, caption=f"{log['Date']} - {log['Meal']}", use_column_width=True)
        
        # Charts
        if st.session_state.symptom_logs:
            sym_df = pd.DataFrame(st.session_state.symptom_logs)
            fig = px.line(sym_df, x="Date", y="Severity", color="Symptom", markers=True, title="Symptom Severity Over Time")
            st.plotly_chart(fig, use_container_width=True)
        if st.session_state.sleep_logs:
            sleep_df = pd.DataFrame(st.session_state.sleep_logs)
            fig = px.bar(sleep_df, x="Date", y="Duration", color="Quality", title="Sleep Duration & Quality")
            st.plotly_chart(fig, use_container_width=True)
        
        if not combined.empty:
            csv = combined.drop(columns=["Photo Base64"], errors="ignore").to_csv(index=False).encode()
            st.download_button("Export All Logs", csv, "gutguardian_logs.csv", "text/csv")

# Helper to extract remedies from AI response
def extract_remedies(response_text):
    remedies = []
    lines = response_text.split('\n')
    for line in lines:
        if line.strip().startswith("Remedy:"):
            parts = line.split(" - Reason:", 1)
            if len(parts) == 2:
                name = parts[0].replace("Remedy:", "").strip()
                reason = parts[1].strip()
                remedies.append((name, reason))
    return remedies

# Chat
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! I'm GutGuardian 🌱\n\nExpand the trackers on the left to log your daily food (with photos!), symptoms, exercise, water, and sleep. I'll analyze everything and suggest safe, natural remedies — especially herbs — with clear reasons and visuals."}
    ]

chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("How's your gut today? Ask for advice..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with chat_container:
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Analyzing your logs and suggesting remedies..."):
                history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
                log_summary = get_recent_logs_summary()
                full_history = [{"role": "system", "content": log_summary}] + history
                
                response = get_gut_health_advice(
                    user_input=prompt,
                    history=full_history,
                    age=age,
                    allergies=allergies
                )
            st.markdown(response)
            
            # Visual Remedy Section
            remedies = extract_remedies(response)
            if remedies:
                st.markdown("### 🌿 Recommended Natural Remedies")
                cols = st.columns(min(len(remedies), 3))  # Max 3 per row
                for i, (name, reason) in enumerate(remedies):
                    with cols[i % len(cols)]:
                        if name in REMEDY_IMAGES:
                            st.image(REMEDY_IMAGES[name], caption=name, use_column_width=True)
                        else:
                            st.image("https://via.placeholder.com/400x300?text=No+Image+Found", caption=name)
                        st.markdown(f"**Why this helps you:** {reason}")
    
    # FIXED LINE: Correct append to session_state.messages
    st.session_state.messages.append({"role": "assistant", "content": response})