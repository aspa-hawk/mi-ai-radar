#!/usr/bin/env python3
# AI Radar Pro + Telegram — Nov 2025
# Alertas en tiempo real sobre IA, deepfakes, ciberseguridad y multimedia

import feedparser
import requests
from datetime import datetime, timedelta
import os

# ===== CONFIGURACIÓN =====
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "TU_TOKEN_AQUI")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "TU_CHAT_ID_AQUI")

IMPACT_KEYWORDS = [
    "deepfake", "zero-day", "exploit", "bypass", "launch", "release", "new model",
    "SOTA", "demo", "text-to-video", "video generation", "voice cloning",
    "generative video", "multimodal", "real-time", "open source", "detection",
    "AI security", "adversarial", "synthetic media", "forgery", "hallucination"
]

SOURCES = {
    "🤖 Generative AI (Video)": "https://huggingface.co/models?pipeline_tag=text-to-video&sort=modified&rss=true",
    "🖼️ Generative AI (Image)": "https://huggingface.co/models?pipeline_tag=text-to-image&sort=modified&rss=true",
    "🔊 Audio & Voice": "https://huggingface.co/models?pipeline_tag=text-to-speech&sort=modified&rss=true",
    "🕵️ Deepfakes & Media": "https://realitydefender.com/blog/rss/",
    "🛡️ AI Cybersecurity": "https://feeds.feedburner.com/TheHackersNews",
    "📜 AI Policy & Ethics": "https://artificialintelligenceact.eu/feed/",
    "🚀 AI Startups": "https://www.producthunt.com/topics/ai/feed",
    "🔬 Research (CV)": "http://arxiv.org/rss/cs.CV",
    "🔐 Research (Security)": "http://arxiv.org/rss/cs.CR"
}

def contains_high_signal(text):
    return any(kw in text.lower() for kw in IMPACT_KEYWORDS)

def fetch_alerts(last_hours=24):
    cutoff = datetime.now() - timedelta(hours=last_hours)
    alerts = {}

    for category, url in SOURCES.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                pub_date = datetime(*entry.published_parsed[:6]) if entry.published_parsed else datetime.min
                if pub_date < cutoff:
                    continue

                title = entry.title[:80] + "..." if len(entry.title) > 80 else entry.title
                link = entry.link

                if contains_high_signal(title + " " + getattr(entry, 'summary', '')):
                    if category not in alerts:
                        alerts[category] = []
                    alerts[category].append(f"• <a href='{link}'>{title}</a>")
        except Exception as e:
            print(f"[ERROR] {category}: {e}")
    return alerts

def send_telegram_alert(alerts):
    if not alerts:
        print("😴 No high-signal alerts in the last 24h.")
        return

    message = "🔍 <b>AI Radar Pro</b> — Nuevas señales de impacto (últimas 24h)\n"
    for category, items in alerts.items():
        message += f"\n🔷 <b>{category}</b>\n" + "\n".join(items)

    # Limitar a 4096 caracteres (máximo de Telegram)
    if len(message) > 4096:
        message = message[:4090] + "…</a>"

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ Alerta enviada por Telegram.")
        else:
            print(f"[TELEGRAM ERROR] {response.text}")
    except Exception as e:
        print(f"[TELEGRAM EXCEPTION] {e}")

# ===========================
# 🧪 PRUEBA MANUAL (borra esta sección después de probar)
# ===========================
if __name__ == "__main__":
    print("✅ Script ejecutado correctamente. Enviando mensaje de prueba a Telegram...")
    send_telegram_alert({"✅ Test": ["• Este es un mensaje de prueba"]})
    exit()  # Detener aquí para la prueba
