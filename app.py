from flask import Flask, render_template, request, redirect, url_for, session, send_file
import pandas as pd
import json
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load category mapping
with open('category_mapper.json') as f:
    CATEGORY_MAP = json.load(f)

@app.route('/')
def index():
    listings = session.get('listings', [])
    return render_template('index.html', listings=listings)

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    file = request.files['file']
    if file and file.filename.endswith('.csv'):
        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)

        df = pd.read_csv(path)
        listings = []
        output_data = []

        for _, row in df.iterrows():
            title = row.get('title', '')[:80]
            price = row.get('price', 9.99)
            description = row.get('description', '')[:1000]
            images = str(row.get('image_urls', '')).split(',')
            category = row.get('category', 'default')

            listings.append({
                'title': title,
                'price': price,
                'description': description,
                'image_urls': images,
                'category': category
            })

            output_data.append({
                "name": title,
                "price": price,
                "description": description,
                "item_condition_name": "Good",
                "image_urls": ",".join(images[:12]),
                "brand_id": "",
                "category_id": CATEGORY_MAP.get(category, '9999'),
                "category_size_group_id": "",
                "size_id": "",
                "shipping_payer_name": "Seller",
                "shipping_method": "Standard"
            })

        session['listings'] = listings
        df_out = pd.DataFrame(output_data)
        df_out.to_csv(os.path.join(UPLOAD_FOLDER, 'mercari_output.csv'), index=False)

    return redirect(url_for('index'))

@app.route('/download_mercari_csv')
def download_mercari_csv():
    return send_file('uploads/mercari_output.csv', as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
