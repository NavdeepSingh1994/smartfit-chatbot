# app.py - SmartFit – Chatfirst mit automatischer Lebensmittelanalyse

import streamlit as st
import requests
from fpdf import FPDF
from dotenv import load_dotenv
import tempfile
import os
import pandas as pd

st.set_page_config(page_title='SmartFit Coaching Report', page_icon="💪")

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
NUTRI_APP_ID = os.getenv("NUTRI_APP_ID")
NUTRI_API_KEY = os.getenv("NUTRI_API_KEY")

if "userdata" not in st.session_state:
    st.session_state.userdata = None
if "history" not in st.session_state:
    st.session_state.history = []
if "ratings" not in st.session_state:
    st.session_state.ratings = []
if "pdf_ready" not in st.session_state:
    st.session_state.pdf_ready = None

# === FUNKTIONEN ===
def calculate_bmi(weight, height_m):
    return round(weight / (height_m ** 2), 1)

def calculate_goals(age, gender, weight, goal_weight, height, workouts, steps, goal_change_per_week, goal_type):
    if gender == "männlich":
        bmr = 66.47 + (13.7 * weight) + (5.0 * height * 100) - (6.8 * age)
    else:
        bmr = 655.1 + (9.6 * weight) + (1.8 * height * 100) - (4.7 * age)
    if steps >= 12000:
        pal = 1.8
    elif steps >= 10000:
        pal = 1.6
    elif steps >= 8000:
        pal = 1.4
    elif steps >= 5000:
        pal = 1.3
    else:
        pal = 1.2
    pal += workouts * 0.05
    tdee = bmr * pal
    delta = goal_change_per_week * 7700 / 7
    cal_target = tdee - delta if goal_type == "abnehmen" else tdee + delta
    protein_target = goal_weight * 2.0
    return round(cal_target), round(protein_target), round(tdee), round(bmr)

def create_pdf(userdata):
    def fix_unicode(text):
        return text.replace("–", "-").replace("’", "'").replace("“", '"').replace("”", '"').replace("…", "...").replace(" ", " ").replace(" ", " ")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 10, "SmartFit Coaching Report", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 10, fix_unicode("Vielen Dank, dass du dich für SmartFit entschieden hast.\n\nHier ist dein individueller Fitness-Überblick auf einen Blick."))
    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(0, 102, 204)
    pdf.cell(0, 10, "Deine Angaben", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(0)
    for key, val in userdata.items():
        if key not in ["Kalorienziel (kcal)", "Proteinziel (g)", "BMI"]:
            pdf.cell(0, 8, fix_unicode(f"{key}: {val}"), ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(0, 102, 204)
    pdf.cell(0, 10, "Wichtige Ziele", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(0)
    pdf.cell(0, 8, fix_unicode(f"Kalorienziel: {userdata['Kalorienziel (kcal)']} kcal"), ln=True)
    pdf.cell(0, 8, fix_unicode(f"Proteinziel: {userdata['Proteinziel (g)']} g"), ln=True)
    pdf.cell(0, 8, fix_unicode(f"BMI: {userdata['BMI']}"), ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(0, 102, 204)
    pdf.cell(0, 10, "Empfehlung", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(0)
    for line in ["Mind. 3x Krafttraining pro Woche", "Proteinaufnahme gleichmäßig verteilen", "Kalorienbilanz einhalten", "7000+ Schritte pro Tag", "2-3 Liter Wasser täglich"]:
        pdf.cell(0, 8, fix_unicode(f"- {line}"), ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(0, 102, 204)
    pdf.cell(0, 10, "Zum Abschluss", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(0)
    pdf.multi_cell(0, 8, fix_unicode("Bleib konsequent und geduldig.\nDu bist auf dem richtigen Weg!\n\nDein SmartFit-Coach"))
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name)
    return tmp.name

with st.sidebar:
    st.title("ℹ️ Was kann SmartFit?")
    st.markdown("""
    - 💪 Kalorien- & Proteinberechnung
    - 🏋️‍♂️ Trainings- & Ernährungsberatung
    - 🍽 Lebensmittelanalyse per Chat
    - 📊 Tageszielvergleich automatisch
    - 🧾 PDF-Bericht & CSV-Bewertung
    """)

st.title("💪 SmartFit")

with st.form("input_form"):
    st.subheader("📅 Deine Daten")
    gender = st.radio("Geschlecht", ["männlich", "weiblich"])
    age = st.number_input("Alter", min_value=10, max_value=99, value=30)
    height = st.number_input("Größe in m", value=1.75, step=0.01)
    weight = st.number_input("Gewicht (kg)", value=85, step=1)
    goal_weight = st.number_input("Zielgewicht (kg)", value=78, step=1)
    workouts = st.slider("Krafttraining pro Woche", 0, 7, 3)
    steps = st.slider("Schritte pro Tag", 0, 20000, 10000, step=500)
    goal_type = st.radio("Was ist dein Ziel?", ["abnehmen", "zunehmen"])
    goal_change = st.selectbox("Wieviel kg pro Woche?", [0.25, 0.5, 0.75, 1.0], index=1)
    confirm = st.form_submit_button("✅ Angaben bestätigen")

if confirm:
    bmi = calculate_bmi(weight, height)
    kcal, protein, tdee, bmr = calculate_goals(age, gender, weight, goal_weight, height, workouts, steps, goal_change, goal_type)
    st.session_state.userdata = {
        "Geschlecht": gender,
        "Alter": age,
        "Größe": height,
        "Gewicht": weight,
        "Zielgewicht": goal_weight,
        "Krafttraining/Woche": workouts,
        "Schritte/Tag": steps,
        "Ziel": goal_type,
        "Zielveränderung (kg/Woche)": goal_change,
        "BMI": bmi,
        "Grundumsatz (BMR)": f"{bmr} kcal",
        "Gesamtumsatz (TDEE)": f"{tdee} kcal",
        "Kalorienziel (kcal)": kcal,
        "Proteinziel (g)": round(protein)
    }
    st.session_state.history = []
    st.session_state.history.append(("Coach", f"Danke für deine Angaben! Du wiegst {weight} kg bei {height} m Größe und möchtest {goal_type} auf {goal_weight} kg.\n\nDein Kalorienziel liegt bei {kcal} kcal, dein Proteinbedarf bei {round(protein)} g. Du machst {workouts}x Krafttraining/Woche und gehst etwa {steps} Schritte am Tag.\n\nStell mir jetzt Fragen zu Training, Essen oder Fortschritt. 📊"))
    st.session_state.pdf_ready = create_pdf(st.session_state.userdata)

if st.session_state.pdf_ready:
    with open(st.session_state.pdf_ready, "rb") as f:
        st.download_button("📄 Coaching-PDF herunterladen", f.read(), file_name="smartfit_report.pdf", mime="application/pdf")

# === CHAT MIT AUTOMATISCHER ERNÄHRUNGSERKENNUNG ===
st.subheader("💬 Chat mit dem KI-Coach")

def ask_mistral(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    system_prompt = (
        "Du bist ein präziser, sympathischer Fitness- und Ernährungsexperte. "
        "Sprich den Nutzer direkt an, sei motivierend und antworte auf Deutsch. "
        "Gib konkrete Empfehlungen zu Training, Ernährung und Fortschritt. "
        "Wenn möglich, berechne grob Kalorien, Protein oder Trainingsvolumen. "
        "Sei niemals vage oder langatmig – Klarheit vor Stil!"
    )
    payload = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def handle_nutritionix(prompt):
    headers = {
        "x-app-id": NUTRI_APP_ID,
        "x-app-key": NUTRI_API_KEY,
        "x-remote-user-id": "0"
    }
    body = {"query": prompt, "timezone": "Europe/Vienna"}
    try:
        res = requests.post("https://trackapi.nutritionix.com/v2/natural/nutrients", json=body, headers=headers)
        res.raise_for_status()
        data = res.json()
        total = {"Kalorien": 0, "Protein": 0, "Fett": 0, "Kohlenhydrate": 0}
        antwort = []
        for f in data["foods"]:
            antwort.append(f"🍽 **{f['food_name'].title()}**: {round(f['nf_calories'])} kcal, {round(f['nf_protein'], 1)} g Protein")
            total["Kalorien"] += f['nf_calories']
            total["Protein"] += f['nf_protein']
            total["Fett"] += f['nf_total_fat']
            total["Kohlenhydrate"] += f['nf_total_carbohydrate']

        ziel = st.session_state.userdata
        kcal_diff = round(total["Kalorien"] - ziel["Kalorienziel (kcal)"])
        prot_diff = round(total["Protein"] - ziel["Proteinziel (g)"])
        status = f"\n\n📊 **Tagesbilanz:** {round(total['Kalorien'])} kcal, {round(total['Protein'],1)} g Protein\n"
        status += f"⚖️ Abweichung: {kcal_diff:+} kcal, {prot_diff:+} g Protein"
        if prot_diff < -20:
            status += "\n🔴 Du hast zu wenig Protein gegessen."
        elif prot_diff >= 0:
            status += "\n✅ Proteinbedarf gedeckt."
        return "\n".join(antwort) + status
    except:
        return None

user_input = st.chat_input("Frag mich etwas…")

if user_input:
    st.session_state.history.append(("Du", user_input))
    with st.spinner("Coach denkt nach..."):
        if any(word in user_input.lower() for word in ["gegessen", "frühstück", "mittag", "abend", "ich habe heute"]):
            reply = handle_nutritionix(user_input)
            if not reply:
                reply = "❌ Ich konnte deine Angaben leider nicht analysieren."
        else:
            try:
                reply = ask_mistral(user_input)
            except Exception as e:
                reply = f"Fehler: {e}"
    st.session_state.history.append(("Coach", reply))

for i, (speaker, msg) in enumerate(st.session_state.history):
    with st.chat_message("AI" if speaker == "Coach" else "Human"):
        st.markdown(msg)
    if speaker == "Coach" and i > 0:
        rating = st.slider(f"⭐ Bewertung dieser Antwort", 1, 5, 3, key=f"rating_{i}")
        if len(st.session_state.ratings) < (i // 2):
            st.session_state.ratings.append(rating)

if st.session_state.ratings and st.session_state.userdata:
    export_data = {
        "Antwort": [msg for spk, msg in st.session_state.history if spk == "Coach" and msg != st.session_state.history[0][1]],
        "Bewertung": st.session_state.ratings
    }
    df = pd.DataFrame(export_data)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📅 Bewertungen als CSV exportieren", csv, "antworten_bewertungen.csv", "text/csv")
