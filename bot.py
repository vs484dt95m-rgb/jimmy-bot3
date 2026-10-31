import time
import feedparser
import requests
import time
import feedparser
import requests

TELEGRAM_TOKEN = "9032544948:AAFm1AVtaOLtcbdxY3Fhqdys-gq-YcC5bkA"
CHANNEL_ID = "@InfoFrancePlus"
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
            lien = entry.link
            
            message = (
                f"⚡️ *FLASH INFO* | **Info France Plus**\n\n"
                f"📰 *{titre}*\n\n"
                f"🔗 [Lire l'article complet]({lien})\n\n"
                f"🔔 _Soyez informés avant tout le monde sur Info France Plus._"
            )
            
            res = envoyer_telegram(message)
            if res and res.get("ok"):
                print(f"Article publié : {titre}")
                articles_publies.add(entry.link)
            else:
                print(f"Échec de l'envoi : {res}")

if __name__ == "__main__":
    print("Le bot Jimmy est lancé !")
    while True:
        verifier_actus()
        time.sleep(CHECK_INTERVAL)