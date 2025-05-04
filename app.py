from flask import Flask, render_template, request, redirect, make_response
import pandas as pd
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/', methods=['GET', 'POST'])
def index():
    listings = []
    if request.method == 'POST':
        file = request.files['csv_file']
        if file:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'eBay-active-listings.csv')
            file.save(filepath)
            df = pd.read_csv(filepath)
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
