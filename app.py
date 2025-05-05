from flask import Flask, render_template, request, send_file
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
    mercari_csv_path = os.path.join(UPLOAD_FOLDER, 'mercari_upload.csv')

    if request.method == 'POST':
        file = request.files.get('csv')
        if not file:
            return "No file uploaded", 400

        filepath = os.path.join(UPLOAD_FOLDER, 'eBay-active-listings.csv')
        file.save(filepath)

        df = pd.read_csv(filepath)
        listings = df.to_dict(orient='records')

        mercari_rows = []
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

            # Prepare Mercari row
            title = listing.get('Title', '')[:80]
            price = listing.get('Price', '')
            condition_map = {
                'New': 'New', 'Brand New': 'New',
                'Like New': 'Like new',
                'Very Good': 'Good', 'Good': 'Good',
                'Acceptable': 'Fair', 'Poor': 'Poor'
            }
            ebay_condition = str(listing.get('Condition', '')).strip()
            condition = condition_map.get(ebay_condition, 'Good')
            description = listing.get('Description') or f"{title}\nCondition: {condition}"
            image_urls = ','.join(images[:12])

            mercari_rows.append({
                'name': title,
                'price': price,
                'description': description,
                'item_condition_name': condition,
                'image_urls': image_urls,
                'shipping_payer_name': 'Seller',
                'shipping_method': 'Standard',
                'category_id': ''
            })

        # Write Mercari CSV
        if mercari_rows:
            df_mercari = pd.DataFrame(mercari_rows)
            df_mercari.to_csv(mercari_csv_path, index=False)

    return render_template('index.html', listings=listings, mercari_csv=True)

@app.route('/download-mercari-csv')
def download_csv():
    path = os.path.join(UPLOAD_FOLDER, 'mercari_upload.csv')
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
