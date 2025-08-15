import requests
from bs4 import BeautifulSoup
import time
from flask import Flask
import threading

# Telegram bilgileri
BOT_TOKEN = "8396240761:AAEtNOrYeHFM_S_NeHbfPLWyVeH5XesO2vc"
CHAT_ID = "1856455295"

# Flask app (Render'da aktif kalması için)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram mesaj hatası:", e)

# Amazon indirimleri
def scrape_amazon():
    url = "https://www.amazon.com.tr/deals?ref_=nav_cs_gb"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    products = []
    for item in soup.select(".a-section.octopus-dlp-asin-section"):
        title = item.select_one("img")["alt"] if item.select_one("img") else "Ürün adı yok"
        link = "https://www.amazon.com.tr" + item.select_one("a")["href"]
        products.append(f"📌 {title}\n🔗 {link}")
    return products

# Trendyol indirimleri
def scrape_trendyol():
    url = "https://www.trendyol.com/sr?fl=indirimde"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    products = []
    for item in soup.select(".prdct-cntnr-wrppr .p-card-wrppr"):
        title = item.select_one(".prdct-desc-cntnr-name").get_text(strip=True) if item.select_one(".prdct-desc-cntnr-name") else "Ürün adı yok"
        link = "https://www.trendyol.com" + item.select_one("a")["href"]
        products.append(f"📌 {title}\n🔗 {link}")
    return products

# Hepsiburada indirimleri
def scrape_hepsiburada():
    url = "https://www.hepsiburada.com/indirimler"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    products = []
    for item in soup.select(".productListContent-item"):
        title = item.select_one("h3").get_text(strip=True) if item.select_one("h3") else "Ürün adı yok"
        link_tag = item.select_one("a")
        if link_tag:
            link = "https://www.hepsiburada.com" + link_tag["href"]
            products.append(f"📌 {title}\n🔗 {link}")
    return products

# Tüm indirimleri çek ve gönder
def check_discounts():
    try:
        all_products = []

        amazon_products = scrape_amazon()
        trendyol_products = scrape_trendyol()
        hepsiburada_products = scrape_hepsiburada()

        all_products.extend(amazon_products[:5])  # Fazla mesaj olmasın diye ilk 5 ürün
        all_products.extend(trendyol_products[:5])
        all_products.extend(hepsiburada_products[:5])

        if all_products:
            message = "🔥 Yeni İndirimler 🔥\n\n" + "\n\n".join(all_products)
            send_telegram_message(message)
        else:
            send_telegram_message("Bugün yeni indirim bulunamadı.")
    except Exception as e:
        print("İndirim çekme hatası:", e)

# Arka planda sürekli çalışacak döngü
def run_scheduler():
    while True:
        check_discounts()
        time.sleep(900)  # 15 dakika

# Flask + bot thread başlatma
if __name__ == "__main__":
    threading.Thread(target=run_scheduler, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
