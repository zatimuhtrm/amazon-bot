import os, re, json, time, datetime, threading
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify

# =================== AYARLAR ===================
# İstersen Render'da Environment Variables ile override edebilirsin
BOT_TOKEN = os.getenv("BOT_TOKEN", "8396240761:AAEtNOrYeHFM_S_NeHbfPLWyVeH5XesO2vc").strip()
CHAT_ID   = os.getenv("CHAT_ID",   "1856455295").strip()

MIN_DISCOUNT = int(os.getenv("MIN_DISCOUNT", "20"))    # %20 ve üzeri
MAX_PER_SITE = int(os.getenv("MAX_PER_SITE", "10"))    # her siteden en fazla kaç ürün göndersin

# User-Agent/Headers (bot engellerini azaltır)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
}

# Gönderilmiş ürünleri hatırlamak için (uykuya geçmezse tekrar göndermez)
SENT_FILE = "sent.json"
_sent = set()
if os.path.exists(SENT_FILE):
    try:
        _sent = set(json.load(open(SENT_FILE)))
    except Exception:
        _sent = set()

# =================== TELEGRAM ===================
def tg_send_text(text: str):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=20)
    except Exception as e:
        print("Telegram text err:", e)

def tg_send_photo(caption: str, photo_url: str):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        data = {"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"}
        files_or_data = {"photo": photo_url}
        requests.post(url, data=data, timeout=20, params=None, files=None)  # fallback
        requests.post(url, data=data | files_or_data, timeout=20)
    except Exception as e:
        # Foto hata verirse metin olarak gönder
        print("Telegram photo err, fallback to text:", e)
        tg_send_text(caption)

def send_item(site: str, title: str, price_tl, pct_off, link: str, img: str | None):
    parts = [f"🏷️ <b>{site}</b>", f"📦 {title}"]
    if price_tl is not None:
        parts.append(f"💰 {price_tl} TL")
    if pct_off is not None:
        parts.append(f"🔻 %{pct_off}")
    parts.append(f"🔗 {link}")
    caption = "\n".join(parts)

    if img:
        tg_send_photo(caption, img)
    else:
        tg_send_text(caption)

def mark_sent(key: str):
    _sent.add(key)
    try:
        json.dump(list(_sent), open(SENT_FILE, "w"))
    except Exception as e:
        print("SENT save err:", e)

def to_num(s: str | None):
    if not s: return None
    s = s.replace("TL","").replace("₺","").replace(".","").replace("\xa0","").replace(" ", "")
    s = s.replace(",", ".")
    m = re.search(r"(\d+(\.\d+)?)", s)
    return float(m.group(1)) if m else None

def pct(old, new):
    try:
        if old and new and old > 0:
            return round((old - new) * 100 / old)
    except: pass
    return None

# =================== SCRAPERS ===================
def scrape_amazon():
    url = "https://www.amazon.com.tr/gp/goldbox"
    out = []
    try:
        html = requests.get(url, headers=HEADERS, timeout=25).text
        soup = BeautifulSoup(html, "html.parser")

        cards = soup.select("[data-component-type='s-deal-card']")
        # ek fallback (bazı dönemlerde sınıf adları değişebiliyor)
        if not cards:
            cards = soup.select(".DealGridItem-module__dealItem, .DealCard")

        for c in cards:
            try:
                # başlık
                title = None
                for sel in [
                    ".DealContent-module__truncate_sWbxETx42ZPStTc9jwySW",
                    "span.a-text-normal",
                    "[data-a-target='deal-title']",
                ]:
                    n = c.select_one(sel)
                    if n:
                        title = n.get_text(strip=True)
                        break
                if not title:
                    title = c.get_text(" ", strip=True)[:120]

                # link
                a = c.select_one("a.a-link-normal, a[href]")
                link = ("https://www.amazon.com.tr" + a["href"]) if a and a.has_attr("href") else url

                # görsel
                img_tag = c.select_one("img")
                img = img_tag["src"] if img_tag and img_tag.has_attr("src") else None

                # fiyat / indirim yüzdesi
                price_now = None
                now_node = c.select_one(".a-price .a-offscreen")
                if now_node:
                    price_now = to_num(now_node.get_text())

                pct_off = None
                # yüzde metin içinde geçiyorsa yakala
                m = re.search(r"%\s?(\d+)", c.get_text(" ", strip=True))
                if m:
                    pct_off = int(m.group(1))

                if pct_off is not None and pct_off >= MIN_DISCOUNT:
                    out.append(("Amazon TR", title, int(price_now) if price_now else None, pct_off, link, img))
                    if len(out) >= MAX_PER_SITE:
                        break
            except: 
                continue
    except Exception as e:
        print("Amazon err:", e)
    return out

def scrape_hepsiburada():
    urls = [
        "https://www.hepsiburada.com/super-fiyat-super-teklifler",
        "https://www.hepsiburada.com/indirimler",
    ]
    out = []
    for url in urls:
        try:
            html = requests.get(url, headers=HEADERS, timeout=25).text
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select("[data-test-id='product-card'], li.productListContent-item")
            for c in cards:
                try:
                    # başlık
                    name = (c.select_one("[data-test-id='product-card-name']") or
                            c.select_one(".product-title") or c)
                    title = name.get_text(strip=True)[:140]

                    # fiyatlar
                    now_node = (c.select_one("[data-test-id='price-current-price']") or
                                c.select_one(".price-value") or
                                c.select_one(".product-price"))
                    old_node = (c.select_one("[data-test-id='price-original-price']") or
                                c.select_one(".originalPrice"))
                    price_now = to_num(now_node.get_text()) if now_node else None
                    price_old = to_num(old_node.get_text()) if old_node else None
                    pct_off = pct(price_old, price_now)

                    # link
                    a = c.select_one("a[href]")
                    link = ("https://www.hepsiburada.com" + a["href"]) if a and a.has_attr("href") else url

                    # görsel
                    img_tag = c.select_one("img")
                    img = img_tag["src"] if img_tag and img_tag.has_attr("src") else None

                    if pct_off is not None and pct_off >= MIN_DISCOUNT:
                        out.append(("Hepsiburada", title, int(price_now) if price_now else None, pct_off, link, img))
                        if len(out) >= MAX_PER_SITE:
                            break
                except:
                    continue
        except Exception as e:
            print("HB err:", e)
    return out

def scrape_trendyol():
    # Trendyol'da JS yoğun; statik HTML'den dönenler sınırlı olabilir, yine de deneriz.
    # "Günün Fırsatları" yaklaşımlı liste
    url = "https://www.trendyol.com/sr?tag=Indirimli-Urunler"
    out = []
    try:
        html = requests.get(url, headers=HEADERS, timeout=25).text
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select(".p-card-wrppr")
        for c in cards:
            try:
                title_node = (c.select_one(".prdct-desc-cntnr-name") or c.select_one(".description") or c)
                title = title_node.get_text(strip=True)[:140]

                # fiyat / indirim
                price_node = (c.select_one(".prc-box-dscntd") or c.select_one(".prc-box-sllng"))
                price_now = to_num(price_node.get_text()) if price_node else None

                disc_txt_node = (c.select_one(".prc-dsc") or c.select_one(".badge-discount"))
                pct_off = None
                if disc_txt_node:
                    m = re.search(r"(\d+)", disc_txt_node.get_text())
                    if m: pct_off = int(m.group(1))

                a = c.select_one("a[href]")
                link = ("https://www.trendyol.com" + a["href"]) if a and a.has_attr("href") else url

                img_tag = c.select_one("img")
                img = img_tag["src"] if img_tag and img_tag.has_attr("src") else None

                if pct_off is not None and pct_off >= MIN_DISCOUNT:
                    out.append(("Trendyol", title, int(price_now) if price_now else None, pct_off, link, img))
                    if len(out) >= MAX_PER_SITE:
                        break
            except:
                continue
    except Exception as e:
        print("Trendyol err:", e)
    return out

# =================== ÇALIŞTIRMA ===================
def run_once():
    """Cron-job.org her tetiklediğinde çağırılacak iş."""
    found = 0
    all_items = []
    all_items += scrape_amazon()
    all_items += scrape_hepsiburada()
    all_items += scrape_trendyol()

    for site, title, price, pct_off, link, img in all_items:
        key = f"{site}|{link}"
        if key in _sent:
            continue
        send_item(site, title, price, pct_off, link, img)
        mark_sent(key)
        found += 1

    return found

# =================== Flask (Render Web Service) ===================
app = Flask(__name__)

@app.get("/")
def index():
    return "OK"

@app.get("/health")
def health():
    return jsonify({"status": "ok", "sent_count": len(_sent)})

@app.get("/run")
def run_endpoint():
    # Sen cron-job.org'a bu endpoint'i ver
    try:
        count = run_once()
        return jsonify({"ok": True, "sent_this_run": count, "total_sent": len(_sent)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

def on_boot_message():
    try:
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        tg_send_text(f"✅ Bot ayakta (Render). Tetikleyici: /run — %{MIN_DISCOUNT}+ filtre | {now}")
    except Exception as e:
        print("Boot TG msg err:", e)

if __name__ == "__main__":
    # Açılışta kısa bir hoşgeldin mesajı
    threading.Thread(target=on_boot_message, daemon=True).start()
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
