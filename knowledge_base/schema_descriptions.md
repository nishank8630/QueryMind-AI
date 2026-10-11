# E-Commerce Database Schema Descriptions & Relationships

## 1. customers
- **Description**: Stores profile, geography, signup timeline, and acquisition attributes for all registered users.
- **Key Columns**: `customer_id` (PK), `first_name`, `last_name`, `email` (Unique), `city`, `state`, `country`, `signup_date`, `customer_segment` (Standard, Premium, Enterprise, Inactive), `acquisition_channel`, `is_active`.
- **Connections**: 1-to-many with `orders` via `customer_id`. 1-to-many with `website_sessions` via `customer_id`.

## 2. products
- **Description**: Contains catalog inventory items, cost structures, and price points.
- **Key Columns**: `product_id` (PK), `product_name`, `category_id` (FK), `supplier_id` (FK), `unit_cost`, `list_price`, `created_at`, `is_active`.
- **Connections**: Many-to-1 with `categories` on `category_id`, many-to-1 with `suppliers` on `supplier_id`. 1-to-many with `order_items` on `product_id`.

## 3. categories
- **Description**: Grouping taxonomy for items (Electronics, Home & Kitchen, Apparel, etc.).
- **Key Columns**: `category_id` (PK), `category_name`, `category_description`.

## 4. suppliers
- **Description**: Vendor records, geographic sourcing hubs, and quality ratings.
- **Key Columns**: `supplier_id` (PK), `supplier_name`, `supplier_region`, `supplier_rating`.

## 5. orders
- **Description**: Header-level purchase transactions.
- **Key Columns**: `order_id` (PK), `customer_id` (FK), `order_date`, `order_status` ('Completed', 'Processing', 'Cancelled'), `sales_channel`, `shipping_city`, `shipping_state`, `shipping_cost`, `discount_amount`.

## 6. order_items
- **Description**: Line-item details inside every order.
- **Key Columns**: `order_item_id` (PK), `order_id` (FK), `product_id` (FK), `quantity`, `unit_price`, `item_discount`.
- **Crucial**: Line revenue equals `quantity * (unit_price - item_discount)`.

## 7. payments
- **Description**: Financial transaction settlement records.
- **Key Columns**: `payment_id` (PK), `order_id` (FK), `payment_date`, `payment_method` ('Credit Card', 'PayPal', 'Apple Pay', 'Bank Transfer'), `amount`, `payment_status` ('Success', 'Failed', 'Refunded', 'Pending'), `transaction_reference`.

## 8. returns
- **Description**: Item return events, refund amounts, and reasons.
- **Key Columns**: `return_id` (PK), `order_id` (FK), `product_id` (FK), `return_date`, `quantity_returned`, `refund_amount`, `return_reason`, `return_status` ('Approved', 'Rejected', 'Pending').

## 9. inventory
- **Description**: Warehouse stock status and availability buffers.
- **Key Columns**: `inventory_id` (PK), `product_id` (FK), `warehouse_location`, `available_quantity`, `reserved_quantity`, `last_updated`.

## 10. website_sessions
- **Description**: Clickstream and web visit activity.
- **Key Columns**: `session_id` (PK), `customer_id` (FK, nullable for anonymous visitors), `session_start`, `session_end`, `device_type`, `traffic_source`, `pages_viewed`, `converted` (Boolean).
