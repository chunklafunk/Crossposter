from flask import Flask, render_template, request, redirect, url_for, session, send_file
import pandas as pd
import json
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load eBay → Mercari category ID mapping
with open('category_mapper.json') as f:
    CATEGORY_MAP = json.load(f)

@app.route('/')
def index():
    listings = session.get('listings', [])
    return render_template('index.html', listings=listings)

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    file = request.files['file']
    if file.filename.endswith('.csv'):
        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)

        df = pd.read_csv(path)
        listings = []

        for _, row in df.iterrows():
            listings.append({
                'title': row.get('title', '')[:80],
                'price': row.get('price', 9.99),
                'description': row.get('description', ''),
                'image_urls': row.get('image_urls', '').split(','),
                'category': row.get('category', 'default')
            })

        session['listings'] = listings
    return redirect(url_for('index'))

@app.route('/generate_mercari_csv')
def generate_mercari_csv():
    listings = session.get('listings', [])
    output_data = []

    for item in listings:
        output_data.append({
            "name": item.get('title', '')[:80],
            "price": item.get('price', 9.99),
            "description": item.get('description', '')[:1000],
            "item_condition_name": "Good",
            "image_urls": ",".join(item.get('image_urls', [])[:12]),
            "brand_id": "",
            "category_id": CATEGORY_MAP.get(item.get('category', 'default'), '9999'),
            "category_size_group_id": "",
            "size_id": "",
            "shipping_payer_name": "Seller",
            "shipping_method": "Standard"
        })

    df = pd.DataFrame(output_data)
    output_path = os.path.join(UPLOAD_FOLDER, 'mercari_output.csv')
    df.to_csv(output_path, index=False)
    return send_file(output_path, as_attachment=True)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
