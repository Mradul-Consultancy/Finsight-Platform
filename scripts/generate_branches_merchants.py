# scripts/generate_branches_merchants.py
"""
Generates 100 branches across 5 national regions and 5,000 merchants across 8 categories.
"""

import os
import random
import pandas as pd

REGIONS = {
    "NORTH": ["Delhi", "Punjab", "Haryana", "Uttar Pradesh", "Rajasthan"],
    "SOUTH": ["Karnataka", "Tamil Nadu", "Telangana", "Kerala", "Andhra Pradesh"],
    "EAST": ["West Bengal", "Odisha", "Bihar", "Assam", "Jharkhand"],
    "WEST": ["Maharashtra", "Gujarat", "Goa", "Madhya Pradesh"],
    "CENTRAL": ["Chhattisgarh", "Madhya Pradesh", "Uttar Pradesh"]
}

MERCHANT_CATEGORIES = [
    "GROCERY", "FUEL", "RESTAURANT", "TRAVEL",
    "HEALTHCARE", "RETAIL", "EDUCATION", "UTILITIES"
]

def generate_branches(n=100) -> pd.DataFrame:
    branches = []
    region_keys = list(REGIONS.keys())
    for i in range(1, n + 1):
        branch_id = f"BR_{i:04d}"
        region = random.choice(region_keys)
        state = random.choice(REGIONS[region])
        city = f"{state} City-{((i - 1) % 15) + 1}"
        branch_name = f"FinSight Bank {city} Branch"
        branches.append({
            "branch_id": branch_id,
            "branch_name": branch_name,
            "city": city,
            "state": state,
            "region": region
        })
    return pd.DataFrame(branches)

def generate_merchants(n=5000) -> pd.DataFrame:
    merchants = []
    all_states = [s for sublist in REGIONS.values() for s in sublist]
    for i in range(1, n + 1):
        merchant_id = f"MERCH_{i:06d}"
        category = random.choice(MERCHANT_CATEGORIES)
        state = random.choice(all_states)
        city = f"{state} Hub"
        merchant_name = f"{category.capitalize()} Mart #{i}"
        merchants.append({
            "merchant_id": merchant_id,
            "merchant_name": merchant_name,
            "merchant_category": category,
            "city": city,
            "state": state
        })
    return pd.DataFrame(merchants)

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "..", "data", "generated")
    os.makedirs(out_dir, exist_ok=True)
    df_branches = generate_branches(100)
    df_merchants = generate_merchants(5000)
    df_branches.to_csv(os.path.join(out_dir, "branches.csv"), index=False)
    df_merchants.to_csv(os.path.join(out_dir, "merchants.csv"), index=False)
    print(f"Generated {len(df_branches)} branches and {len(df_merchants)} merchants.")
