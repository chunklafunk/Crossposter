from flask import Flask, render_template, request, make_response
import pandas as pd
import os
import time
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_image_url(item_number):
    url = f'https://www.ebay.com/itm/{item_number}'
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        meta_image = soup.find("meta", property="og:image")
        if meta_image and meta_image.get("content"):
            return meta_image["content"]
    except Exception as e:
        print(f"[{item_number}] Error: {e}")
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
