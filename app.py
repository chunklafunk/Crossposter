from flask import Flask, render_template, request, session, redirect
import os
import pandas as pd
import requests
import numpy as np

app = Flask(__name__)
app.secret_key = "secret"
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

RAILWAY_API_BASE = 'https://web-production-0646.up.railway.app/api/images'

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

        # ✅ Force all invalid values to None
        df = df.replace({np.nan: None, 'NaN': None, 'nan': None, '': None})

        listings = df.to_dict(orient='records')

        for listing in listings:
            item_id = str(
                listing.get('Item number') or
                listing.get('Item ID') or
                listing.get('ItemID') or
                listing.get('item_id') or ''
            ).strip()
            print(f"\n📦 Item ID: {item_id}", flush=True)

            images = []
            if item_id:
                try:
                    api_url = f"{RAILWAY_API_BASE}?item={item_id}"
                    print(f"🌐 Fetching from: {api_url}", flush=True)
                    res = requests.get(api_url, timeout=20)
                    print(f"📡 Status: {res.status_code}", flush=True)
                    print(f"📄 Raw Response: {res.text[:300]}...", flush=True)
                    res.raise_for_status()
                    data = res.json()
                    images = data.get('image_urls', [])
                    print(f"🖼️ Found {len(images)} images", flush=True)
                except Exception as e:
                    print(f"❌ Error for {item_id}: {e}", flush=True)
            else:
                print("⚠️ No item ID found in this row.", flush=True)

            listing['images'] = images

    return render_template('index.html', listings=listings, mercari_linked=session.get('mercari_linked', False))

@app.route('/linked-accounts', methods=['GET', 'POST'])
def linked_accounts():
    if request.method == 'POST':
        session['mercari_linked'] = True
        return redirect('/')
    return "<h2>✅ Mercari is linked</h2><br><a href='/'>Back</a>"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
