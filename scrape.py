

import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from supabase import create_client, Client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

URL = "https://www.argos.co.uk/browse/technology/televisions-and-accessories/televisions/c:30106/opt/sort:new-arrivals/"
headers = {"User-Agent": "Mozilla/5.0"}

response = requests.get(URL, headers=headers, timeout=20)
soup = BeautifulSoup(response.text, "html.parser")

products = []
items = soup.select('.ds-c-product-card')

for item in items:
    # Product name
    name_tag = item.select_one('.ds-c-product-card__title')
    product_name = name_tag.text.strip() if name_tag else "Unknown"

    # Price
    price_tag = item.select_one('.ds-c-price__price')
    price = float(price_tag.text.strip().replace("£", "").replace(",", "")) if price_tag else 0.0

    # Brand (first word of product name)
    brand = product_name.split()[0] if product_name != "Unknown" else "Unknown"

    # Stock status
    text = item.get_text().lower()
    stock_status = "Out of stock" if "out of stock" in text or "unavailable" in text else "In stock"

    # Price tier
    if price < 300:
        price_tier = "<£300"
    elif price <= 600:
        price_tier = "£300–£600"
    else:
        price_tier = ">£600"

    # Append row
    products.append([product_name, brand, price, stock_status, datetime.now().isoformat(), price_tier])

df = pd.DataFrame(products, columns=[
    "product_name", "brand", "price", "stock_status", "scraped_at", "price_tier"
])


dfs = []
for i in range(3):  # simulate 3 different days
    df_temp = df.copy()
    df_temp['scraped_at'] = (datetime.now() - timedelta(days=i)).isoformat()
    df_temp['stock_status'] = df_temp['stock_status'].apply(
        lambda x: "Out of stock" if np.random.rand() < 0.2 else "In stock"
    )
    dfs.append(df_temp)

df_simulated = pd.concat(dfs)


data = df_simulated.to_dict(orient='records')
response = supabase.table("argos_electronics").insert(data).execute()
print("✅ Data inserted into Supabase!")
print(response)


latest = supabase.table("argos_electronics").select("*").order("scraped_at", desc=True).limit(5).execute()
print("Latest 5 rows:")
print(latest.data)