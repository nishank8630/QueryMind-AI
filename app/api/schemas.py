"""Pydantic schemas and models for FastAPI request and response validation."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=1000, description="Natural language question")
    mode: Optional[str] = Field(default=None, description="Execution mode: 'demo' or 'live'")

class QueryResponse(BaseModel):
    success: bool
    status: str
    user_question: str
    generated_sql: Optional[str] = None
    explanation: Optional[str] = None
    columns: List[str] = []
    rows: List[Dict[str, Any]] = []
    row_count: int = 0
    tables_used: List[str] = []
    execution_time_ms: float = 0.0
    total_time_ms: float = 0.0
    evidence_docs: List[Dict[str, Any]] = []
    error: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    status: str
    version: str
    mode: str
    database: Dict[str, Any]
    llm_provider: Dict[str, Any]
    vector_store: Dict[str, Any]
    schema_router: Dict[str, Any]

class InsertOrderRequest(BaseModel):
    customer_id: Optional[int] = None
    product_id: Optional[int] = None

class ResetDatabaseRequest(BaseModel):
    confirm_dbname: str = Field(..., description="Must exactly match 'querymind_db'")

class TrainModelRequest(BaseModel):
    num_samples: int = Field(default=600, ge=100, le=2000)
    seed: int = Field(default=42)
