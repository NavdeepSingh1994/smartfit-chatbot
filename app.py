import streamlit as st
import requests
import pandas as pd
from fpdf import FPDF
import tempfile
import os

st.set_page_config(page_title='SmartFit Coaching Report', page_icon="💪")

# OpenRouter API Key
OPENROUTER_API_KEY = "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"

# Session-Init
if "userdata" not in st.session_state:
    st.session_state.userdata = None
if "history" not in st.session_state:
    st.session_state.history = [("Coach", "Hallo! Ich bin dein persönlicher Fitness-Chatbot. Fülle oben deine Daten aus, dann können wir dein Kalorien- und Proteinbedarf berechnen.")]

# BMI-Rechner
def calculate_bmi(weight, height_m):
    return round(weight / (height_m ** 2), 1)

# Kalorien-/Protein-Rechner
def calculate_goals(age, gender, weight, goal_weight, height, workouts, steps, loss_per_week):
    height_cm = height * 100
    gender_const = 5 if gender == "männlich" else -161
    bmr = 10 * weight + 6.25 * height_cm - 5 * age + gender_const
    activity_factor = 1.2 + (workouts * 0.075)
    if steps:
        activity_factor += 0.1
    tdee = bmr * activity_factor
    deficit = loss_per_week * 7700 / 7
    cal_target = tdee - deficit
    protein_target = goal_weight * 2.2
    return round(cal_target), round(protein_target), round(tdee), round(bmr)

# PDF Generator
def create_pdf(userdata):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "SmartFit Coaching Report", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.ln(5)
    for key, value in userdata.items():
        pdf.cell(0, 10, f"{key}: {value}", ln=True)
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_pdf.name)
    return temp_pdf.name

# Chatbot Anfrage
def query_openrouter(prompt, userdata=None):
    system_msg = "You are a multilingual fitness coach. You answer questions about fitness, nutrition, weight loss, training, and related health behavior. Always respond helpfully. If user data is provided, personalize your responses."
    if userdata:
        system_msg += f" User context: age={userdata['Alter']}, gender={userdata['Geschlecht']}, weight={userdata['Gewicht']}kg, height={userdata['Größe']}m, goal={userdata['Zielgewicht']}kg, training={userdata['Krafttraining/Woche']}x per week, calories={userdata['Kalorienziel (kcal)']}, protein={userdata['Proteinziel (g)']}g."
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 300
    }
    try:
        res = requests.post(url, headers=headers, json=body)
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"].strip()
        else:
            return f"❌ Fehler {res.status_code}: {res.text}"
    except Exception as e:
        return f"❌ Verbindungsfehler: {str(e)}"

# Eingabeformular
st.title("💪 SmartFit Coaching Abschlussbericht")

with st.form("input_form"):
    gender = st.radio("Geschlecht", ["männlich", "weiblich"])
    default_weight = 75 if gender == "männlich" else 62
    default_goal = 70 if gender == "männlich" else 58
    default_height = 1.78 if gender == "männlich" else 1.65
    age = st.number_input("Alter", min_value=10, max_value=99, value=30 if gender == "männlich" else 28)
    height = st.number_input("Größe in Metern", value=default_height, step=0.01)
    weight = st.number_input("Aktuelles Gewicht (kg)", min_value=30, max_value=200, step=1, value=default_weight)
    goal_weight = st.number_input("Zielgewicht (kg)", min_value=30, max_value=200, step=1, value=default_goal)
    workouts = st.slider("Krafttraining pro Woche", 0, 7, 3)
    steps = st.checkbox("Ich gehe täglich ca. 10.000 Schritte")
    loss_per_week = st.selectbox("Wie viel kg möchtest du pro Woche verlieren?", [0.25, 0.5, 0.75, 1.0], index=1)
    confirm = st.form_submit_button("✅ Angaben bestätigen")

# Verarbeitung
if confirm:
    bmi = calculate_bmi(weight, height)
    kcal, protein, tdee, bmr = calculate_goals(age, gender, weight, goal_weight, height, workouts, steps, loss_per_week)

    st.session_state.userdata = {
        "Geschlecht": gender,
        "Alter": age,
        "Größe": height,
        "Gewicht": weight,
        "Zielgewicht": goal_weight,
        "Krafttraining/Woche": workouts,
        "10.000 Schritte/Tag": "Ja" if steps else "Nein",
        "Ziel (kg/Woche)": loss_per_week,
        "BMI": bmi,
        "Grundumsatz (BMR)": f"{bmr} kcal",
        "Gesamtumsatz (TDEE)": f"{tdee} kcal",
        "Kalorienziel (kcal)": kcal,
        "Proteinziel (g)": round(protein)
    }

    pdf_path = create_pdf(st.session_state.userdata)
    st.success("✅ Coaching-Werte berechnet. Lade jetzt deinen PDF-Bericht herunter:")
    with open(pdf_path, "rb") as f:
        st.download_button("📄 Coaching-PDF herunterladen", f.read(), file_name="smartfit_coaching.pdf", mime="application/pdf")
    os.remove(pdf_path)

    st.session_state.history = [
        ("Coach", f"Du solltest täglich etwa {kcal} kcal und {round(protein)} g Protein zu dir nehmen, um ca. {loss_per_week} kg pro Woche abzunehmen. Stell mir gerne deine Fragen zu Ernährung oder Training!")
    ]

# Chat
st.divider()
st.subheader("💬 Chat mit dem KI-Coach")

user_input = st.chat_input("Frag mich etwas…")

if user_input:
    reply = query_openrouter(user_input, st.session_state.userdata)
    st.session_state.history.append(("Du", user_input))
    st.session_state.history.append(("Coach", reply))

for i, (speaker, msg) in enumerate(st.session_state.history):
    with st.chat_message("AI" if speaker == "Coach" else "Human"):
        st.markdown(msg)
    if speaker == "Coach":
        st.slider(f"⭐ Bewertung dieser Antwort", 1, 5, 3, key=f"rating_{i}")
