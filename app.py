from flask import Flask, render_template, request, redirect, jsonify
import os
import csv
import pandas as pd
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def scrape_ebay_images(item_number):
    url = f"https://www.ebay.com/itm/{item_number}"
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1200x800')
    options.binary_location = '/usr/bin/chromium'

    try:
        service = Service(executable_path='/usr/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        time.sleep(4)
        html = driver.page_source
        driver.quit()

        soup = BeautifulSoup(html, 'html.parser')
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'mediaList' in script.string:
                text = script.string
                start = text.find('mediaList') + len('mediaList') + 1
                start_bracket = text.find('[', start)
                end = start_bracket + 1
                bracket_count = 1
                while end < len(text) and bracket_count > 0:
                    if text[end] == '[':
                        bracket_count += 1
                    elif text[end] == ']':
                        bracket_count -= 1
                    end += 1
                raw_json = text[start_bracket:end]
                media_list = json.loads(raw_json)
                urls = []
                for media in media_list:
                    try:
                        url = media["image"]["zoomImg"]["URL"]
                        if url:
                            urls.append(url)
                    except KeyError:
                        continue
                return urls
    except Exception as e:
        return []

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
            item_id = str(listing.get('Item ID') or listing.get('ItemID') or listing.get('item_id'))
            images = scrape_ebay_images(item_id)
            listing['images'] = images

    return render_template('index.html', listings=listings)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
