import time
import requests
from bs4 import BeautifulSoup
import pandas as pd
import undetected_chromedriver as uc

# Suppress WinError 6 on Windows
_orig_quit = uc.Chrome.quit

def _safe_quit(self):
    try:
        _orig_quit(self)
    except OSError:
        pass

uc.Chrome.quit = _safe_quit

HEADERS = {'User-Agent': 'Mozilla/5.0'}
TARGET_ITEMS = ['onion', 'onions', 'tomato', 'tomatoes', 'cabbage']


def extract_products(soup, item_sel, name_sel, price_sel, source):
    products = []
    for item in soup.select(item_sel):
        name_elem = item.select_one(name_sel)
        price_elem = item.select_one(price_sel)
        if name_elem and price_elem:
            name = name_elem.text.strip()
            price = price_elem.text.strip()
            if any(term in name.lower() for term in TARGET_ITEMS):
                products.append({'Item': name, 'Price': price, 'Source': source})
    return products


def fetch_with_selenium(url, item_sel, name_sel, price_sel, source):
    print(f"🌐 Using Selenium for {source}")
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-blink-features=AutomationControlled')

    driver = uc.Chrome(options=options)
    try:
        driver.get(url)
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
    finally:
        try:
            driver.close()
            driver.quit()
        except:
            pass

    return extract_products(soup, item_sel, name_sel, price_sel, source)


def scrape_naivas():
    url = 'https://naivas.online/search?q=onion+tomato+cabbage'
    print("🔍 Scraping Naivas...")
    try:
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        if not soup.select('div.product-card'):
            raise ValueError
        return extract_products(soup, 'div.product-card', 'p.product-title', 'span.money', 'Naivas')
    except:
        return fetch_with_selenium(url, 'div.product-card', 'p.product-title', 'span.money', 'Naivas')


def scrape_quickmart():
    url = 'https://quickmart.co.ke/catalogsearch/result/?q=onion+tomato+cabbage'
    print("🔍 Scraping Quickmart...")
    try:
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        if not soup.select('li.product-item'):
            raise ValueError
        return extract_products(soup, 'li.product-item', 'a.product-item-link', 'span.price', 'Quickmart')
    except:
        return fetch_with_selenium(url, 'li.product-item', 'a.product-item-link', 'span.price', 'Quickmart')


def scrape_kiondo():
    url = 'https://kiondomarket.co.ke/search?q=onion+tomato+cabbage'
    print("🔍 Scraping Kiondo Market...")
    try:
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        if not soup.select('div.card-body'):
            raise ValueError
        return extract_products(soup, 'div.card-body', 'p.card-text', 'h5.card-title', 'Kiondo Market')
    except:
        return fetch_with_selenium(url, 'div.card-body', 'p.card-text', 'h5.card-title', 'Kiondo Market')


def compare_prices():
    all_data = scrape_naivas() + scrape_quickmart() + scrape_kiondo()
    if not all_data:
        print("❌ No products found.")
        return

    df = pd.DataFrame(all_data)
    df.sort_values(by='Item', inplace=True)
    print("\n📊 Price Comparison:\n", df.to_string(index=False))
    df.to_excel("Vegetable_Price_Comparison.xlsx", index=False)
    print("\n✅ Data exported to 'Vegetable_Price_Comparison.xlsx'")


if __name__ == "__main__":
    compare_prices()


