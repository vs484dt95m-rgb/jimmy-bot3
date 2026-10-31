import time
import feedparser
import requests
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "9032544948:AAFm1AVtaOLtcbdxY3Fhqdys-gq-YcC5bkA")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@InfoFrancePlus")
RSS_URL = "https://www.lefigaro.fr/rss/figaro_actualites.xml"
CHECK_INTERVAL = 300

articles_publies = set()

def envoyer_telegram(texte):
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

def verifier_actus():
    print("Vérification des nouvelles actualités...")
    feed = feedparser.parse(RSS_URL)
    
    for entry in reversed(feed.entries[:5]):
        if entry.link not in articles_publies:
            titre = entry.title
            
            message = (
                f"⚡️ *FLASH INFO* | **Info France Plus**\n\n"
                f"📰 *{titre}*\n\n"
                f"🔔 _Soyez informés avant tout le monde sur Info France Plus._"
            )
            
            res = envoyer_telegram(message)
            if res and res.get("ok"):
                print(f"Article publié : {titre}")
                articles_publies.add(entry.link)
            else:
                print(f"Échec de l'envoi : {res}")

# Serveur HTTP minimal pour que Render détecte un port
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
    # Lance le serveur HTTP en arrière-plan
    threading.Thread(target=run_server, daemon=True).start()
    
    while True:
        verifier_actus()
        time.sleep(CHECK_INTERVAL)
