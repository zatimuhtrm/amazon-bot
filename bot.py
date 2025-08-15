import requests
from bs4 import BeautifulSoup
import time
import os
from datetime import datetime

# Telegram bilgileri
BOT_TOKEN = "8396240761:AAEtNOrYeHFM_S_NeHbfPLWyVeH5XesO2vc"
CHAT_ID = "1856455295"

# Bildirim gönderme fonksiyonu
def send_telegram_message(text, photo_url=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)
    
    if photo_url:
        photo_payload = {
            "chat_id": CHAT_ID,
            "photo": photo_url
        }
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto", data=photo_payload)

# Amazon indirimleri
def scrape_amazon():
    url = "https://www.amazon.com.tr/gp/goldbox"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    
    items = soup.select(".a-section.a-text-center.sponsored-products-truncator")
    for item in items:
        title = item.get_text(strip=True)
        link = "https://www.amazon.com.tr" + item.find("a")["href"]
        send_telegram_message(f"📌 {title}\n🔗 {link}")

# Trendyol indirimleri
def scrape_trendyol():
    url = "https://www.trendyol.com/sr?wb=102&os=1&sst=PRICE_BY_ASC"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    
    items = soup.select(".p-card-wrppr")
    for item in items:
        title = item.select_one(".prdct-desc-cntnr-ttl").get_text(strip=True)
        link = "https://www.trendyol.com" + item.find("a")["href"]
        send_telegram_message(f"📌 {title}\n🔗 {link}")

# Hepsiburada indirimleri
def scrape_hepsiburada():
    url = "https://www.hepsiburada.com/indirimler"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    
    items = soup.select(".productListContent-item")
    for item in items:
        title = item.get_text(strip=True)
        link = "https://www.hepsiburada.com" + item.find("a")["href"]
        send_telegram_message(f"📌 {title}\n🔗 {link}")

# Ana fonksiyon
def main():
    send_telegram_message(f"⏳ İndirim kontrolü başladı ({datetime.now().strftime('%H:%M:%S')})")
    scrape_amazon()
    scrape_trendyol()
    scrape_hepsiburada()
    send_telegram_message(f"✅ İndirim kontrolü bitti ({datetime.now().strftime('%H:%M:%S')})")

if __name__ == "__main__":
    main()
