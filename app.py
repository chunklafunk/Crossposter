from flask import Flask, render_template, request, make_response
import pandas as pd
import os
import requests

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

RAILWAY_API_BASE = "https://web-production-0646.up.railway.app"

def get_image_url(item_number):
    try:
        url = f"{RAILWAY_API_BASE}/api/image?item={item_number}"
        res = requests.get(url, timeout=20)
        if res.status_code == 200:
            return res.json().get("image_url", "")
        else:
            print(f"[{item_number}] API error {res.status_code}: {res.text}", flush=True)
    except Exception as e:
        print(f"[{item_number}] Error: {e}", flush=True)
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
                print("🔍 Fetching images from API...", flush=True)
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
