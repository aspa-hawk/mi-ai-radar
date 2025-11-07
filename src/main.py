from flask import Flask, request
import requests
import os
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ALLOWED_CHAT_ID = os.getenv("ALLOWED_CHAT_ID")
RADAR_SECRET_KEY = os.getenv("RADAR_SECRET_KEY")

app = Flask(__name__)

def send_telegram(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})
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

def extract_arxiv_abstract(arxiv_id):
    try:
        url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            entry = root.find("{http://www.w3.org/2005/Atom}entry")
            if entry is not None:
                summary = entry.find("{http://www.w3.org/2005/Atom}summary")
                title = entry.find("{http://www.w3.org/2005/Atom}title")
                if summary is not None and title is not None:
                    return title.text.strip(), summary.text.strip()
    except Exception as e:
        print(f"[arXiv Error] {e}")
    return None, None

def extract_generic_content(url):
    try:
        import trafilatura
        downloaded = trafilatura.fetch_url(url)
        text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        if text and len(text) > 100:
            return text[:2000]
    except Exception as e:
        print(f"[Scraping Error] {e}")
    return f"Contenido de {url}."

def get_content_for_url(url):
    parsed = urlparse(url)
    if "arxiv.org" in parsed.netloc:
        path_parts = parsed.path.strip("/").split("/")
        if "abs" in path_parts:
            arxiv_id = path_parts[-1]
            title, abstract = extract_arxiv_abstract(arxiv_id)
            if title and abstract:
                return title, abstract
    content = extract_generic_content(url)
    return f"Contenido de {url}", content

# === Almacenamiento temporal de URLs (para profundizar) ===
temp_urls = {}

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
            global temp_urls
            temp_urls[ALLOWED_CHAT_ID] = urls[:6]  # Guardar hasta 6 URLs
            analyses = []
            for i, url in enumerate(urls[:6], 1):
                title, content = get_content_for_url(url)
                prompt = f"""
Eres un analista de IA y ciberseguridad. Analiza este contenido:

Título: {title}
URL: {url}
Contenido: {content}

Resume en 3 líneas: (1) qué es, (2) por qué es relevante, (3) riesgos o aplicaciones.
Luego, da un puntaje de impacto del 1 al 10.
"""
                analysis = query_openai(prompt)
                analyses.append(f"{i}. {analysis}\n")
            ranking = "\n".join(analyses)
            response = (
                "🧠 <b>✨ AI Radar — Análisis con Scraping Real</b>\n\n"
                f"{ranking}\n"
                "💬 Responde con <b>\"Profundiza sobre la 1\"</b>, <b>\"2\"</b>, etc. para analizar en detalle."
            )
            send_telegram(ALLOWED_CHAT_ID, response)
        else:
            send_telegram(ALLOWED_CHAT_ID, message)
        return "OK"
    except Exception as e:
        return f"Error: {e}", 500

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

    # Comando para profundizar
    if text.lower().startswith("profundiza sobre la"):
        try:
            num = int(text.split()[-1])
            urls = temp_urls.get(chat_id, [])
            if 1 <= num <= len(urls):
                selected_url = urls[num - 1]
                title, content = get_content_for_url(selected_url)
                prompt = f"""
Eres un experto en IA y ciberseguridad. Profundiza en este tema:

Título: {title}
URL: {selected_url}
Contenido: {content}

Responde con:
- Explicación técnica detallada
- Aplicaciones prácticas
- Riesgos o ventajas
- Recomendaciones para mitigar riesgos
"""
                analysis = query_openai(prompt)
                send_telegram(chat_id, f"🔍 <b>Profundización sobre Noticia {num}</b>\n\n{analysis}")
            else:
                send_telegram(chat_id, "⚠️ Número inválido. Elige entre 1 y 6.")
        except Exception as e:
            send_telegram(chat_id, "⚠️ Usa el formato: \"Profundiza sobre la 1\"")
        return "OK"

    # Análisis de enlaces en mensajes manuales
    urls = re.findall(r'https?://[^\s\)]+', text)
    if urls:
        temp_urls[chat_id] = urls[:6]
        analyses = []
        for i, url in enumerate(urls[:6], 1):
            title, content = get_content_for_url(url)
            prompt = f"""
Eres un analista de IA y ciberseguridad. Analiza este contenido:

Título: {title}
URL: {url}
Contenido: {content}

Resume en 3 líneas: (1) qué es, (2) por qué es relevante, (3) riesgos o aplicaciones.
Luego, da un puntaje de impacto del 1 al 10.
"""
            analysis = query_openai(prompt)
            analyses.append(f"{i}. {analysis}\n")
        ranking = "\n".join(analyses)
        response = (
            "🧠 <b>✨ Análisis con Scraping Real</b>\n\n"
            f"{ranking}\n"
            "💬 Responde con <b>\"Profundiza sobre la 1\"</b>, <b>\"2\"</b>, etc."
        )
        send_telegram(chat_id, response)
    else:
        response = query_openai(f"Eres un experto en IA. Responde: {text}")
        send_telegram(chat_id, response)
    return "OK"

@app.route("/health", methods=["GET"])
def health():
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
