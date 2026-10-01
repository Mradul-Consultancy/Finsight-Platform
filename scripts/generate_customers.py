# scripts/generate_customers.py
"""
Generates realistic customer demographics for FinSight banking analytics.
Configurable number of customers with income distributions and state mappings.
"""

import os
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

FIRST_NAMES = [
    "Aarav", "Aditi", "Rohan", "Priya", "Vikram", "Neha", "Rahul", "Ananya",
    "Siddharth", "Pooja", "Arjun", "Kavita", "Amit", "Sneha", "Karan", "Divya",
    "Deepak", "Ritu", "Manish", "Sunita", "Rajesh", "Meera", "Suresh", "Geeta"
]

LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Gupta", "Singh", "Kumar", "Iyer", "Nair",
    "Reddy", "Rao", "Joshi", "Chopra", "Mehta", "Bose", "Das", "Choudhury"
]

INDIAN_STATES = [
    "Maharashtra", "Karnataka", "Tamil Nadu", "Delhi", "Uttar Pradesh",
    "Gujarat", "West Bengal", "Telangana", "Kerala", "Rajasthan", "Haryana"
]

def generate_customers(n=50000, seed=42) -> pd.DataFrame:
    np.random.seed(seed)
    random.seed(seed)
    
    customers = []
    base_date = datetime(2023, 1, 1)

    # Demographic income distributions
    # 20% Students / Entry (1.5L - 4.5L)
    # 50% Mass Market / Salaried (4.5L - 14L)
    # 20% Affluent (15L - 24L)
    # 10% Premium (> 25L)
    
    for i in range(1, n + 1):
        cust_id = f"CUST_{i:07d}"
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        name = f"{first} {last}"
        gender = random.choice(["MALE", "FEMALE", "OTHER"])
        state = random.choice(INDIAN_STATES)
        city = f"{state} Metro"
        
        # Age distribution
        r = random.random()
        if r < 0.20:
            age = random.randint(18, 24)
            income = round(random.uniform(150000, 480000), 2)
            c_type = "STUDENT" if age < 23 else "RETAIL"
        elif r < 0.70:
            age = random.randint(25, 45)
            income = round(random.uniform(450000, 1400000), 2)
            c_type = "SALARIED"
        elif r < 0.85:
            age = random.randint(35, 59)
            income = round(random.uniform(1500000, 2400000), 2)
            c_type = "BUSINESS" if random.random() < 0.3 else "SALARIED"
        elif r < 0.95:
            age = random.randint(35, 58)
            income = round(random.uniform(2500000, 6000000), 2)
            c_type = "HIGH_NET_WORTH"
        else:
            age = random.randint(60, 78)
            income = round(random.uniform(350000, 1800000), 2)
            c_type = "SENIOR_CITIZEN"

        dob = datetime.now() - timedelta(days=int(age * 365.25) + random.randint(0, 360))
        created = base_date - timedelta(days=random.randint(30, 1200))

        customers.append({
            "customer_id": cust_id,
            "customer_name": name,
            "date_of_birth": dob.strftime("%Y-%m-%d"),
            "age": age,
            "gender": gender,
            "city": city,
            "state": state,
            "customer_type": c_type,
            "annual_income": income,
            "created_at": created.strftime("%Y-%m-%d %H:%M:%S")
        })

    return pd.DataFrame(customers)

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "..", "data", "generated")
    os.makedirs(out_dir, exist_ok=True)
    # Default generate 25,000 customers for fast local development (can scale up)
    df = generate_customers(25000)
    df.to_csv(os.path.join(out_dir, "customers.csv"), index=False)
    print(f"Generated {len(df)} customers.")
