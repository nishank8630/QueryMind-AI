# Verified Production SQL Examples

## Example 1: Top 5 Highest Spending Customers
```sql
SELECT 
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
LIMIT 5;
```

---

## Example 2: Monthly Net Revenue Trend
```sql
WITH monthly_sales AS (
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
ORDER BY month ASC;
```

---

## Example 3: Revenue by Category
```sql
SELECT 
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
ORDER BY category_revenue DESC;
```

---

## Example 4: Conversion Rate by Traffic Source
```sql
SELECT 
    traffic_source,
    COUNT(*) AS total_sessions,
    SUM(CASE WHEN converted = true THEN 1 ELSE 0 END) AS conversions,
    ROUND((SUM(CASE WHEN converted = true THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100), 2) AS conversion_rate_pct
FROM website_sessions
GROUP BY traffic_source
ORDER BY conversion_rate_pct DESC;
```

---

## Example 5: Customers with Zero Orders
```sql
SELECT 
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    c.email,
    c.signup_date,
    c.acquisition_channel
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_id IS NULL
ORDER BY c.signup_date ASC
LIMIT 100;
```

---

## Example 6: Products with Low Inventory (Below 20 units)
```sql
SELECT 
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
ORDER BY inv.available_quantity ASC;
```
