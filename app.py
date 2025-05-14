import streamlit as st
import requests
from fpdf import FPDF
import tempfile
import os

st.set_page_config(page_title='SmartFit Coaching Report', page_icon="💪")

OPENROUTER_API_KEY = "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"

if "userdata" not in st.session_state:
    st.session_state.userdata = None
if "history" not in st.session_state:
    st.session_state.history = [
        ("Coach", "Hallo! Ich bin dein persönlicher Fitness-Chatbot. Fülle oben deine Daten aus, dann kann ich dich besser beraten.")
    ]

def fix_unicode_for_fpdf(text):
    return (
        text.replace("–", "-")
            .replace("’", "'")
            .replace("“", '"')
            .replace("”", '"')
            .replace("…", "...")
            .replace("\u202f", " ")
            .replace("\xa0", " ")
    )

def calculate_bmi(weight, height_m):
    return round(weight / (height_m ** 2), 1)

def calculate_goals(age, gender, weight, goal_weight, height, workouts, steps, goal_change_per_week, goal_type):
    height_cm = height * 100
    gender_const = 5 if gender == "männlich" else -161
    bmr = 10 * weight + 6.25 * height_cm - 5 * age + gender_const
    activity_factor = 1.2 + (workouts * 0.075)
    if steps >= 7000:
        activity_factor += 0.1
    tdee = bmr * activity_factor
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

    empfehlung = [
        "Mind. 3x Krafttraining pro Woche",
        "Proteinaufnahme gleichmäßig verteilen",
        "Kalorienbilanz einhalten (Defizit/Überschuss)",
        "7000+ Schritte pro Tag",
        "2–3 Liter Wasser täglich"
    ]
    pdf.add_block("Empfehlung", empfehlung)

    schluss = [
        "Bleib konsequent und geduldig.",
        "Du bist auf dem richtigen Weg!",
        "Dein SmartFit-Coach"
    ]
    pdf.add_block("Zum Abschluss", schluss)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name)
    return tmp.name

def query_openrouter(prompt, userdata=None):
    # language detection handled above
