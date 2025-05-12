import streamlit as st
import requests

st.set_page_config(page_title='SmartFit Chatbot (Mistral via OpenRouter)', page_icon="💪")

# ✅ OpenRouter API-Key (aktuell öffentlich – später austauschen!)
OPENROUTER_API_KEY = "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"

# 📊 Kalorien-/Proteinrechner
def calculate_goals(age, weight, goal_weight, height, workouts):
    height_cm = height * 100
    bmr = 10 * weight + 6.25 * height_cm - 5 * age + 5
    activity_factor = 1.2 + (workouts * 0.075)
    tdee = bmr * activity_factor
    cal_target = tdee - 500
    protein_target = goal_weight * 2.2
    return round(cal_target), round(protein_target)

# 🤖 Anfrage an OpenRouter senden
def query_openrouter(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {"role": "system", "content": "You are a multilingual fitness coach. Answer clearly and helpfully."},
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

# 🧠 Chatverlauf initialisieren
if "history" not in st.session_state:
    st.session_state.history = [
        ("Coach", "Hallo! Ich bin dein smarter Fitness-Coach. Frag mich alles zu Kalorien, Training oder Ernährung.")
    ]

# 🖼️ UI
st.title("💪 SmartFit Chatbot (Mistral 7B über OpenRouter)")
st.subheader("📊 Kalorien- und Proteinziel berechnen")

with st.form("zielrechner"):
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Alter", value=31)
        height = st.number_input("Größe in m", value=1.74)
    with col2:
        weight = st.number_input("Aktuelles Gewicht (kg)", value=87.0)
        goal_weight = st.number_input("Zielgewicht (kg)", value=78.0)
    workouts = st.slider("Krafttraining/Woche", 0, 7, 3)
    submitted = st.form_submit_button("🎯 Ziel berechnen")

if submitted:
    kcal, protein = calculate_goals(age, weight, goal_weight, height, workouts)
    st.success(f"Kalorienziel: {kcal} kcal/Tag\nProteinziel: {protein} g/Tag")
    st.info("Du kannst unten im Chat weitere Fragen stellen.")

st.divider()
st.subheader("💬 Chat mit dem KI-Coach")

user_input = st.chat_input("Frag mich auf Deutsch oder Englisch…")

if user_input:
    reply = query_openrouter(user_input)
    st.session_state.history.append(("Du", user_input))
    st.session_state.history.append(("Coach", reply))

for speaker, msg in st.session_state.history:
    with st.chat_message("AI" if speaker == "Coach" else "Human"):
        st.markdown(msg)
