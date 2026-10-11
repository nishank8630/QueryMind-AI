"""Controlled synthetic business event injector for live database update demonstrations."""
import random
import uuid
from datetime import datetime
from typing import Dict, Any
from app.database.connection import SessionLocal
from app.database.models import Customer, Product, Order, OrderItem, Payment

class DemoDataService:
    """Manages safe live updates to the synthetic PostgreSQL database."""

    def insert_synthetic_order(self, customer_id: int = None, product_id: int = None) -> Dict[str, Any]:
        """
        Safely creates a new completed order with valid customer, product, order_item,
        and payment records to demonstrate live database responsiveness.
        """
        session = SessionLocal()
        try:
            # 1. Pick or verify Customer
            if customer_id:
                cust = session.query(Customer).filter_by(customer_id=customer_id).first()
            else:
                cust = session.query(Customer).first()

            if not cust:
                raise ValueError("No customer found in synthetic database.")

            # 2. Pick or verify Product
            if product_id:
                prod = session.query(Product).filter_by(product_id=product_id).first()
            else:
                prod = session.query(Product).first()

            if not prod:
                raise ValueError("No product found in synthetic database.")

            now = datetime.utcnow()
            shipping_cost = 9.99
            qty = random.randint(1, 3)
            unit_price = float(prod.list_price)
            discount = 0.0
            order_total = (qty * unit_price) + shipping_cost

            # 3. Create Order
            new_order = Order(
                customer_id=cust.customer_id,
                order_date=now,
                order_status="Completed",
                sales_channel="Web Store (Live Demo)",
                shipping_city=cust.city,
                shipping_state=cust.state,
                shipping_cost=shipping_cost,
                discount_amount=discount
            )
            session.add(new_order)
            session.flush()  # Obtain order_id

            # 4. Create Order Item
            order_item = OrderItem(
                order_id=new_order.order_id,
                product_id=prod.product_id,
                quantity=qty,
                unit_price=unit_price,
                item_discount=discount
            )
            session.add(order_item)

            # 5. Create Payment
            payment = Payment(
                order_id=new_order.order_id,
                payment_date=now,
                payment_method="Credit Card",
                amount=order_total,
                payment_status="Success",
                transaction_reference=f"DEMO-TXN-{new_order.order_id}-{uuid.uuid4().hex[:8].upper()}"
            )
            session.add(payment)

            session.commit()

            return {
                "success": True,
                "order_id": new_order.order_id,
                "customer_name": f"{cust.first_name} {cust.last_name}",
                "product_name": prod.product_name,
                "quantity": qty,
                "total_amount": round(order_total, 2),
                "order_date": now.isoformat(),
                "order_status": "Completed"
            }
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
