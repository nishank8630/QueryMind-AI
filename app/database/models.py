"""SQLAlchemy ORM models for e-commerce business domain and query history."""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Date, 
    ForeignKey, Text, Numeric, Index
)
from sqlalchemy.orm import relationship
from app.database.connection import Base

# =========================================================================
# DOMAIN TABLES (10 E-COMMERCE TABLES)
# =========================================================================

class Category(Base):
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String(100), nullable=False, unique=True)
    category_description = Column(Text, nullable=True)

    products = relationship("Product", back_populates="category")


class Supplier(Base):
    __tablename__ = "suppliers"

    supplier_id = Column(Integer, primary_key=True, index=True)
    supplier_name = Column(String(150), nullable=False)
    supplier_region = Column(String(100), nullable=False)
    supplier_rating = Column(Float, nullable=False, default=4.0)

    products = relationship("Product", back_populates="supplier")


class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(200), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.supplier_id"), nullable=False, index=True)
    unit_cost = Column(Numeric(10, 2), nullable=False)
    list_price = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    category = relationship("Category", back_populates="products")
    supplier = relationship("Supplier", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")
    returns = relationship("Return", back_populates="product")
    inventory = relationship("Inventory", back_populates="product", uselist=False)


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False, default="United States")
    signup_date = Column(Date, nullable=False, index=True)
    customer_segment = Column(String(50), nullable=False)  # Premium, Standard, Inactive, Enterprise
    acquisition_channel = Column(String(50), nullable=False)  # Organic, Paid Search, Social, Referral
    is_active = Column(Boolean, default=True, nullable=False)

    orders = relationship("Order", back_populates="customer")
    sessions = relationship("WebsiteSession", back_populates="customer")


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False, index=True)
    order_date = Column(DateTime, nullable=False, index=True)
    order_status = Column(String(50), nullable=False, index=True)  # Completed, Cancelled, Returned, Processing
    sales_channel = Column(String(50), nullable=False)  # Web, Mobile App, In-Store, Affiliate
    shipping_city = Column(String(100), nullable=False)
    shipping_state = Column(String(100), nullable=False)
    shipping_cost = Column(Numeric(10, 2), nullable=False, default=0.00)
    discount_amount = Column(Numeric(10, 2), nullable=False, default=0.00)

    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    returns = relationship("Return", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    order_item_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    item_discount = Column(Numeric(10, 2), nullable=False, default=0.00)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False, index=True)
    payment_date = Column(DateTime, nullable=False, index=True)
    payment_method = Column(String(50), nullable=False)  # Credit Card, PayPal, Bank Transfer, Apple Pay
    amount = Column(Numeric(10, 2), nullable=False)
    payment_status = Column(String(50), nullable=False, index=True)  # Success, Failed, Refunded, Pending
    transaction_reference = Column(String(100), nullable=False, unique=True)

    order = relationship("Order", back_populates="payments")


class Return(Base):
    __tablename__ = "returns"

    return_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False, index=True)
    return_date = Column(DateTime, nullable=False, index=True)
    quantity_returned = Column(Integer, nullable=False)
    refund_amount = Column(Numeric(10, 2), nullable=False)
    return_reason = Column(String(100), nullable=False)  # Defective, Wrong Size, Not as Described, Buyer Remorse
    return_status = Column(String(50), nullable=False)  # Approved, Rejected, Pending

    order = relationship("Order", back_populates="returns")
    product = relationship("Product", back_populates="returns")


class Inventory(Base):
    __tablename__ = "inventory"

    inventory_id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False, unique=True, index=True)
    warehouse_location = Column(String(100), nullable=False)
    available_quantity = Column(Integer, nullable=False, default=0)
    reserved_quantity = Column(Integer, nullable=False, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)

    product = relationship("Product", back_populates="inventory")


class WebsiteSession(Base):
    __tablename__ = "website_sessions"

    session_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=True, index=True)
    session_start = Column(DateTime, nullable=False, index=True)
    session_end = Column(DateTime, nullable=False)
    device_type = Column(String(50), nullable=False)  # Desktop, Mobile, Tablet
    traffic_source = Column(String(50), nullable=False)  # Google, Direct, Facebook, Email, Organic
    pages_viewed = Column(Integer, nullable=False, default=1)
    converted = Column(Boolean, nullable=False, default=False)

    customer = relationship("Customer", back_populates="sessions")


# =========================================================================
# APPLICATION METADATA TABLES (Query History & Benchmark Runs)
# =========================================================================

class QueryLog(Base):
    __tablename__ = "query_logs"

    query_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_question = Column(Text, nullable=False)
    generated_sql = Column(Text, nullable=True)
    query_status = Column(String(50), nullable=False)  # SUCCESS, REJECTED, EXECUTION_ERROR, CLARIFICATION
    execution_time_ms = Column(Float, nullable=False, default=0.0)
    result_row_count = Column(Integer, nullable=False, default=0)
    retrieval_document_ids = Column(Text, nullable=True)  # Comma separated
    selected_model = Column(String(100), nullable=True)
    retrieval_strategy = Column(String(100), nullable=True)
    error_category = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
