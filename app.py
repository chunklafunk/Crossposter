from flask import Flask, render_template, request, redirect, url_for, session
import os
import pandas as pd
import requests
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')
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

    return render_template('index.html', listings=listings, mercari_logged_in=session.get('mercari_logged_in', False))


@app.route('/login/mercari', methods=['POST'])
def login_mercari():
    # Simulate successful login
    print("🔐 User logged into Mercari session", flush=True)
    session['mercari_logged_in'] = True
    return redirect(url_for('index'))


@app.route('/logout/mercari', methods=['POST'])
def logout_mercari():
    session.pop('mercari_logged_in', None)
    return redirect(url_for('index'))


@app.route('/crosspost/mercari/<item_id>', methods=['POST'])
def crosspost_mercari(item_id):
    if not session.get('mercari_logged_in'):
        return "Not logged in to Mercari", 403

    filepath = os.path.join(UPLOAD_FOLDER, 'eBay-active-listings.csv')
    df = pd.read_csv(filepath)
    listings = df.to_dict(orient='records')

    listing = next((l for l in listings if str(l.get('Item number') or l.get('Item ID') or l.get('item_id')) == item_id), None)

    if not listing:
        return f"Listing {item_id} not found", 404

    # Mock crosspost logic
    print(f"\n🚀 [MOCK] Crossposting to Mercari: {item_id}", flush=True)
    print(json.dumps(listing, indent=2), flush=True)

    return f"✅ Listing {item_id} mock-posted to Mercari!"


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
