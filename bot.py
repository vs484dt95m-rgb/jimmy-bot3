import time
import feedparser
import requests
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import re

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "9032544948:AAFm1AVtaOLtcbdxY3Fhqdys-gq-YcC5bkA")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@InfoFrancePlus")

# Liste des flux RSS avec nom de la source
RSS_FEEDS = [
    {"url": "https://feeds.leparisien.fr/leparisien/rss", "source": "Le Parisien"},
    {"url": "https://www.bfmtv.com/rss/news-24-7/", "source": "BFMTV"},
    {"url": "https://www.lemonde.fr/rss/en_continu.xml", "source": "Le Monde"},
    {"url": "https://www.humanite.fr/rss", "source": "L'Humanité"},
    {"url": "https://www.rfi.fr/fr/rss", "source": "RFI"},
    {"url": "https://www.liberation.fr/arc/outboundfeeds/rss/", "source": "Libération"},
    {"url": "https://www.mediapart.fr/articles/feed", "source": "Mediapart"},
]

CHECK_INTERVAL = 300  # 5 minutes
articles_publies = set()

def envoyer_telegram(texte, image_url=None):
    if image_url:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        payload = {
            "chat_id": CHANNEL_ID,
            "photo": image_url,
            "caption": texte,
            "parse_mode": "Markdown"
        }
    else:
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
    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            if enc.get("type", "").startswith("image"):
                return enc.get("href")
    
    if hasattr(entry, "media_content") and entry.media_content:
        return entry.media_content[0].get("url")
    
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        return entry.media_thumbnail[0].get("url")
    
    return None

def clean_summary(text):
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    if len(text) > 250:
        text = text[:247] + "..."
    return text.strip()

def get_theme_and_emoji(titre):
    titre_lower = titre.lower()
    
    if any(word in titre_lower for word in [
        "iran", "israel", "ukraine", "guerre", "bombardement", "missile", "attaque", 
        "mort", "tué", "attentat", "explosion", "frappe", "conflit", "armée", "soldat"
    ]):
        return "FLASH INFO", "⚡️"
    
    if any(word in titre_lower for word in [
        "macron", "gouvernement", "président", "politique", "assemblée", "sénat", 
        "loi", "député", "ministre", "réforme", "élection", "vote", "parti", 
        "rn", "lfi", "renaissance", "ps", "lr", "budget", "taxe"
    ]):
        return "Politique", "🏛️"
    
    elif any(word in titre_lower for word in [
        "police", "justice", "tribunal", "procès", "arrestation", "crime", 
        "meurtre", "agression", "vol", "cambriolage", "prison", "condamné", 
        "enquête", "suspect", "victime", "homicide"
    ]):
        return "Faits divers", "⚖️"
    
    elif any(word in titre_lower for word in [
        "économie", "euro", "bourse", "inflation", "emploi", "entreprise", 
        "chômage", "salaire", "prix", "carburant", "essence", "immobilier", 
        "banque", "crédit", "pme", "industrie"
    ]):
        return "Économie", "📈"
    
    elif any(word in titre_lower for word in [
        "sport", "foot", "football", "match", "ligue", "psg", "om", "rugby", 
        "tennis", "roland-garros", "cyclisme", "tour de france", "basket", 
        "formule 1", "f1", "jo", "olympique", "championnat"
    ]):
        return "Sport", "⚽"
    
    elif any(word in titre_lower for word in [
        "climat", "météo", "tempête", "chaleur", "inondation", "canicule", 
        "orage", "neige", "froid", "réchauffement", "écologie", "pollution", 
        "environnement", "sécheresse"
    ]):
        return "Météo / Climat", "🌪️"
    
    elif any(word in titre_lower for word in [
        "santé", "hôpital", "covid", "virus", "médecin", "épidémie", 
        "vaccin", "maladie", "cancer", "urgences", "soignants", "grippe"
    ]):
        return "Santé", "🏥"
    
    elif any(word in titre_lower for word in [
        "international", "monde", "europe", "chine", "usa", "états-unis", 
        "russie", "poutine", "trump", "biden", "allemagne", "italie", 
        "espagne", "onu", "otan", "diplomatie"
    ]):
        return "International", "🌍"
    
    elif any(word in titre_lower for word in [
        "école", "éducation", "université", "étudiant", "professeur", 
        "manifestation", "grève", "syndicat", "retraite", "logement", 
        "famille", "société"
    ]):
        return "Société", "👥"
    
    elif any(word in titre_lower for word in [
        "technologie", "tech", "ia", "intelligence artificielle", "internet", 
        "téléphone", "apple", "google", "espace", "nasa", "science"
    ]):
        return "Tech / Science", "🔬"
    
    elif any(word in titre_lower for word in [
        "cinéma", "film", "musique", "concert", "festival", "culture", 
        "people", "célébrité", "acteur", "chanteur"
    ]):
        return "Culture", "🎬"
    
    else:
        return "Actualité", "📰"

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
                    
                    summary = ""
                    if hasattr(entry, "summary"):
                        summary = clean_summary(entry.summary)
                    elif hasattr(entry, "description"):
                        summary = clean_summary(entry.description)
                    
                    theme, emoji = get_theme_and_emoji(titre)
                    
                    message = (
                        f"*{theme}* | **Info France Plus**\n\n"
                        f"{emoji} *{titre}*\n\n"
                    )
                    
                    if summary:
                        message += f"{summary}\n\n"
                    
                    message += (
                        f"Source : *{source}*\n"
                        f"[Lire l'article complet]({lien})\n\n"
                        f"_Restez informés en direct sur Info France Plus_ → t.me/infofranceplus"
                    )
                    
                    res = envoyer_telegram(message, image_url)
                    if res and res.get("ok"):
                        print(f"Article publié : {titre} ({source})")
                        articles_publies.add(entry.link)
                    else:
                        print(f"Échec de l'envoi : {res}")
        except Exception as e:
            print(f"Erreur sur le flux {source} : {e}")

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
