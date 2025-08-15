import requests
from bs4 import BeautifulSoup
import time
import os
from flask import Flask

# Telegram bilgileri
BOT_TOKEN = "8396240761:AAEtNOrYeHFM_S_NeHbfPLWyVeH5XesO2vc"
CHAT_ID = "1856455295"

# Flask ayarları (Render uyanık tutsun diye)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot çalışıyor."

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Telegram mesaj hatası: {e}")

def check_discounts():
    urls = [
        "https://www.amazon.com.tr/deals",   # Amazon indirim sayfası
        "https://www.hepsiburada.com/indirimler",  # Hepsiburada indirim sayfası
        "https://www.trendyol.com/sr?wc=103108&os=1"  # Trendyol indirim sayfası
    ]

    for site in urls:
        try:
            response = requests.get(site, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.title.string.strip() if soup.title else "İndirim Sayfası"
            send_telegram_message(f"📢 Yeni indirimleri kontrol et: {site}\nSayfa başlığı: {title}")
        except Exception as e:
            print(f"Hata: {site} - {e}")

if __name__ == "__main__":
    send_telegram_message("✅ Bot başlatıldı ve indirimler takip ediliyor.")
    while True:
        check_discounts()
        time.sleep(3600)  # 1 saatte bir kontrol et
