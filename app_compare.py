import streamlit as st
import requests
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# === FLAN-T5 Setup (lokal)
@st.cache_resource
def load_flan_t5():
    tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-base")
    model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-base")
    return model, tokenizer

flan_model, flan_tokenizer = load_flan_t5()

# === OpenRouter Mistral-7B Setup
OPENROUTER_API_KEY = "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"
OPENROUTER_MODEL = "mistralai/mistral-7b-instruct"

def query_openrouter(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": "You are a multilingual fitness assistant. Answer clearly and helpfully."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 300
    }
    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body)
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"].strip()
        else:
            return f"❌ OpenRouter Error {res.status_code}: {res.text}"
    except Exception as e:
        return f"❌ Connection Error: {str(e)}"

def query_flan(prompt):
    inputs = flan_tokenizer(prompt, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = flan_model.generate(**inputs, max_new_tokens=150)
    return flan_tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

# === UI ===
st.set_page_config(page_title="Modelvergleich: Mistral vs. FLAN-T5", page_icon="🤖")
st.title("🤖 Vergleich: Mistral-7B (via OpenRouter) vs. flan-T5 (lokal)")

user_input = st.text_area("Gib eine Frage auf Deutsch oder Englisch ein:")

if st.button("Antworten vergleichen"):
    if not user_input.strip():
        st.warning("Bitte gib eine Frage ein.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🧠 Mistral-7B (OpenRouter)")
            st.write(query_openrouter(user_input))

        with col2:
            st.subheader("🧪 flan-T5 (lokal)")
            st.write(query_flan(user_input))
