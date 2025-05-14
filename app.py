import streamlit as st
import requests
from fpdf import FPDF
import tempfile
import os

st.set_page_config(page_title='SmartFit Coaching Report', page_icon="💪")

OPENROUTER_API_KEY = "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"

# === Session State initialisieren ===
if "userdata" not in st.session_state:
    st.session_state.userdata = None
if "history" not in st.session_state:
    st.session_state.history = [
        ("Coach", "Hallo! Ich bin dein persönlicher Fitness-Chatbot. Fülle oben deine Daten aus, dann kann ich dich besser beraten.")
    ]

# === Hilfsfunktionen ===
def fix_unicode_for_fpdf(text):
    return text.replace("–", "-").replace("’", "'").replace("“", '"').replace("”", '"').replace("…", "...").replace("\u202f", " ").replace("\xa0", " ")

def calculate_bmi(weight, height_m):
    return round(weight / (height_m ** 2), 1)

def calculate_goals(age, gender, weight, goal_weight, height, workouts, steps, goal_change_per_week, goal_type):
    if gender == "männlich":
        bmr = 66.47 + (13.7 * weight) + (5.0 * height * 100) - (6.8 * age)
    else:
        bmr = 655.1 + (9.6 * weight) + (1.8 * height * 100) - (4.7 * age)

    # PAL basiert nur auf Schritten + Workouts
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
    if goal_type == "abnehmen":
        cal_target = tdee - delta
    else:
        cal_target = tdee + delta

    protein_target = goal_weight * 2.0
    return round(cal_target), round(protein_target), round(tdee), round(bmr)

class StyledPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.set_text_color(40, 40, 40)
        self.cell(0, 10, "SmartFit Coaching Report", ln=True, align="C")
        self.ln(5)

    def add_block(self, title, lines):
        self.set_font("Arial", "B", 11)
        self.set_text_color(0, 102, 204)
        self.cell(0, 8, title, ln=True)
        self.set_font("Arial", "", 10)
        self.set_text_color(0)
        for line in lines:
            self.cell(0, 7, fix_unicode_for_fpdf(line), ln=True)
        self.ln(2)

    def add_highlight(self, label, value, unit=""):
        self.set_fill_color(240, 240, 255)
        self.set_text_color(0)
        self.set_font("Arial", "B", 11)
        self.cell(50, 8, f"{label}:", 0, 0, 'L', True)
        self.set_font("Arial", "", 11)
        self.cell(0, 8, f"{value} {unit}", 0, 1, 'L', True)

def create_pdf(userdata):
    pdf = StyledPDF()
    pdf.add_page()
    pdf.add_block("Einleitung", [
        "Vielen Dank, dass du dich für SmartFit entschieden hast.",
        "Hier ist dein individueller Fitness-Überblick auf einen Blick."
    ])
    werte = [f"{key}: {value}" for key, value in userdata.items() if key not in ["Kalorienziel (kcal)", "Proteinziel (g)", "BMI"]]
    pdf.add_block("Deine Angaben", werte)
    pdf.add_block("Wichtige Ziele", ["Diese Kennzahlen sind entscheidend für dein Ziel:"])
    pdf.add_highlight("Kalorienziel", userdata["Kalorienziel (kcal)"], "kcal")
    pdf.add_highlight("Proteinziel", userdata["Proteinziel (g)"], "g")
    pdf.add_highlight("BMI", userdata["BMI"])
    pdf.add_block("Empfehlung", [
        "Mind. 3x Krafttraining pro Woche",
        "Proteinaufnahme gleichmäßig verteilen",
        "Kalorienbilanz einhalten (Defizit/Überschuss)",
        "7000+ Schritte pro Tag",
        "2–3 Liter Wasser täglich"
    ])
    pdf.add_block("Zum Abschluss", [
        "Bleib konsequent und geduldig.",
        "Du bist auf dem richtigen Weg!",
        "Dein SmartFit-Coach"
    ])
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name)
    return tmp.name

def query_openrouter(prompt, userdata=None):
    language = "German" if userdata else "English"
    system_msg = f"You are a helpful multilingual fitness coach. Reply only in {language}. You answer questions about fitness, nutrition, weight loss, weight gain, training, and behavior change. Personalize answers if user data is available."
    if userdata:
        system_msg += f" Context: age={userdata['Alter']}, gender={userdata['Geschlecht']}, weight={userdata['Gewicht']}kg, height={userdata['Größe']}m, goal={userdata['Zielgewicht']}kg, training={userdata['Krafttraining/Woche']}x, steps={userdata['Schritte/Tag']}, calories={userdata['Kalorienziel (kcal)']}, protein={userdata['Proteinziel (g)']}g."
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [{"role": "system", "content": system_msg}, {"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 800
    }
    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body)
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"].strip()
        else:
            return f"❌ Fehler {res.status_code}: {res.text}"
    except Exception as e:
        return f"❌ Verbindungsfehler: {str(e)}"

# === UI ===
st.title("SmartFit Coaching")

with st.form("input_form"):
    gender = st.radio("Geschlecht", ["männlich", "weiblich"])
    age = st.number_input("Alter", min_value=10, max_value=99, value=30)
    height = st.number_input("Größe in m", value=1.75, step=0.01)
    weight = st.number_input("Gewicht (kg)", value=85, step=1)
    goal_weight = st.number_input("Zielgewicht (kg)", value=78, step=1)
    workouts = st.slider("Krafttraining pro Woche", 0, 7, 3)
    steps = st.slider("Schritte pro Tag", 0, 20000, 10000, step=500)
    goal_type = st.radio("Was ist dein Ziel?", ["abnehmen", "zunehmen"])
    goal_change = st.selectbox("Wieviel kg pro Woche?", [0.25, 0.5, 0.75, 1.0], index=1)
    confirm = st.form_submit_button("Angaben bestätigen")

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

    pdf_path = create_pdf(st.session_state.userdata)
    st.success("✅ PDF wurde erfolgreich erstellt.")
    with open(pdf_path, "rb") as f:
        st.download_button("📄 Coaching-PDF herunterladen", f.read(), file_name="smartfit_report.pdf", mime="application/pdf")

    # Dynamische Willkommensnachricht mit Kontext
    delta = round(tdee - kcal)
    balance_text = f"ein Kaloriendefizit von {abs(delta)} kcal" if goal_type == "abnehmen" else f"einen Kalorienüberschuss von {delta} kcal"
    welcome_msg = (
        f"Danke für deine Angaben! Du wiegst {weight} kg bei {height} m Größe und möchtest {goal_type} auf {goal_weight} kg.\n\n"
        f"Dein Kalorienziel liegt bei **{kcal} kcal**, das entspricht {balance_text}.\n"
        f"Du machst **{workouts}x Krafttraining pro Woche** und gehst täglich etwa **{steps} Schritte**.\n\n"
        f"Stell mir jetzt gerne Fragen zu Ernährung, Training oder Fortschritt – ich bin bereit! 💪"
    )
    st.session_state.history.append(("Coach", welcome_msg))


# === Chatbereich ===
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
