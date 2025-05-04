from flask import Flask, render_template, request
import os
import pandas as pd
import requests

app = Flask(__name__)
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
            item_id = str(listing.get('Item ID') or listing.get('ItemID') or listing.get('item_id') or '').strip()
            print(f"📦 Item ID: {item_id}")

            images = []
            if item_id:
                try:
                    res = requests.get(f"{RAILWAY_API_BASE}?item={item_id}", timeout=20)
                    res.raise_for_status()
                    images = res.json().get('image_urls', [])
                    print(f"🖼️ Found {len(images)} images")
                except Exception as e:
                    print(f"❌ Error for {item_id}: {e}")
            else:
                print("⚠️ No item ID found in listing.")

            listing['images'] = images

    return render_template('index.html', listings=listings)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
