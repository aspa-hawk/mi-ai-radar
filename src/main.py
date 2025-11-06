from flask import Flask, request
import requests
import os
import re

app = Flask(__name__)

# ===== CONFIGURACIÓN =====
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ALLOWED_CHAT_ID = os.getenv("ALLOWED_CHAT_ID")
RADAR_SECRET_KEY = os.getenv("RADAR_SECRET_KEY")

def send_telegram(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        })
    except Exception as e:
        print(f"[TELEGRAM ERROR] {e}")

def query_openai(prompt):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
        "max_tokens": 600
    }
    try:
        r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=20)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
        else:
            return "⚠️ Error al generar análisis."
    except Exception as e:
        return f"⚠️ Error técnico: {str(e)}"

# 🔔 Recibe alertas del radar (GitHub → Replit) y ANALIZA AUTOMÁTICAMENTE
@app.route("/ingest-alert", methods=["POST"])
def ingest_alert():
    auth = request.headers.get("X-Secret-Key")
    if auth != RADAR_SECRET_KEY:
        return "Forbidden", 403
    try:
        data = request.json
        message = data.get("message", "")
        urls = re.findall(r'https?://[^\s\)]+', message)
        if urls:
            analyses = []
            for i, url in enumerate(urls[:4], 1):
                prompt = f"""
Eres un analista de inteligencia en IA, deepfakes y ciberseguridad.
Analiza este enlace: {url}
Responde en este formato exacto:
- Tema: [breve título]
- Impacto: [número entero del 1 al 10]
- Resumen: [2 líneas claras: qué es, por qué es relevante, riesgos o aplicaciones]
"""
                analysis = query_openai(prompt)
                analyses.append(f"{i}. {analysis}\n")
            ranking = "\n".join(analyses)
            response = (
                "🧠 <b>✨ AI Radar Galáctico — Análisis Automático</b>\n\n"
                f"{ranking}\n"
                "💬 ¿Sobre cuál quieres profundizar? Responde con el número o pregúntame cualquier cosa."
            )
            send_telegram(ALLOWED_CHAT_ID, response)
        else:
            send_telegram(ALLOWED_CHAT_ID, message)
        return "OK"
    except Exception as e:
        return f"Error: {e}", 500

# 💬 Responde a tus comandos y analiza enlaces automáticamente
@app.route("/webhook", methods=["POST"])
def telegram_webhook():
    update = request.get_json()
    if not update or "message" not in update:
        return "OK"

    message = update["message"]
    chat_id = str(message["chat"]["id"])
    text = message.get("text", "").strip()

    if chat_id != ALLOWED_CHAT_ID:
        return "OK"

    urls = re.findall(r'https?://[^\s\)]+', text)
    if urls:
        analyses = []
        for i, url in enumerate(urls[:4], 1):
            prompt = f"""
Eres un analista de inteligencia en IA, deepfakes y ciberseguridad.
Analiza este enlace: {url}
Responde en este formato exacto:
- Tema: [breve título]
- Impacto: [número entero del 1 al 10]
- Resumen: [2 líneas claras: qué es, por qué es relevante, riesgos o aplicaciones]
"""
            analysis = query_openai(prompt)
            analyses.append(f"{i}. {analysis}\n")
        ranking = "\n".join(analyses)
        response = (
            "🧠 <b>✨ Análisis Automático</b>\n\n"
            f"{ranking}\n"
            "💬 ¿Sobre cuál quieres profundizar?"
        )
        send_telegram(chat_id, response)
    else:
        response = query_openai(f"Eres un experto en IA y ciberseguridad. Responde: {text}")
        send_telegram(chat_id, response)

    return "OK"

# ✅ Health check
@app.route("/health", methods=["GET"])
def health():
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)