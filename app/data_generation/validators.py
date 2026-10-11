"""Validators for referential integrity, business constraints, and data sanity."""
from typing import Dict, List, Any

def validate_dataset_integrity(data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Validate referential integrity and logical consistency across all generated tables.
    Returns status and detailed diagnostics.
    """
    errors = []
    
    # Primary Key sets
    cat_ids = {c["category_id"] for c in data["categories"]}
    sup_ids = {s["supplier_id"] for s in data["suppliers"]}
    prod_ids = {p["product_id"] for p in data["products"]}
    cust_ids = {c["customer_id"] for c in data["customers"]}
    order_ids = {o["order_id"] for o in data["orders"]}

    # 1. Product FK validation
    for p in data["products"]:
        if p["category_id"] not in cat_ids:
            errors.append(f"Product {p['product_id']} has invalid category_id {p['category_id']}")
        if p["supplier_id"] not in sup_ids:
            errors.append(f"Product {p['product_id']} has invalid supplier_id {p['supplier_id']}")
        if p["unit_cost"] <= 0 or p["list_price"] <= 0:
            errors.append(f"Product {p['product_id']} has non-positive cost or price")

    # 2. Inventory FK validation
    for inv in data["inventory"]:
        if inv["product_id"] not in prod_ids:
            errors.append(f"Inventory {inv['inventory_id']} has invalid product_id {inv['product_id']}")
        if inv["available_quantity"] < 0 or inv["reserved_quantity"] < 0:
            errors.append(f"Inventory {inv['inventory_id']} has negative quantities")

    # 3. Order FK validation
    for o in data["orders"]:
        if o["customer_id"] not in cust_ids:
            errors.append(f"Order {o['order_id']} has invalid customer_id {o['customer_id']}")

    # 4. Order Item FK validation
    for oi in data["order_items"]:
        if oi["order_id"] not in order_ids:
            errors.append(f"OrderItem {oi['order_item_id']} references missing order {oi['order_id']}")
        if oi["product_id"] not in prod_ids:
            errors.append(f"OrderItem {oi['order_item_id']} references missing product {oi['product_id']}")
        if oi["quantity"] <= 0:
            errors.append(f"OrderItem {oi['order_item_id']} has invalid quantity {oi['quantity']}")

    # 5. Payment FK validation
    for pay in data["payments"]:
        if pay["order_id"] not in order_ids:
            errors.append(f"Payment {pay['payment_id']} references missing order {pay['order_id']}")
        if pay["amount"] < 0:
            errors.append(f"Payment {pay['payment_id']} has negative amount {pay['amount']}")

    # 6. Return FK validation
    for ret in data["returns"]:
        if ret["order_id"] not in order_ids:
            errors.append(f"Return {ret['return_id']} references missing order {ret['order_id']}")
        if ret["product_id"] not in prod_ids:
            errors.append(f"Return {ret['return_id']} references missing product {ret['product_id']}")
        if ret["refund_amount"] < 0:
            errors.append(f"Return {ret['return_id']} has negative refund amount")

    # 7. Website Sessions validation
    for s in data["website_sessions"]:
        if s["customer_id"] is not None and s["customer_id"] not in cust_ids:
            errors.append(f"Session {s['session_id']} references non-existent customer {s['customer_id']}")

    is_valid = len(errors) == 0
    return {
        "is_valid": is_valid,
        "error_count": len(errors),
        "errors": errors[:20],  # sample first 20 errors if any
        "table_counts": {k: len(v) for k, v in data.items()}
    }
