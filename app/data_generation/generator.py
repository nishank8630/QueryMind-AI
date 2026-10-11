"""Deterministic synthetic business dataset generator with realistic e-commerce distributions."""
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any
import numpy as np
from faker import Faker

fake = Faker()

def generate_synthetic_data(
    num_customers: int = 2000,
    num_products: int = 100,
    num_categories: int = 10,
    num_suppliers: int = 20,
    num_orders: int = 10000,
    num_sessions: int = 15000,
    seed: int = 42
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Generate realistic e-commerce synthetic dataset maintaining referential integrity.
    Uses a fixed random seed for strict reproducibility.
    """
    random.seed(seed)
    np.random.seed(seed)
    Faker.seed(seed)

    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 12, 31)
    total_days = (end_date - start_date).days

    # 1. CATEGORIES (10)
    category_names = [
        ("Electronics", "High-tech consumer gadgets, smartphones, laptops, and wearables"),
        ("Home & Kitchen", "Modern cookware, dining sets, small appliances, and smart home tools"),
        ("Apparel", "Men and women fashion, seasonal clothing, footwear, and accessories"),
        ("Health & Beauty", "Personal wellness, cosmetics, organic skincare, and nutritional supplements"),
        ("Sports & Outdoors", "Athletic gear, fitness machines, camping equipment, and outdoor recreation"),
        ("Books & Stationery", "Bestsellers, educational guides, office supplies, and notebooks"),
        ("Toys & Games", "Family board games, educational robotics, puzzle kits, and collectibles"),
        ("Automotive", "Car care essentials, electronics, tools, and automotive accessories"),
        ("Pet Supplies", "Organic pet food, grooming supplies, toys, and veterinary essentials"),
        ("Office Furniture", "Ergonomic chairs, standing desks, monitors, and workspace lighting")
    ]
    categories = []
    for i, (name, desc) in enumerate(category_names[:num_categories], 1):
        categories.append({
            "category_id": i,
            "category_name": name,
            "category_description": desc
        })

    # 2. SUPPLIERS (20)
    regions = ["North America", "East Asia", "Europe", "South America", "South Asia"]
    suppliers = []
    for i in range(1, num_suppliers + 1):
        suppliers.append({
            "supplier_id": i,
            "supplier_name": f"{fake.company()} Supply Co.",
            "supplier_region": random.choice(regions),
            "supplier_rating": round(random.uniform(3.5, 4.9), 2)
        })

    # 3. PRODUCTS (100)
    products = []
    category_profit_margins = {1: 0.35, 2: 0.45, 3: 0.55, 4: 0.60, 5: 0.40, 6: 0.30, 7: 0.45, 8: 0.35, 9: 0.50, 10: 0.40}
    product_base_costs = {1: 150.0, 2: 45.0, 3: 30.0, 4: 25.0, 5: 60.0, 6: 15.0, 7: 20.0, 8: 40.0, 9: 22.0, 10: 120.0}

    for i in range(1, num_products + 1):
        cat_id = ((i - 1) % len(categories)) + 1
        sup_id = ((i - 1) % len(suppliers)) + 1
        base_cost = product_base_costs.get(cat_id, 35.0) * random.uniform(0.6, 2.2)
        margin = category_profit_margins.get(cat_id, 0.40)
        list_price = base_cost / (1.0 - margin)

        created_days = random.randint(0, 120)
        created_at = start_date + timedelta(days=created_days)

        products.append({
            "product_id": i,
            "product_name": f"{fake.catch_phrase().title()} Model-{i}",
            "category_id": cat_id,
            "supplier_id": sup_id,
            "unit_cost": round(base_cost, 2),
            "list_price": round(list_price, 2),
            "created_at": created_at,
            "is_active": True
        })

    # 4. INVENTORY (1:1 with products)
    warehouses = ["Central Distribution Dallas", "West Coast Hub Seattle", "East Coast Depot Newark", "Midwest Logistics Chicago"]
    inventory = []
    for p in products:
        # Some products have low inventory to create realistic analytics cases
        is_low_stock = random.random() < 0.15
        avail = random.randint(2, 15) if is_low_stock else random.randint(50, 650)
        reserved = random.randint(0, min(15, avail))
        inventory.append({
            "inventory_id": p["product_id"],
            "product_id": p["product_id"],
            "warehouse_location": random.choice(warehouses),
            "available_quantity": avail,
            "reserved_quantity": reserved,
            "last_updated": end_date - timedelta(days=random.randint(0, 10))
        })

    # 5. CUSTOMERS (2000)
    segments = ["Standard", "Premium", "Enterprise", "Inactive"]
    channels = ["Organic Search", "Paid Search", "Social Media", "Email Referral", "Affiliate"]
    customers = []
    for i in range(1, num_customers + 1):
        signup_offset = random.randint(0, total_days - 30)
        signup_dt = (start_date + timedelta(days=signup_offset)).date()
        customers.append({
            "customer_id": i,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": f"cust_{i}_{fake.unique.user_name()}@{fake.free_email_domain()}",
            "city": fake.city(),
            "state": fake.state_abbr(),
            "country": "United States",
            "signup_date": signup_dt,
            "customer_segment": random.choices(segments, weights=[0.60, 0.25, 0.05, 0.10])[0],
            "acquisition_channel": random.choices(channels, weights=[0.35, 0.25, 0.20, 0.12, 0.08])[0],
            "is_active": random.random() > 0.08
        })

    # 6. ORDERS & ORDER ITEMS (10,000 orders)
    # Power-law customer spending: top 20% customers place 60% of orders.
    # ~15% customers never place an order.
    ordering_customer_count = int(num_customers * 0.85)
    ordering_customers = customers[:ordering_customer_count]
    weights = np.random.pareto(a=1.5, size=len(ordering_customers))
    weights /= weights.sum()

    order_statuses = ["Completed", "Processing", "Cancelled"]
    sales_channels = ["Web Store", "Mobile App", "Marketplace", "Phone Support"]

    orders = []
    order_items = []
    payments = []
    returns = []

    order_item_id_counter = 1
    payment_id_counter = 1
    return_id_counter = 1

    # Product popularity weights (Zipf-like distribution)
    prod_weights = np.array([1.0 / (idx + 1) ** 0.85 for idx in range(len(products))])
    prod_weights /= prod_weights.sum()

    for o_id in range(1, num_orders + 1):
        cust = np.random.choice(ordering_customers, p=weights)
        cust_signup = datetime.combine(cust["signup_date"], datetime.min.time())

        # Order date occurs after signup date
        remaining_days = max(1, (end_date - cust_signup).days)
        order_dt = cust_signup + timedelta(days=random.randint(0, remaining_days), hours=random.randint(8, 22), minutes=random.randint(0, 59))
        if order_dt > end_date:
            order_dt = end_date - timedelta(hours=random.randint(1, 48))

        status = random.choices(order_statuses, weights=[0.86, 0.06, 0.08])[0]
        channel = random.choices(sales_channels, weights=[0.55, 0.35, 0.07, 0.03])[0]

        discount = round(random.choice([0.0, 0.0, 5.0, 10.0, 15.0, 20.0]), 2)
        shipping_cost = round(random.choice([0.0, 4.99, 9.99, 14.99]), 2)

        # 1 to 4 items per order
        num_items = random.choices([1, 2, 3, 4], weights=[0.50, 0.30, 0.15, 0.05])[0]
        selected_prods = np.random.choice(products, size=num_items, replace=False, p=prod_weights)

        order_subtotal = 0.0
        current_order_items = []

        for p in selected_prods:
            qty = random.choices([1, 2, 3, 5], weights=[0.75, 0.18, 0.05, 0.02])[0]
            unit_price = float(p["list_price"])
            item_disc = round(random.choice([0.0, 0.0, 2.0, 5.0]), 2)
            if item_disc >= unit_price:
                item_disc = 0.0
            line_total = (unit_price * qty) - (item_disc * qty)
            order_subtotal += max(0.0, line_total)

            item_dict = {
                "order_item_id": order_item_id_counter,
                "order_id": o_id,
                "product_id": p["product_id"],
                "quantity": qty,
                "unit_price": unit_price,
                "item_discount": item_disc
            }
            order_items.append(item_dict)
            current_order_items.append(item_dict)
            order_item_id_counter += 1

        total_order_amount = max(0.0, order_subtotal + shipping_cost - discount)

        orders.append({
            "order_id": o_id,
            "customer_id": cust["customer_id"],
            "order_date": order_dt,
            "order_status": status,
            "sales_channel": channel,
            "shipping_city": cust["city"],
            "shipping_state": cust["state"],
            "shipping_cost": shipping_cost,
            "discount_amount": discount
        })

        # PAYMENT
        # If cancelled, payment might have failed or refunded
        if status == "Cancelled":
            pay_status = random.choice(["Failed", "Refunded"])
        else:
            pay_status = "Success" if random.random() > 0.03 else "Failed"

        pay_method = random.choices(
            ["Credit Card", "PayPal", "Apple Pay", "Bank Transfer"],
            weights=[0.58, 0.24, 0.14, 0.04]
        )[0]

        payments.append({
            "payment_id": payment_id_counter,
            "order_id": o_id,
            "payment_date": order_dt + timedelta(minutes=random.randint(1, 15)),
            "payment_method": pay_method,
            "amount": round(total_order_amount, 2),
            "payment_status": pay_status,
            "transaction_reference": f"TXN-{o_id}-{uuid.uuid4().hex[:10].upper()}"
        })
        payment_id_counter += 1

        # RETURNS (Only for completed orders with successful payment, ~7% return rate)
        if status == "Completed" and pay_status == "Success" and random.random() < 0.07:
            ret_item = random.choice(current_order_items)
            ret_qty = random.randint(1, ret_item["quantity"])
            refund_val = round(ret_qty * (ret_item["unit_price"] - ret_item["item_discount"]), 2)
            ret_reason = random.choice(["Defective", "Wrong Size", "Not as Described", "Buyer Remorse"])
            ret_status = random.choices(["Approved", "Rejected"], weights=[0.88, 0.12])[0]

            returns.append({
                "return_id": return_id_counter,
                "order_id": o_id,
                "product_id": ret_item["product_id"],
                "return_date": order_dt + timedelta(days=random.randint(3, 14)),
                "quantity_returned": ret_qty,
                "refund_amount": refund_val,
                "return_reason": ret_reason,
                "return_status": ret_status
            })
            return_id_counter += 1

    # 7. WEBSITE SESSIONS (15,000)
    devices = ["Desktop", "Mobile", "Tablet"]
    traffic_srcs = ["Google Search", "Direct", "Facebook Ads", "Email Newsletter", "Referral"]
    sessions = []
    for s_id in range(1, num_sessions + 1):
        # 60% of sessions are by registered customers, 40% anonymous
        is_registered = random.random() < 0.60
        cust_id = random.choice(customers)["customer_id"] if is_registered else None

        s_start = start_date + timedelta(
            days=random.randint(0, total_days),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        duration_mins = random.randint(1, 45)
        s_end = s_start + timedelta(minutes=duration_mins)

        pages = random.randint(1, 15)
        # Higher pages visited correlate with higher conversion rate
        conv_prob = min(0.35, 0.02 * pages + (0.05 if is_registered else 0.01))
        converted = random.random() < conv_prob

        sessions.append({
            "session_id": s_id,
            "customer_id": cust_id,
            "session_start": s_start,
            "session_end": s_end,
            "device_type": random.choices(devices, weights=[0.52, 0.40, 0.08])[0],
            "traffic_source": random.choices(traffic_srcs, weights=[0.40, 0.25, 0.18, 0.10, 0.07])[0],
            "pages_viewed": pages,
            "converted": converted
        })

    return {
        "categories": categories,
        "suppliers": suppliers,
        "products": products,
        "inventory": inventory,
        "customers": customers,
        "orders": orders,
        "order_items": order_items,
        "payments": payments,
        "returns": returns,
        "website_sessions": sessions
    }
