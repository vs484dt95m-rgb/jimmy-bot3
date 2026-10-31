import time
import feedparser
import requests
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "9032544948:AAFm1AVtaOLtcbdxY3Fhqdys-gq-YcC5bkA")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@InfoFrancePlus")

# Liste des flux RSS avec nom de la source
RSS_FEEDS = [
    {"url": "https://feeds.leparisien.fr/leparisien/rss", "source": "Le Parisien"},
    {"url": "https://www.bfmtv.com/rss/news-24-7/", "source": "BFMTV"},
    {"url": "https://www.lemonde.fr/rss/en_continu.xml", "source": "Le Monde"}
]

CHECK_INTERVAL = 300  # 5 minutes
articles_publies = set()

def envoyer_telegram(texte, image_url=None):
    if image_url:
        # Envoi avec image
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        payload = {
            "chat_id": CHANNEL_ID,
            "photo": image_url,
            "caption": texte,
            "parse_mode": "Markdown"
        }
    else:
        # Envoi texte seul
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHANNEL_ID,
            "text": texte,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False
        }
    
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Erreur d'envoi : {e}")

def get_image_url(entry):
    """Essaie de récupérer une image depuis le flux RSS"""
    # Enclosure (souvent utilisé pour les images)
    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            if enc.get("type", "").startswith("image"):
                return enc.get("href")
    
    # media_content
    if hasattr(entry, "media_content") and entry.media_content:
        return entry.media_content[0].get("url")
    
    # media_thumbnail
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        return entry.media_thumbnail[0].get("url")
    
    return None

def verifier_actus():
    print("Vérification des nouvelles actualités...")
    for feed_info in RSS_FEEDS:
        rss_url = feed_info["url"]
        source = feed_info["source"]
        
        try:
            feed = feedparser.parse(rss_url)
            print(f"Flux {source} → {len(feed.entries)} articles")
            
            for entry in reversed(feed.entries[:5]):
                if entry.link not in articles_publies:
                    titre = entry.title
                    lien = entry.link
                    image_url = get_image_url(entry)
                    
                    message = (
                        f"⚡️ *FLASH INFO* | **Info France Plus**\n\n"
                        f"📰 *{titre}*\n\n"
                        f"📰 Source : *{source}*\n"
                        f"🔗 [Lire l'article]({lien})\n\n"
                        f"🔔 _Soyez informés avant tout le monde sur Info France Plus._"
                    )
                    
                    res = envoyer_telegram(message, image_url)
                    if res and res.get("ok"):
                        print(f"Article publié : {titre} ({source})")
                        articles_publies.add(entry.link)
                    else:
                        print(f"Échec de l'envoi : {res}")
        except Exception as e:
            print(f"Erreur sur le flux {source} : {e}")

# Serveur HTTP minimal pour Render
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Jimmy bot is alive")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"Serveur keep-alive sur le port {port}")
    server.serve_forever()

if __name__ == "__main__":
    print("Le bot Jimmy est lancé !")
    threading.Thread(target=run_server, daemon=True).start()
    
    while True:
        verifier_actus()
        time.sleep(CHECK_INTERVAL)
