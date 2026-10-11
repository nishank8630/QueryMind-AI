"""FastAPI Application Entry Point with full API routes and CORS."""
import logging
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import get_settings
from app.database.connection import check_db_connection, get_db, engine
from app.database.schema_inspector import SchemaInspector
from app.database.models import QueryLog
from app.services.query_pipeline import QueryPipeline
from app.demo.demo_data_service import DemoDataService
from app.ml.schema_router import SchemaRouter
from app.ml.training import train_and_evaluate_router
from app.evaluation.runner import EvaluationRunner
from app.rag.document_loader import KnowledgeDocumentLoader
from app.database.seed import reset_database_safely
from app.api.schemas import (
    QueryRequest, QueryResponse, HealthResponse,
    InsertOrderRequest, ResetDatabaseRequest, TrainModelRequest
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("querymind.api")

settings = get_settings()

app = FastAPI(
    title="QueryMind AI API",
    description="RAG-Powered Database Intelligence & Natural Language Analytics Platform API",
    version=settings.APP_VERSION
)

# CORS Policy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = QueryPipeline()
demo_service = DemoDataService()
schema_inspector = SchemaInspector()

# -------------------------------------------------------------
# 1. Health & Overview
# -------------------------------------------------------------
@app.get("/health", response_model=HealthResponse)
def get_health_status():
    db_status = check_db_connection()
    router = SchemaRouter()
    return {
        "status": "healthy" if db_status.get("status") == "healthy" else "degraded",
        "version": settings.APP_VERSION,
        "mode": settings.APP_MODE,
        "database": db_status,
        "llm_provider": {
            "configured": bool(settings.GROQ_API_KEY),
            "provider": "Groq" if settings.GROQ_API_KEY else "Deterministic Demo Catalog",
            "model": settings.GROQ_MODEL
        },
        "vector_store": {
            "type": "Qdrant",
            "collection": settings.QDRANT_COLLECTION,
            "embedding_model": settings.EMBEDDING_MODEL
        },
        "schema_router": {
            "loaded": router.model is not None,
            "classes": router.classes
        }
    }

@app.get("/api/overview")
def get_overview_kpis(db: Session = Depends(get_db)):
    """Fetch live e-commerce KPIs and metrics directly from PostgreSQL."""
    try:
        total_customers = db.execute(text("SELECT COUNT(*) FROM customers;")).scalar() or 0
        total_orders = db.execute(text("SELECT COUNT(*) FROM orders;")).scalar() or 0
        total_products = db.execute(text("SELECT COUNT(*) FROM products;")).scalar() or 0
        
        # Net revenue calculation according to business rule
        rev_query = """
        WITH gross_rev AS (
            SELECT 
                o.order_id,
                SUM(oi.quantity * (oi.unit_price - oi.item_discount)) AS net_items
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.order_status = 'Completed'
            GROUP BY o.order_id
        ),
        refunds_agg AS (
            SELECT order_id, SUM(refund_amount) AS total_refunded
            FROM returns WHERE return_status = 'Approved' GROUP BY order_id
        )
        SELECT COALESCE(SUM(g.net_items - COALESCE(r.total_refunded, 0)), 0)
        FROM gross_rev g
        LEFT JOIN refunds_agg r ON g.order_id = r.order_id;
        """
        net_revenue = float(db.execute(text(rev_query)).scalar() or 0.0)

        # Category sales
        cat_query = """
        SELECT c.category_name, ROUND(SUM(oi.quantity * (oi.unit_price - oi.item_discount))::numeric, 2) AS revenue
        FROM categories c
        JOIN products p ON c.category_id = p.category_id
        JOIN order_items oi ON p.product_id = oi.product_id
        JOIN orders o ON oi.order_id = o.order_id
        WHERE o.order_status = 'Completed'
        GROUP BY c.category_name
        ORDER BY revenue DESC
        LIMIT 5;
        """
        cat_res = db.execute(text(cat_query)).fetchall()
        top_categories = [{"category": row[0], "revenue": float(row[1])} for row in cat_res]

        return {
            "total_customers": total_customers,
            "total_orders": total_orders,
            "total_products": total_products,
            "net_revenue": round(net_revenue, 2),
            "top_categories": top_categories
        }
    except Exception as e:
        logger.error(f"Error fetching overview KPIs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------------------
# 2. Natural Language Query Execution
# -------------------------------------------------------------
@app.post("/api/query", response_model=QueryResponse)
def execute_natural_language_query(request: QueryRequest):
    result = pipeline.process_query(request.question, app_mode=request.mode)
    return result

# -------------------------------------------------------------
# 3. Live Database Schema
# -------------------------------------------------------------
@app.get("/api/schema")
def get_live_schema():
    return schema_inspector.get_schema_summary()

@app.post("/api/schema/refresh")
def refresh_schema_index():
    loader = KnowledgeDocumentLoader()
    docs = loader.load_all_documents()
    pipeline.retriever.build_index()
    return {
        "status": "success",
        "documents_indexed": len(docs),
        "message": "Schema metadata refreshed and re-embedded into vector index."
    }

# -------------------------------------------------------------
# 4. Knowledge Base & Documents
# -------------------------------------------------------------
@app.get("/api/knowledge/documents")
def get_knowledge_documents():
    loader = KnowledgeDocumentLoader()
    docs = loader.load_all_documents()
    return {"count": len(docs), "documents": docs}

# -------------------------------------------------------------
# 5. ML Models & Schema Router
# -------------------------------------------------------------
@app.get("/api/models/status")
def get_model_status():
    router = SchemaRouter()
    return {
        "is_trained": router.model is not None,
        "classes": router.classes,
        "metadata": router.metadata
    }

@app.post("/api/models/train")
def train_model_endpoint(req: TrainModelRequest):
    metrics = train_and_evaluate_router(num_samples=req.num_samples, seed=req.seed)
    # Reload in pipeline
    pipeline.schema_router.load_model()
    return {"status": "success", "metrics": metrics}

# -------------------------------------------------------------
# 6. Evaluation Benchmark
# -------------------------------------------------------------
@app.post("/api/evaluation/run")
def run_evaluation_benchmark(limit: int = 25):
    runner = EvaluationRunner()
    report = runner.run_benchmark(limit=limit)
    return report

# -------------------------------------------------------------
# 7. Query History
# -------------------------------------------------------------
@app.get("/api/query-history")
def get_query_history(limit: int = 50, db: Session = Depends(get_db)):
    logs = db.query(QueryLog).order_by(QueryLog.created_at.desc()).limit(limit).all()
    return [
        {
            "query_id": l.query_id,
            "user_question": l.user_question,
            "generated_sql": l.generated_sql,
            "query_status": l.query_status,
            "execution_time_ms": l.execution_time_ms,
            "result_row_count": l.result_row_count,
            "created_at": l.created_at.isoformat(),
            "error_category": l.error_category
        }
        for l in logs
    ]

# -------------------------------------------------------------
# 8. Live Demonstration Controls
# -------------------------------------------------------------
@app.post("/api/demo/insert-order")
def insert_live_demo_order(req: InsertOrderRequest):
    result = demo_service.insert_synthetic_order(customer_id=req.customer_id, product_id=req.product_id)
    return result

@app.post("/api/demo/reset-database")
def reset_database_endpoint(req: ResetDatabaseRequest):
    if req.confirm_dbname != "querymind_db":
        raise HTTPException(status_code=400, detail="Security error: Target database confirmation does not match 'querymind_db'.")
    reset_database_safely(confirm_dbname=req.confirm_dbname)
    return {"status": "success", "message": "Database tables safely reset to clean state."}
