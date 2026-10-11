"""CLI script to generate synthetic business data and seed PostgreSQL."""
import argparse
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.seed import seed_database, reset_database_safely

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic data and populate PostgreSQL database.")
    parser.add_argument("--customers", type=int, default=2000, help="Number of customers (default: 2000)")
    parser.add_argument("--products", type=int, default=100, help="Number of products (default: 100)")
    parser.add_argument("--categories", type=int, default=10, help="Number of categories (default: 10)")
    parser.add_argument("--suppliers", type=int, default=20, help="Number of suppliers (default: 20)")
    parser.add_argument("--orders", type=int, default=10000, help="Number of orders (default: 10000)")
    parser.add_argument("--sessions", type=int, default=15000, help="Number of website sessions (default: 15000)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--reset", action="store_true", help="Reset existing tables before seeding")

    args = parser.parse_args()

    if args.reset:
        print("Resetting synthetic database...")
        reset_database_safely()

    print(f"Generating & seeding synthetic dataset (Seed={args.seed})...")
    result = seed_database(
        customers=args.customers,
        products=args.products,
        categories=args.categories,
        suppliers=args.suppliers,
        orders=args.orders,
        sessions=args.sessions,
        seed=args.seed
    )
    print("Database seeding completed successfully!")
    print("Record counts:")
    for table, count in result["table_counts"].items():
        print(f"  - {table}: {count:,} rows")

if __name__ == "__main__":
    main()
