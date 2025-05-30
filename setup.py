import pandas as pd
import sqlite3
import os

# Paths
csv_path = "data/raw/SuperStoreOrders.csv"
db_path = "data/SuperStore.db"

# Load data
df = pd.read_csv(csv_path)

# Clean and normalize column names
df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

# Debug: print column names to verify
print("✅ Columns loaded:", df.columns.tolist())

# Ensure required columns exist
required_cols = ["order_id", "product_id", "customer_name", "category", "sub_category", "product_name"]
for col in required_cols:
    if col not in df.columns:
        raise KeyError(f"❌ Missing expected column: {col}")

# Create output folder if it doesn't exist
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# Connect to SQLite
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# --- Create Category Table ---
df["category_id"] = df.groupby(["category", "sub_category"]).ngroup() + 1
categories = df[["category_id", "category", "sub_category"]].drop_duplicates()
categories.to_sql("categories", conn, if_exists="replace", index=False)

# --- Create Products Table ---
df["product_id_clean"] = df["product_id"].astype(str)
products = df[["product_id_clean", "product_name", "category_id"]].drop_duplicates()
products.rename(columns={"product_id_clean": "product_id"}, inplace=True)
products.to_sql("products", conn, if_exists="replace", index=False)

# --- Create Customers Table ---
df["customer_id"] = df["customer_name"].astype("category").cat.codes + 1
customers = df[["customer_id", "customer_name", "segment"]].drop_duplicates()
customers.to_sql("customers", conn, if_exists="replace", index=False)

# --- Create Regions Table ---
df["region_id"] = df.groupby(["region", "market", "country", "state"]).ngroup() + 1
regions = df[["region_id", "region", "market", "country", "state"]].drop_duplicates()
regions.to_sql("regions", conn, if_exists="replace", index=False)

# --- Create Orders Table ---
df["order_id_clean"] = df["order_id"].astype(str)
orders = df[["order_id_clean", "order_date", "ship_date", "ship_mode", "order_priority", "year", "customer_id", "region_id"]].drop_duplicates()
orders.rename(columns={"order_id_clean": "order_id"}, inplace=True)
orders.to_sql("orders", conn, if_exists="replace", index=False)

# --- Create Order Items Table ---
df["order_item_id"] = df.index + 1
order_items = df[[
    "order_item_id", "order_id_clean", "product_id_clean", "quantity",
    "discount", "sales", "profit", "shipping_cost"
]].copy()
order_items.rename(columns={
    "order_id_clean": "order_id",
    "product_id_clean": "product_id"
}, inplace=True)
order_items.to_sql("order_items", conn, if_exists="replace", index=False)

# Done
conn.commit()
conn.close()
print("✅ SuperStore.db created with multiple relational tables.")
