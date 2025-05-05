from flask import Flask, render_template, request, redirect, url_for, session
import os
import pandas as pd
import requests

app = Flask(__name__)
app.secret_key = 'your-secret-key'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
            item_id = str(row['item_id'])
            title = row.get('title', '')
            description = row.get('description', '')
            price = row.get('price', '')

            # Call scraper API to get image URLs
            try:
                response = requests.get(f'https://your-scraper-service-url/api/images?item={item_id}')
                data = response.json()
                image_urls = data.get('image_urls', [])
            except Exception:
                image_urls = []

            listings.append({
                'item_id': item_id,
                'title': title,
                'description': description,
                'price': price,
                'image_urls': image_urls
            })

        session['listings'] = listings

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
