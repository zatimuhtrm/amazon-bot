import os, time, requests, re
from bs4 import BeautifulSoup
from threading import Thread
from flask import Flask, jsonify

# ====== AYARLAR ======
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("CHAT_ID", "").strip()
INTERVAL_SEC = int(os.getenv("INTERVAL_SEC", "300"))  # 5 dk
MIN_PCT = int(os.getenv("MIN_DISCOUNT", "20"))        # %20+

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
}

SENT = set()  # aynı fırsatı tekrar yollamamak için (container resetlenirse sıfırlanır)

def send_msg(title, price, pct_off, link, img=None, source=""):
    if not (BOT_TOKEN and CHAT_ID):
        print("BOT_TOKEN/CHAT_ID yok.")
        return
    caption = f"📦 {title}\n💰 {price} TL\n🔻 %{pct_off} indirim\n🏷️ {source}\n🔗 {link}"
    if img:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
            data={"chat_id": CHAT_ID, "caption": caption, "photo": img}
        )
    else:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": caption}
        )

def to_num(s):
    if not s: return None
    s = s.replace("TL","").replace("₺","").replace(".","").replace(" ", "").replace("\xa0","")
    s = s.replace(",", ".")
    m = re.search(r"(\d+(\.\d+)?)", s)
    return float(m.group(1)) if m else None

def pct(old, new):
    if not old or not new or old <= 0: return None
    return round((old - new) * 100 / old)

# ---------- Amazon TR ----------
def get_amazon_tr():
    url = "https://www.amazon.com.tr/gp/goldbox"
    out = []
    try:
        html = requests.get(url, headers=HEADERS, timeout=25).text
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("[data-component-type='s-deal-card']")
        for c in cards:
            title = (c.select_one(".DealContent-module__truncate_sWbxETx42ZPStTc9jwySW")
                     or c.select_one("span.a-text-normal") or c).get_text(strip=True)
            a = c.select_one("a.a-link-normal")
            link = "https://www.amazon.com.tr" + a["href"] if a and a.has_attr("href") else url
            img = (c.select_one("img") or {}).get("src") if c.select_one("img") else None
            now_node = c.select_one(".a-price .a-offscreen")
            price_now = to_num(now_node.get_text()) if now_node else None

            pct_node = c.find(text=re.compile("%"))
            pct_off = None
            if pct_node:
                m = re.search(r"%\s?(\d+)", str(pct_node))
                if m: pct_off = int(m.group(1))

            if price_now and pct_off and pct_off >= MIN_PCT:
                out.append(("Amazon TR", title, int(price_now), pct_off, link, img))
    except Exception as e:
        print("Amazon err:", e)
    return out

# ---------- Trendyol ----------
def get_trendyol():
    # Basit liste sayfası: bazı dönemlerde çalışır, bazen sınırlı döner
    url = "https://www.trendyol.com/sr?tag=Indirimli-Urunler"
    out = []
    try:
        html = requests.get(url, headers=HEADERS, timeout=25).text
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select(".p-card-wrppr")
        for c in cards:
            try:
                title = c.select_one(".prdct-desc-cntnr-name").get_text(strip=True)
                price = to_num((c.select_one(".prc-box-dscntd") or c.select_one(".prc-box-sllng")).get_text(strip=True))
                disc_txt = (c.select_one(".prc-dsc") or c.select_one(".badge-discount")).get_text(strip=True)
                m = re.search(r"(\d+)", disc_txt)
                pct_off = int(m.group(1)) if m else None
                a = c.select_one("a")
                link = "https://www.trendyol.com" + a["href"] if a and a.has_attr("href") else url
                img = (c.select_one("img") or {}).get("src") if c.select_one("img") else None
                if price and pct_off and pct_off >= MIN_PCT:
                    out.append(("Trendyol", title, int(price), pct_off, link, img))
            except: 
                continue
    except Exception as e:
        print("Trendyol err:", e)
    return out

# ---------- Hepsiburada ----------
def get_hepsiburada():
    urls = [
        "https://www.hepsiburada.com/super-fiyat-super-teklifler",
        "https://www.hepsiburada.com/indirimler",
    ]
    out = []
    for url in urls:
        try:
            html = requests.get(url, headers=HEADERS, timeout=25).text
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select("li.productListContent-item") or soup.select("[data-test-id='product-card']")
            for c in cards:
                try:
                    title = (c.select_one("[data-test-id='product-card-name']") or c.select_one(".product-title")).get_text(strip=True)
                    now_node = c.select_one("[data-test-id='price-current-price']") or c.select_one(".price-value") or c.select_one(".product-price")
                    old_node = c.select_one("[data-test-id='price-original-price']") or c.select_one(".originalPrice")
                    price_now = to_num(now_node.get_text()) if now_node else None
                    price_old = to_num(old_node.get_text()) if old_node else None
                    pct_off = pct(price_old, price_now) if price_old and price_now else None
                    a = c.select_one("a")
                    link = "https://www.hepsiburada.com" + a["href"] if a and a.has_attr("href") else url
                    img = (c.select_one("img") or {}).get("src") if c.select_one("img") else None
                    if price_now and pct_off and pct_off >= MIN_PCT:
                        out.append(("Hepsiburada", title, int(price_now), pct_off, link, img))
                except:
                    continue
        except Exception as e:
            print("HB err:", e)
    return out

def bot_loop():
    # başlangıç mesajı
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                      data={"chat_id": CHAT_ID, "text": f"✅ Bot aktif. {INTERVAL_SEC//60} dk aralıkla, %{MIN_PCT}+ indirimleri tarıyorum."})
    except Exception as e:
        print("TG start msg err:", e)

    while True:
        try:
            print("Tarama başladı...")
            all_items = []
            for source, title, price, pct_off, link, img in get_amazon_tr():
                all_items.append((source, title, price, pct_off, link, img))
            for source, title, price, pct_off, link, img in get_trendyol():
                all_items.append((source, title, price, pct_off, link, img))
            for source, title, price, pct_off, link, img in get_hepsiburada():
                all_items.append((source, title, price, pct_off, link, img))

            for source, title, price, pct_off, link, img in all_items:
                key = f"{source}|{link}"
                if key in SENT: 
                    continue
                send_msg(title, price, pct_off, link, img, source)
                SENT.add(key)
            print("Tarama bitti.")
        except Exception as e:
            print("Loop err:", e)
        time.sleep(INTERVAL_SEC)

# ====== Flask - sahte web ucu (Render Free için) ======
app = Flask(__name__)

@app.get("/")
def index():
    return "OK"

@app.get("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    # Bot arka planda
    Thread(target=bot_loop, daemon=True).start()
    # Render Free: portu bağla
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)

from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Amazon Bot is running!"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
