#!/usr/bin/env python3
# AI Radar Galáctico v2.0 — Nov 2025
# Monitorea IA, deepfakes, ciberseguridad, tendencias globales y señales desde Antares 🌌

import feedparser
import requests
import json
from datetime import datetime, timedelta
import os

# ===== CONFIGURACIÓN =====
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Palabras clave de ALTA SEÑAL
IMPACT_KEYWORDS = [
    "deepfake", "zero-day", "exploit", "bypass", "launch", "release", "new model",
    "SOTA", "demo", "text-to-video", "video generation", "voice cloning",
    "multimodal", "real-time", "open source", "detection", "AI red teaming",
    "adversarial", "synthetic media", "forgery", "hallucination", "agent",
    "quantum", "Chinese AI", "Kolors", "HunYuan", "ERNIE"
]

# Fuentes RSS globales
RSS_SOURCES = {
    "🤖 Generative AI (Video)": "https://huggingface.co/models?pipeline_tag=text-to-video&sort=modified&rss=true",
    "🖼️ Generative AI (Image)": "https://huggingface.co/models?pipeline_tag=text-to-image&sort=modified&rss=true",
    "🔊 Voice & Audio": "https://huggingface.co/models?pipeline_tag=text-to-speech&sort=modified&rss=true",
    "🌍 Beyond HF (Replicate)": "https://replicate.com/new/feed",
    "🕵️ Deepfakes & Detection": "https://realitydefender.com/blog/rss/",
    "🛡️ MITRE ATLAS": "https://atlas.mitre.org/updates.rss",
    "📜 EU AI Act": "https://digital-strategy.ec.europa.eu/en/rss/ai-act",
    "🔬 arXiv CV": "http://arxiv.org/rss/cs.CV",
    "🔐 arXiv Security": "http://arxiv.org/rss/cs.CR",
    "🌀 Quantum + AI": "http://arxiv.org/rss/quant-ph",
    "🚨 CISA AI Security": "https://www.cisa.gov/news.xml?field_topic_target_id[9751]=9751",
    "📰 AI Policy (Global)": "https://artificialintelligenceact.eu/feed/"
}

def contains_high_signal(text):
    return any(kw in text.lower() for kw in IMPACT_KEYWORDS)

def fetch_rss_alerts(last_hours=24):
    cutoff = datetime.now() - timedelta(hours=last_hours)
    alerts = {}
    for category, url in RSS_SOURCES.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                pub = entry.published_parsed
                if not pub:
                    continue
                pub_date = datetime(*pub[:6])
                if pub_date < cutoff:
                    continue
                title = entry.title[:80] + "..." if len(entry.title) > 80 else entry.title
                link = entry.link
                if contains_high_signal(title + " " + getattr(entry, 'summary', '')):
                    alerts.setdefault(category, []).append(f"• <a href='{link}'>{title}</a>")
        except Exception as e:
            print(f"[RSS ERROR] {category}: {e}")
    return alerts

def scout_github_alerts():
    """Busca repos de IA con tracción reciente"""
    query = "deepfake OR 'voice cloning' OR 'multimodal agent' OR 'AI red teaming' OR 'text-to-video'"
    url = f"https://api.github.com/search/repositories"
    params = {
        "q": f"{query} created:>{(datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')}",
        "sort": "stars",
        "order": "desc",
        "per_page": 5
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        alerts = []
        for repo in data.get("items", []):
            if repo["stargazers_count"] >= 30:  # solo repos con tracción
                desc = repo.get("description", "")[:60]
                alerts.append(f"• <a href='{repo['html_url']}'>{repo['full_name']}</a> ({repo['stargazers_count']} ⭐) — {desc}")
        return alerts
    except Exception as e:
        print(f"[GITHUB ERROR]: {e}")
        return []

def send_telegram_alert(full_alerts):
    if not any(full_alerts.values()):
        print("😴 No high-signal alerts in the last 24h.")
        return

    message = "🌌 <b>AI Radar Galáctico</b> — Nuevas señales (últimas 24h)\n"
    for category, items in full_alerts.items():
        if items:
            message += f"\n🔷 <b>{category}</b>\n" + "\n".join(items)

    if len(message) > 4000:
        message = message[:3994] + "…</a>"

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Alerta galáctica enviada.")
        else:
            print(f"[TELEGRAM ERROR] {response.text}")
    except Exception as e:
        print(f"[TELEGRAM EXCEPTION] {e}")

# ===========================
# Ejecución principal
# ===========================
if __name__ == "__main__":
    print("🌌 Iniciando AI Radar Galáctico...")
    
    # 1. Alertas desde RSS
    alerts = fetch_rss_alerts(last_hours=24)
    
    # 2. Alertas desde GitHub
    github_alerts = scout_github_alerts()
    if github_alerts:
        alerts["🐙 GitHub Trending (IA)"] = github_alerts

    # 3. Enviar todo
    send_telegram_alert(alerts)
