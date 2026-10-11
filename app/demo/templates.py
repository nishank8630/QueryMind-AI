"""Deterministic demo query catalog and parameterized templates for offline demo mode."""
from typing import Dict, Any, Optional

DEMO_QUERY_TEMPLATES: Dict[str, Dict[str, Any]] = {
    # 1. Customers
    "top_customers": {
        "keywords": ["top", "highest", "spent", "spending", "customer"],
        "sql": """SELECT 
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    c.email,
    ROUND(SUM(p.amount)::numeric, 2) AS total_spent
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN payments p ON o.order_id = p.order_id
WHERE o.order_status = 'Completed' AND p.payment_status = 'Success'
GROUP BY c.customer_id, c.first_name, c.last_name, c.email
ORDER BY total_spent DESC
LIMIT 5;""",
        "explanation": "Calculates the top 5 customers with the highest cumulative spending across all completed orders with verified payments.",
        "tables": ["customers", "orders", "payments"],
        "metric": "Customer Lifetime Spending"
    },

    "customers_no_orders": {
        "keywords": ["never", "no order", "zero", "haven't placed"],
        "sql": """SELECT 
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    c.email,
    c.signup_date,
    c.acquisition_channel
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_id IS NULL
ORDER BY c.signup_date ASC
LIMIT 100;""",
        "explanation": "Identifies registered customers who have never placed an order in the store.",
        "tables": ["customers", "orders"],
        "metric": "Inactive Prospects"
    },

    "acquisition_channels": {
        "keywords": ["channel", "acquisition", "brings most", "source"],
        "sql": """SELECT 
    acquisition_channel,
    COUNT(*) AS total_customers,
    ROUND((COUNT(*)::numeric / (SELECT COUNT(*) FROM customers) * 100), 2) AS percentage_share
FROM customers
GROUP BY acquisition_channel
ORDER BY total_customers DESC;""",
        "explanation": "Analyzes the distribution of acquired customers across organic, paid search, social media, and referral channels.",
        "tables": ["customers"],
        "metric": "Customer Acquisition Trends"
    },

    # 2. Sales & Revenue
    "monthly_net_revenue": {
        "keywords": ["monthly", "net revenue", "sales revenue", "trend"],
        "sql": """WITH monthly_sales AS (
    SELECT 
        DATE_TRUNC('month', o.order_date) AS sales_month,
        SUM(oi.quantity * (oi.unit_price - oi.item_discount)) AS gross_sales
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'Completed'
    GROUP BY DATE_TRUNC('month', o.order_date)
),
monthly_refunds AS (
    SELECT 
        DATE_TRUNC('month', r.return_date) AS refund_month,
        SUM(r.refund_amount) AS total_refunds
    FROM returns r
    WHERE r.return_status = 'Approved'
    GROUP BY DATE_TRUNC('month', r.return_date)
)
SELECT 
    TO_CHAR(s.sales_month, 'YYYY-MM') AS month,
    ROUND(s.gross_sales::numeric, 2) AS gross_revenue,
    ROUND(COALESCE(r.total_refunds, 0)::numeric, 2) AS refunds,
    ROUND((s.gross_sales - COALESCE(r.total_refunds, 0))::numeric, 2) AS net_revenue
FROM monthly_sales s
LEFT JOIN monthly_refunds r ON s.sales_month = r.refund_month
ORDER BY month ASC;""",
        "explanation": "Computes monthly net sales revenue by subtracting approved refunds from completed line-item revenues.",
        "tables": ["orders", "order_items", "returns"],
        "metric": "Net Sales Revenue"
    },

    "category_revenue": {
        "keywords": ["category", "categories", "most revenue", "sales by category"],
        "sql": """SELECT 
    cat.category_name,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(oi.quantity) AS total_units_sold,
    ROUND(SUM(oi.quantity * (oi.unit_price - oi.item_discount))::numeric, 2) AS category_revenue
FROM categories cat
JOIN products p ON cat.category_id = p.category_id
JOIN order_items oi ON p.product_id = oi.product_id
JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_status = 'Completed'
GROUP BY cat.category_name
ORDER BY category_revenue DESC;""",
        "explanation": "Aggregates net product sales and unit volume across all 10 product categories for completed orders.",
        "tables": ["categories", "products", "order_items", "orders"],
        "metric": "Category Performance"
    },

    "average_order_value": {
        "keywords": ["average order", "aov", "average order value"],
        "sql": """SELECT 
    ROUND(AVG(p.amount)::numeric, 2) AS average_order_value,
    COUNT(DISTINCT o.order_id) AS total_completed_orders,
    ROUND(SUM(p.amount)::numeric, 2) AS total_settled_amount
FROM orders o
JOIN payments p ON o.order_id = p.order_id
WHERE o.order_status = 'Completed' AND p.payment_status = 'Success';""",
        "explanation": "Measures the average order value (AOV) across all successfully settled and completed customer transactions.",
        "tables": ["orders", "payments"],
        "metric": "Average Order Value (AOV)"
    },

    "cancelled_orders": {
        "keywords": ["cancelled", "canceled", "cancel"],
        "sql": """SELECT 
    sales_channel,
    COUNT(*) AS cancelled_orders_count,
    ROUND(SUM(shipping_cost)::numeric, 2) AS lost_shipping
FROM orders
WHERE order_status = 'Cancelled'
GROUP BY sales_channel
ORDER BY cancelled_orders_count DESC;""",
        "explanation": "Summarizes the number of cancelled purchases broken down by sales channel.",
        "tables": ["orders"],
        "metric": "Cancelled Orders"
    },

    # 3. Products & Inventory
    "low_inventory": {
        "keywords": ["inventory", "low stock", "stock", "out of stock"],
        "sql": """SELECT 
    p.product_id,
    p.product_name,
    c.category_name,
    inv.available_quantity,
    inv.reserved_quantity,
    inv.warehouse_location
FROM inventory inv
JOIN products p ON inv.product_id = p.product_id
JOIN categories c ON p.category_id = c.category_id
WHERE inv.available_quantity < 20
ORDER BY inv.available_quantity ASC;""",
        "explanation": "Queries items with available inventory lower than 20 units across regional warehouses.",
        "tables": ["inventory", "products", "categories"],
        "metric": "Inventory Availability"
    },

    "product_returns": {
        "keywords": ["return rate", "returned", "highest return", "refund"],
        "sql": """SELECT 
    p.product_name,
    c.category_name,
    COUNT(r.return_id) AS total_returns,
    SUM(r.quantity_returned) AS units_returned,
    ROUND(SUM(r.refund_amount)::numeric, 2) AS total_refunded
FROM returns r
JOIN products p ON r.product_id = p.product_id
JOIN categories c ON p.category_id = c.category_id
WHERE r.return_status = 'Approved'
GROUP BY p.product_name, c.category_name
ORDER BY total_returns DESC
LIMIT 10;""",
        "explanation": "Calculates products with the highest return frequencies and total refund claims.",
        "tables": ["returns", "products", "categories"],
        "metric": "Refunds & Return Rate"
    },

    # 4. Payments & Web
    "payment_failures": {
        "keywords": ["failed", "payment failure", "failed payment", "declined"],
        "sql": """SELECT 
    payment_method,
    COUNT(*) AS failed_count,
    ROUND(SUM(amount)::numeric, 2) AS total_failed_amount
FROM payments
WHERE payment_status = 'Failed'
GROUP BY payment_method
ORDER BY failed_count DESC;""",
        "explanation": "Identifies failed transaction volume and total amount by payment provider.",
        "tables": ["payments"],
        "metric": "Payment Failure Rate"
    },

    "website_conversions": {
        "keywords": ["conversion", "device", "traffic source", "session", "web"],
        "sql": """SELECT 
    traffic_source,
    COUNT(*) AS total_sessions,
    SUM(CASE WHEN converted = true THEN 1 ELSE 0 END) AS conversions,
    ROUND((SUM(CASE WHEN converted = true THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100), 2) AS conversion_rate_pct
FROM website_sessions
GROUP BY traffic_source
ORDER BY conversion_rate_pct DESC;""",
        "explanation": "Evaluates digital traffic conversion efficiency across referral channels.",
        "tables": ["website_sessions"],
        "metric": "Website Conversion Rate"
    }
}

def match_demo_template(query: str) -> Optional[Dict[str, Any]]:
    """
    Matches natural language user question to a prevalidated demo template.
    Returns matched template or None.
    """
    q_lower = query.lower()

    # Direct match scoring
    best_match = None
    max_score = 0

    for key, data in DEMO_QUERY_TEMPLATES.items():
        score = sum(1 for kw in data["keywords"] if kw in q_lower)
        if score > max_score:
            max_score = score
            best_match = data

    if max_score > 0 and best_match:
        return best_match
    return None
