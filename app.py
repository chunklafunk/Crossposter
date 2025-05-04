from flask import Flask, render_template, request, make_response
import pandas as pd
import os
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_image_url(item_number):
    url = f'https://www.ebay.com/itm/{item_number}'
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code != 200:
            print(f"[{item_number}] Failed to load page. Status: {res.status_code}")
            return ""

        soup = BeautifulSoup(res.text, 'html.parser')

        # Try og:image first
        meta_image = soup.find("meta", property="og:image")
        if meta_image and meta_image.get("content"):
            return meta_image["content"]

        # Fallback: try first <img> on the page
        img_tag = soup.find("img")
        if img_tag and img_tag.get("src"):
            return img_tag["src"]

        print(f"[{item_number}] No image found on page.")
    except Exception as e:
        print(f"[{item_number}] Error scraping image: {e}")
    return ""

@app.route('/', methods=['GET', 'POST'])
def index():
    listings = []
    if request.method == 'POST':
        file = request.files['csv_file']
        if file:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'eBay-active-listings.csv')
            file.save(filepath)
            df = pd.read_csv(filepath)

            if 'Item number' in df.columns:
                print("🔍 Scraping photos...")
                df['PhotoURL'] = df['Item number'].astype(str).apply(get_image_url)
                df.to_csv(filepath, index=False)

            df = df.fillna('')
            listings = df.to_dict(orient='records')
    else:
        try:
            df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], 'eBay-active-listings.csv'))
            listings = df.fillna('').to_dict(orient='records')
        except:
            listings = []

    rendered = render_template('index.html', listings=listings)
    response = make_response(rendered)
    response.headers['Content-Security-Policy'] = "default-src * 'unsafe-inline' data: blob:;"
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
