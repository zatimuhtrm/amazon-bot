import os
import time
import requests
from bs4 import BeautifulSoup

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram_message(text, photo_url=None):
    if photo_url:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
            data={"chat_id": CHAT_ID, "caption": text},
            files={"photo": requests.get(photo_url, stream=True).raw}
        )
    else:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
        )

def get_amazon_tr():
    url = "https://www.amazon.com.tr/deals?ref_=nav_cs_gb"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    items = []
    for deal in soup.select(".DealCard-module__card_1oA2E"):
        try:
            title = deal.select_one(".DealContent-module__truncate_sWbxETx42ZPStTc9jwySW").get_text(strip=True)
            price = deal.select_one(".a-price-whole").get_text(strip=True).replace(".", "")
            discount = deal.select_one(".BadgeAutomatedLabel-module__badgeText_1LCx4").get_text(strip=True)
            if "%" in discount:
                rate = int(discount.replace("%", "").replace("-", ""))
                if rate >= 20:
                    link = "https://www.amazon.com.tr" + deal.select_one("a")["href"]
                    img = deal.select_one("img")["src"]
                    items.append((title, price, discount, link, img))
        except:
            continue
    return items

def get_trendyol():
    url = "https://www.trendyol.com/sr?tag=Indirimli-Urunler"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    items = []
    for deal in soup.select(".p-card-wrppr"):
        try:
            title = deal.select_one(".prdct-desc-cntnr-name").get_text(strip=True)
            price = deal.select_one(".prc-box-dscntd").get_text(strip=True)
            discount = deal.select_one(".prc-dsc").get_text(strip=True)
            if "%" in discount:
                rate = int(discount.replace("%", "").replace("-", ""))
                if rate >= 20:
                    link = "https://www.trendyol.com" + deal.select_one("a")["href"]
                    img = deal.select_one("img")["src"]
                    items.append((title, price, discount, link, img))
        except:
            continue
    return items

def get_hepsiburada():
    url = "https://www.hepsiburada.com/indirimler"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    items = []
    for deal in soup.select(".productListContent-item"):
        try:
            title = deal.select_one(".product-title").get_text(strip=True)
            price = deal.select_one(".price-value").get_text(strip=True)
            discount = deal.select_one(".discount-badge").get_text(strip=True)
            if "%" in discount:
                rate = int(discount.replace("%", "").replace("-", ""))
                if rate >= 20:
                    link = "https://www.hepsiburada.com" + deal.select_one("a")["href"]
                    img = deal.select_one("img")["src"]
                    items.append((title, price, discount, link, img))
        except:
            continue
    return items

def main():
    while True:
        for site_func in [get_amazon_tr, get_trendyol, get_hepsiburada]:
            try:
                for title, price, discount, link, img in site_func():
                    text = f"<b>{title}</b>\nFiyat: {price} TL\nİndirim: {discount}\n{link}"
                    send_telegram_message(text, img)
            except Exception as e:
                print(f"Hata: {e}")
        time.sleep(300)  # 5 dakika

if __name__ == "__main__":
    main()
