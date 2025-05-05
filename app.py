from flask import Flask, render_template, request, send_file
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

RAILWAY_API_BASE = 'https://web-production-0646.up.railway.app/api/images'
MERCARI_CSV_PATH = os.path.join(UPLOAD_FOLDER, 'mercari_upload.csv')

def scrape_ebay_details(item_id):
    url = f"https://www.ebay.com/itm/{item_id}"
    print(f"🔍 Scraping {url}")

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(20)

    try:
        driver.get(url)
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Title
        title_tag = soup.select_one('#itemTitle')
        title = title_tag.get_text(strip=True).replace("Details about  ", "") if title_tag else ""

        # Price
        price_tag = soup.select_one('.x-price-approx__value, .notranslate')
        price_text = price_tag.get_text(strip=True).replace('$', '') if price_tag else ""
        try:
            price = float(price_text.replace(",", ""))
        except:
            price = ""

        # Condition
        condition_tag = soup.select_one('#vi-itm-cond')
        condition = condition_tag.get_text(strip=True) if condition_tag else "Good"

        # Description
        description = title if title else "No description"
    except Exception as e:
        print(f"❌ Error scraping eBay page: {e}")
        title = ""
        price = ""
        condition = "Good"
        description = ""
    finally:
        driver.quit()

    return {
        'title': title[:80],
        'price': price,
        'condition': condition,
        'description': description
    }

@app.route('/', methods=['GET', 'POST'])
def index():
    listings = []

    if request.method == 'POST':
        file = request.files.get('csv')
        if not file:
            return "No file uploaded", 400

        filepath = os.path.join(UPLOAD_FOLDER, 'eBay-active-listings.csv')
        file.save(filepath)
        df = pd.read_csv(filepath)

        mercari_rows = []
        listings = []

        for index, row in df.iterrows():
            item_id = str(
                row.get('Item number') or
                row.get('Item ID') or
                row.get('ItemID') or
                row.get('item_id') or ''
            ).strip()
            if not item_id:
                continue

            print(f"\n📦 Processing Item ID: {item_id}")
            scraped = scrape_ebay_details(item_id)

            # Get image URLs
            images = []
            try:
                api_url = f"{RAILWAY_API_BASE}?item={item_id}"
                print(f"🌐 Fetching images from: {api_url}")
                res = requests.get(api_url, timeout=20)
                res.raise_for_status()
                data = res.json()
                images = data.get('image_urls', [])
                print(f"🖼️ Found {len(images)} images")
            except Exception as e:
                print(f"❌ Image fetch failed for {item_id}: {e}")

            # Prepare listing display
            listings.append({
                'title': scraped['title'],
                'price': scraped['price'],
                'condition': scraped['condition'],
                'quantity': row.get('Quantity', 1),
                'images': images
            })

            # Prepare Mercari CSV row
            condition_map = {
                'New': 'New', 'Brand New': 'New',
                'Like New': 'Like new',
                'Very Good': 'Good', 'Good': 'Good',
                'Acceptable': 'Fair', 'Poor': 'Poor'
            }
            clean_condition = condition_map.get(scraped['condition'], 'Good')

            mercari_rows.append({
                'name': scraped['title'],
                'price': scraped['price'],
                'description': scraped['description'],
                'item_condition_name': clean_condition,
                'image_urls': ','.join(images[:12]),
                'brand_id': '',
                'category_id': '',
                'category_size_group_id': '',
                'size_id': '',
                'shipping_payer_name': 'Seller',
                'shipping_method': 'Standard'
            })

        if mercari_rows:
            df_mercari = pd.DataFrame(mercari_rows)
            column_order = [
                'name', 'price', 'description', 'item_condition_name', 'image_urls',
                'brand_id', 'category_id', 'category_size_group_id',
                'size_id', 'shipping_payer_name', 'shipping_method'
            ]
            df_mercari = df_mercari[column_order]
            df_mercari.to_csv(MERCARI_CSV_PATH, index=False)

    return render_template('index.html', listings=listings, mercari_csv=True)

@app.route('/download-mercari-csv')
def download_csv():
    return send_file(MERCARI_CSV_PATH, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
