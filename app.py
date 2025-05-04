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
        url = f"{RAILWAY_API_BASE}/api/images?item={item_number}"
        print(f"[{item_number}] → {url}", flush=True)
        res = requests.get(url, timeout=20)
        if res.status_code == 200:
            images = res.json().get("image_urls", [])
            if images:
                print(f"[{item_number}] ✅ Got {len(images)} images", flush=True)
                return images[0]  # Only return first image for now
            else:
                print(f"[{item_number}] ⚠️ No images found", flush=True)
        else:
            print(f"[{item_number}] ❌ API error {res.status_code}: {res.text}", flush=True)
    except Exception as e:
        print(f"[{item_number}] ❌ Exception: {e}", flush=True)
    return ""

@app.route('/', methods=['GET', 'POST'])
def index():
    listings = []
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'eBay-active-listings.csv')

    if request.method == 'POST':
        file = request.files['csv_file']
        if file:
            file.save(filepath)
            print(f"📁 Saved uploaded CSV to {filepath}", flush=True)

            df = pd.read_csv(filepath)
            if 'Item number' in df.columns:
                print("🔍 Fetching images from Railway API...", flush=True)
                df['PhotoURL'] = df['Item number'].astype(str).apply(get_image_url)
                df.to_csv(filepath, index=False)
                print(f"✅ Updated CSV saved to {filepath}", flush=True)

            df = df.fillna('')
            listings = df.to_dict(orient='records')

    else:
        try:
            df = pd.read_csv(filepath)
            listings = df.fillna('').to_dict(orient='records')
        except Exception as e:
            print(f"⚠️ No existing CSV to load: {e}", flush=True)
            listings = []

    rendered = render_template('index.html', listings=listings)
    response = make_response(rendered)
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
