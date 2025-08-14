import requests
from bs4 import BeautifulSoup
import datetime

# Telegram bilgileri
BOT_TOKEN = "8396240761:AAEtNOrYeHFM_S_NeHbfPLWyVeH5XesO2vc"
CHAT_ID = "6013361654"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    requests.post(url, data=payload)

def scrape_amazon():
    url = "https://www.amazon.com.tr/gp/goldbox"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    items = soup.select(".DealCard", limit=5)
    results = []
    for item in items:
        title = item.get_text(strip=True)[:80]
        link = "https://www.amazon.com.tr" + item.find("a")["href"]
        results.append(f"📦 <b>{title}</b>\n🔗 {link}")
    return results

def scrape_hepsiburada():
    url = "https://www.hepsiburada.com/super-fiyat-super-teklif"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    items = soup.select(".productListContent-item", limit=5)
    results = []
    for item in items:
        title = item.get_text(strip=True)[:80]
        link = "https://www.hepsiburada.com" + item.find("a")["href"]
        results.append(f"📦 <b>{title}</b>\n🔗 {link}")
    return results

def scrape_trendyol():
    url = "https://www.trendyol.com/sr?wb=102&qt=indirim"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    items = soup.select(".p-card-wrppr", limit=5)
    results = []
    for item in items:
        title = item.get_text(strip=True)[:80]
        link_tag = item.find("a")
        if link_tag:
            link = "https://www.trendyol.com" + link_tag["href"]
            results.append(f"📦 <b>{title}</b>\n🔗 {link}")
    return results

if __name__ == "__main__":
    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    send_telegram_message(f"✅ Bot aktif! ({now})")

    amazon = scrape_amazon()
    hb = scrape_hepsiburada()
    trendyol = scrape_trendyol()

    all_products = amazon + hb + trendyol
    for product in all_products:
        send_telegram_message(product)
