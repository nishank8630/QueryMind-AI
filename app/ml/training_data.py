"""Synthetic training data generator for schema routing classifier."""
import json
import random
from pathlib import Path
from typing import List, Dict, Any
from app.config import get_settings

settings = get_settings()

QUERY_TEMPLATES = [
    # Customers
    ("Who are the top customers by spending?", ["customers", "orders", "payments"]),
    ("How many new customers registered in January?", ["customers"]),
    ("List customers who signed up via organic search.", ["customers"]),
    ("Which customers live in California?", ["customers"]),
    ("Show me inactive users and their emails.", ["customers"]),
    ("What is the customer retention rate?", ["customers", "orders"]),
    ("Find customers who haven't placed an order yet.", ["customers", "orders"]),
    ("List enterprise segment clients and their signup dates.", ["customers"]),
    ("Find all shoppers from New York state.", ["customers"]),
    ("Which channel acquires the most premium customers?", ["customers"]),

    # Products & Categories & Suppliers
    ("Which products have a list price over 100 dollars?", ["products"]),
    ("What are the most expensive products in our catalog?", ["products"]),
    ("Show all product categories and descriptions.", ["categories"]),
    ("Which category has the highest number of active products?", ["categories", "products"]),
    ("List all suppliers in North America with high ratings.", ["suppliers"]),
    ("Who supplies our electronics merchandise?", ["suppliers", "products", "categories"]),
    ("Show products created in the last 60 days.", ["products"]),
    ("Calculate the average unit cost of apparel items.", ["products", "categories"]),
    ("Find suppliers with ratings below 4.0.", ["suppliers"]),
    ("List active products sorted by list price descending.", ["products"]),

    # Orders & Order Items
    ("What is the total number of orders placed this year?", ["orders"]),
    ("Show all cancelled orders and their shipping states.", ["orders"]),
    ("Calculate average discount amount on orders.", ["orders"]),
    ("How many orders were completed via mobile app?", ["orders"]),
    ("Show order items with quantity greater than 3.", ["order_items"]),
    ("What is the total item discount granted on electronics?", ["order_items", "products", "categories"]),
    ("List orders with shipping cost greater than 10 dollars.", ["orders"]),
    ("Show all line items for order number 502.", ["order_items"]),
    ("How many units were sold for product 12?", ["order_items"]),
    ("What are the total units ordered across all items?", ["order_items"]),

    # Payments
    ("How many payment transactions failed?", ["payments"]),
    ("What is the total amount settled through PayPal?", ["payments"]),
    ("List all transactions with payment status Refunded.", ["payments"]),
    ("Which payment method is used most frequently?", ["payments"]),
    ("Show payments processed in March.", ["payments"]),
    ("Find the largest single transaction payment.", ["payments"]),
    ("Show orders where payment status is pending.", ["orders", "payments"]),

    # Returns
    ("What is the total refund amount from approved returns?", ["returns"]),
    ("Which product has the highest return frequency?", ["returns", "products"]),
    ("Show all returns due to Defective reason.", ["returns"]),
    ("How many returns were rejected by customer service?", ["returns"]),
    ("List returns processed for order 1044.", ["returns"]),
    ("What percentage of orders resulted in a return?", ["returns", "orders"]),

    # Inventory
    ("Which products have less than 10 units in stock?", ["inventory", "products"]),
    ("Show available stock in the Dallas warehouse.", ["inventory"]),
    ("Which warehouse has the highest reserved quantity?", ["inventory"]),
    ("Find out of stock products.", ["inventory", "products"]),
    ("What is the total available inventory across all locations?", ["inventory"]),

    # Website Sessions
    ("What is the website conversion rate by device type?", ["website_sessions"]),
    ("Which traffic source brings the most website visits?", ["website_sessions"]),
    ("Show desktop sessions with more than 5 pages viewed.", ["website_sessions"]),
    ("How many anonymous visitors visited the site?", ["website_sessions"]),
    ("Compare mobile versus desktop session counts.", ["website_sessions"]),

    # Multi-Table Complex Analytics
    ("What was our monthly net sales revenue after returns?", ["orders", "order_items", "returns"]),
    ("Which category generates the highest net revenue?", ["categories", "products", "order_items", "orders"]),
    ("Find the five customers who spent the most money.", ["customers", "orders", "payments"]),
    ("What is the average order value for completed purchases?", ["orders", "payments"]),
    ("Show profit margins per category based on product unit costs.", ["categories", "products", "order_items", "orders"]),
    ("Which suppliers produce our best selling items?", ["suppliers", "products", "order_items"]),
    ("List customers with returns greater than 50 dollars.", ["customers", "orders", "returns"])
]

PARAPHRASE_PREFIXES = [
    "Could you tell me", "Please show", "I want to see", "Find", "Calculate",
    "Display", "What is", "Can you give me", "Fetch", "Give me a breakdown of"
]

def generate_schema_router_dataset(num_samples: int = 500, seed: int = 42) -> List[Dict[str, Any]]:
    """Generates varied training examples with label arrays."""
    random.seed(seed)
    dataset = []

    for q_text, tables in QUERY_TEMPLATES:
        # Base template
        dataset.append({"question": q_text, "tables": tables})
        
        # Paraphrased variations
        for p in PARAPHRASE_PREFIXES:
            q_var = f"{p} {q_text[0].lower()}{q_text[1:]}"
            dataset.append({"question": q_var, "tables": tables})

    # Shuffle deterministically
    random.shuffle(dataset)
    return dataset[:num_samples]

if __name__ == "__main__":
    out_file = settings.DATA_DIR / "schema_router_train.json"
    data = generate_schema_router_dataset(num_samples=600)
    out_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Generated {len(data)} schema router training examples -> {out_file}")
