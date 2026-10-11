"""Database seeder and safe reset manager."""
import logging
from typing import Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database.connection import engine, Base, SessionLocal
from app.database.models import (
    Category, Supplier, Product, Customer, Order,
    OrderItem, Payment, Return, Inventory, WebsiteSession, QueryLog
)
from app.data_generation.generator import generate_synthetic_data
from app.data_generation.validators import validate_dataset_integrity

logger = logging.getLogger("querymind.seed")

def init_db_tables():
    """Create all database tables if they do not exist."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created successfully.")

def reset_database_safely(confirm_dbname: str = None):
    """
    Safely resets all tables in the approved synthetic database ONLY.
    Guarantees no arbitrary external database can be dropped or cleared.
    """
    target_db = engine.url.database
    approved_dbs = {"querymind_db", "neondb", "postgres"}
    if target_db not in approved_dbs and target_db != confirm_dbname:
        raise ValueError(
            f"Security Violation: Target database '{target_db}' is not in approved list ({approved_dbs})!"
        )

    logger.warning(f"Resetting synthetic database tables for {target_db}...")
    with engine.begin() as conn:
        # Drop application tables in cascade or reverse dependency order
        conn.execute(text("DROP TABLE IF EXISTS query_logs CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS website_sessions CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS returns CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS payments CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS order_items CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS orders CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS inventory CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS products CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS customers CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS suppliers CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS categories CASCADE;"))
    
    # Recreate tables cleanly
    Base.metadata.create_all(bind=engine)
    logger.info("Database reset complete. All schema tables recreated empty.")

def seed_database(
    customers: int = 2000,
    products: int = 100,
    categories: int = 10,
    suppliers: int = 20,
    orders: int = 10000,
    sessions: int = 15000,
    seed: int = 42
) -> Dict[str, Any]:
    """Generate synthetic data and batch insert into PostgreSQL."""
    init_db_tables()
    logger.info("Generating synthetic business dataset...")
    data = generate_synthetic_data(
        num_customers=customers,
        num_products=products,
        num_categories=categories,
        num_suppliers=suppliers,
        num_orders=orders,
        num_sessions=sessions,
        seed=seed
    )

    # Validate dataset before inserting
    val_report = validate_dataset_integrity(data)
    if not val_report["is_valid"]:
        raise ValueError(f"Synthetic dataset validation failed: {val_report['errors']}")

    logger.info(f"Integrity check passed: {val_report['table_counts']}")
    session = SessionLocal()

    try:
        # 1. Categories
        session.bulk_insert_mappings(Category, data["categories"])
        session.commit()

        # 2. Suppliers
        session.bulk_insert_mappings(Supplier, data["suppliers"])
        session.commit()

        # 3. Products
        session.bulk_insert_mappings(Product, data["products"])
        session.commit()

        # 4. Inventory
        session.bulk_insert_mappings(Inventory, data["inventory"])
        session.commit()

        # 5. Customers
        session.bulk_insert_mappings(Customer, data["customers"])
        session.commit()

        # 6. Orders
        session.bulk_insert_mappings(Order, data["orders"])
        session.commit()

        # 7. Order Items (batch in chunks of 5000)
        chunk_size = 5000
        for i in range(0, len(data["order_items"]), chunk_size):
            session.bulk_insert_mappings(OrderItem, data["order_items"][i:i + chunk_size])
            session.commit()

        # 8. Payments
        for i in range(0, len(data["payments"]), chunk_size):
            session.bulk_insert_mappings(Payment, data["payments"][i:i + chunk_size])
            session.commit()

        # 9. Returns
        if data["returns"]:
            session.bulk_insert_mappings(Return, data["returns"])
            session.commit()

        # 10. Sessions
        for i in range(0, len(data["website_sessions"]), chunk_size):
            session.bulk_insert_mappings(WebsiteSession, data["website_sessions"][i:i + chunk_size])
            session.commit()

        logger.info("All synthetic data successfully seeded into PostgreSQL!")
        return {
            "status": "success",
            "table_counts": val_report["table_counts"],
            "seed": seed
        }
    except Exception as e:
        session.rollback()
        logger.error(f"Seeding failed: {e}")
        raise e
    finally:
        session.close()
