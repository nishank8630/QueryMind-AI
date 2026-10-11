"""Unit and integration tests for QueryMind AI."""
import pytest
from app.data_generation.generator import generate_synthetic_data
from app.data_generation.validators import validate_dataset_integrity
from app.sql.validator import SQLValidator, SQLValidationError
from app.ml.schema_router import SchemaRouter
from app.services.query_pipeline import QueryPipeline

def test_synthetic_data_generation_and_integrity():
    """Verify that synthetic dataset satisfies referential integrity constraints."""
    data = generate_synthetic_data(
        num_customers=50,
        num_products=10,
        num_categories=5,
        num_suppliers=5,
        num_orders=100,
        num_sessions=100,
        seed=123
    )
    val = validate_dataset_integrity(data)
    assert val["is_valid"] is True
    assert val["error_count"] == 0
    assert len(data["customers"]) == 50
    assert len(data["orders"]) == 100

def test_sql_validator_read_only_enforcement():
    """Verify that data-modifying SQL queries are strictly rejected."""
    validator = SQLValidator()
    
    # Valid SELECT
    res = validator.validate_and_sanitize("SELECT * FROM customers;")
    assert res["is_valid"] is True
    assert "customers" in res["tables_used"]

    # Reject DELETE
    with pytest.raises(SQLValidationError):
        validator.validate_and_sanitize("DELETE FROM orders WHERE order_id = 1;")

    # Reject DROP
    with pytest.raises(SQLValidationError):
        validator.validate_and_sanitize("DROP TABLE products;")

    # Reject Multiple statements
    with pytest.raises(SQLValidationError):
        validator.validate_and_sanitize("SELECT * FROM customers; DROP TABLE orders;")

    # Reject Unauthorized table
    with pytest.raises(SQLValidationError):
        validator.validate_and_sanitize("SELECT * FROM pg_user;")

def test_schema_router_inference():
    """Verify schema router predicts table metadata for analytics queries."""
    router = SchemaRouter()
    res = router.predict("Who are the top customers by spending?")
    assert len(res["tables"]) > 0
    assert "customers" in res["tables"]

def test_query_pipeline_security_attack():
    """Verify query pipeline safely catches malicious injection attempts."""
    pipeline = QueryPipeline()
    res = pipeline.process_query("Drop the customers table completely.")
    assert res["success"] is False
    assert res["status"] == "SECURITY_REJECTED"

def test_query_pipeline_demo_query():
    """Verify that built-in demo questions execute against PostgreSQL."""
    pipeline = QueryPipeline()
    res = pipeline.process_query("Who are the five customers who spent the most?", app_mode="demo")
    assert res["success"] is True
    assert len(res["rows"]) > 0
    assert "customer_name" in res["columns"]
