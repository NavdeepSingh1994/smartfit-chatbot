import streamlit as st
import openai
import requests
import os
from dotenv import load_dotenv

st.set_page_config(page_title="Mistral vs. ChatGPT Vergleich", page_icon="🤖")

# .env explizit laden
load_dotenv(dotenv_path=".env")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY


st.title("🤖 Vergleich: Mistral-7B vs. ChatGPT")

user_input = st.text_area("Stelle eine Frage zum Thema Fitness oder Ernährung:")

if st.button("Antworten vergleichen") and user_input:
    with st.spinner("Antworten werden generiert..."):

        # === Anfrage an OpenRouter (Mistral) ===
        mistral_headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        mistral_data = {
            "model": "mistralai/mistral-7b-instruct",
            "messages": [
                {"role": "system", "content": "Du bist ein Fitness- und Ernährungscoach. Antworte nur auf solche Fragen."},
                {"role": "user", "content": user_input}
            ]
        }

        try:
            mistral_response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=mistral_headers,
                json=mistral_data,
                timeout=30
            )

            if mistral_response.status_code == 200:
                mistral_json = mistral_response.json()
                mistral_text = mistral_json.get("choices", [{}])[0].get("message", {}).get("content", "Keine Antwort erhalten.")
            else:
                mistral_text = f"Fehler {mistral_response.status_code}: {mistral_response.text}"

        except requests.exceptions.RequestException as e:
            mistral_text = f"Netzwerkfehler bei Mistral: {e}"

        # === Anfrage an ChatGPT (GPT-4) ===
        try:
            chatgpt_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Du bist ein Fitness- und Ernährungscoach. Antworte nur auf solche Fragen."},
                    {"role": "user", "content": user_input}
                ]
            )
            chatgpt_text = chatgpt_response.choices[0].message.content
        except Exception as e:
            chatgpt_text = f"Fehler bei ChatGPT: {e}"

        # === GPT-gestützter Vergleich beider Antworten ===
        vergleichs_prompt = f"""
Hier sind zwei Antworten auf die Nutzerfrage:

Frage: {user_input}

Antwort von Mistral:
{mistral_text}

Antwort von ChatGPT:
{chatgpt_text}

Bitte bewerte beide Antworten hinsichtlich Qualität, Korrektheit und Nützlichkeit im Kontext von Fitness und Ernährung. Gib eine klare Empfehlung, welche besser ist und warum.
"""

        try:
            analyse_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Du bist ein erfahrener KI-Analyst für Fitness- und Ernährungsantworten."},
                    {"role": "user", "content": vergleichs_prompt}
                ]
            )
            gpt_analysis = analyse_response.choices[0].message.content
        except Exception as e:
            gpt_analysis = f"Fehler bei der GPT-Analyse: {e}"

        # === Anzeige der Ergebnisse ===
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("💬 Mistral-7B")
            st.write(mistral_text)

        with col2:
            st.subheader("💬 ChatGPT (GPT-4)")
            st.write(chatgpt_text)

        # === Bewertung durch Benutzer ===
        st.markdown("---")
        st.write("🔍 Welche Antwort war hilfreicher?")
        better = st.radio("Deine Bewertung", ["Mistral-7B", "ChatGPT (GPT-4)", "Beide gleich gut", "Keine hilfreich"], key="rating")

        st.success(f"Danke für deine Bewertung: {better}")

        # === GPT-Vergleich anzeigen ===
        st.markdown("---")
        st.subheader("🤖 GPT-Analyse der Antworten")
        st.write(gpt_analysis)
