"""End-to-End Query Processing Pipeline connecting ML, RAG, SQL validation, execution, and evidence grounding."""
import logging
import re
import time
from typing import Dict, Any, List, Optional
from app.config import get_settings
from app.ml.schema_router import SchemaRouter
from app.rag.retriever import HybridRetriever
from app.sql.validator import SQLValidator, SQLValidationError
from app.sql.generator import get_llm_provider
from app.sql.prompts import build_sql_prompt
from app.database.query_executor import QueryExecutor
from app.demo.templates import match_demo_template
from app.database.models import QueryLog
from app.database.connection import SessionLocal

logger = logging.getLogger("querymind.pipeline")
settings = get_settings()

MALICIOUS_INJECTION_PATTERNS = [
    r"\bdrop\s+", r"\bdelete\s+", r"\binsert\s+",
    r"\btruncate\b", r"\bupdate\s+", r"\bgrant\s+",
    r"\brevoke\s+", r"\bpg_shadow\b", r"\bpg_catalog\b", r"\binformation_schema\b",
    r"\balter\s+", r"\bexec(ute)?\b", r"\bshutdown\b"
]

class QueryPipeline:
    """Orchestrates end-to-end question answering pipeline."""

    def __init__(self):
        self.schema_router = SchemaRouter()
        self.retriever = HybridRetriever()
        self.sql_validator = SQLValidator(max_row_limit=settings.MAX_QUERY_ROWS)
        self.query_executor = QueryExecutor()
        self.llm_provider = get_llm_provider()

    def process_query(self, user_question: str, app_mode: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes full pipeline:
        Validation -> Schema Router -> RAG -> Generation (Live or Demo) -> Security Validation -> Execution -> Grounding
        """
        start_time = time.perf_counter()
        clean_question = user_question.strip()
        current_mode = app_mode or settings.APP_MODE

        pipeline_diagnostics = {
            "question": clean_question,
            "mode": current_mode,
            "stages": []
        }

        # 1. Input Safety & Malicious Pattern Check
        for pat in MALICIOUS_INJECTION_PATTERNS:
            if re.search(pat, clean_question, re.IGNORECASE):
                diag = {
                    "success": False,
                    "status": "SECURITY_REJECTED",
                    "error": f"Security Violation: Query or intent matches dangerous operation pattern '{pat}'. Action rejected.",
                    "total_time_ms": round((time.perf_counter() - start_time) * 1000, 2),
                    "generated_sql": None,
                    "rows": [],
                    "columns": [],
                    "diagnostics": pipeline_diagnostics
                }
                self._log_query(clean_question, None, "REJECTED", diag["total_time_ms"], 0, "MALICIOUS_INPUT")
                return diag

        # 2. Schema Router (Trainable ML Component)
        router_res = self.schema_router.predict(clean_question)
        pipeline_diagnostics["stages"].append({
            "stage": "Schema Router (ML)",
            "predicted_tables": router_res["tables"],
            "confidence": round(router_res["confidence"], 3),
            "is_fallback": router_res["is_fallback"]
        })

        # 3. Hybrid RAG Retrieval (Dense + BM25 Lexical + RRF)
        retrieved_docs = self.retriever.retrieve(clean_question, top_k=settings.RAG_TOP_K)
        pipeline_diagnostics["stages"].append({
            "stage": "Hybrid RAG Retrieval",
            "document_count": len(retrieved_docs),
            "document_ids": [d.get("document_id") for d in retrieved_docs]
        })

        generated_sql = ""
        explanation = ""
        tables_used = []
        is_ambiguous = False
        clarification_question = None

        # 4. SQL Generation: Live LLM or Deterministic Demo Mode
        use_live_llm = (current_mode == "live") and self.llm_provider.is_available()

        if use_live_llm:
            try:
                prompt = build_sql_prompt(clean_question, retrieved_docs, router_res["tables"])
                llm_output = self.llm_provider.generate_sql(prompt)
                
                generated_sql = llm_output.get("sql", "")
                explanation = llm_output.get("explanation", "")
                tables_used = llm_output.get("tables_used", [])
                is_ambiguous = llm_output.get("is_ambiguous", False)
                clarification_question = llm_output.get("clarification_question")
                pipeline_diagnostics["stages"].append({"stage": "Groq LLM Generation", "status": "Success"})
            except Exception as e:
                logger.warning(f"Live LLM generation failed ({e}). Falling back to Demo template.")
                use_live_llm = False

        if not use_live_llm:
            # Deterministic Demo Mode
            demo_match = match_demo_template(clean_question)
            if demo_match:
                generated_sql = demo_match["sql"]
                explanation = demo_match["explanation"]
                tables_used = demo_match["tables"]
                pipeline_diagnostics["stages"].append({"stage": "Demo Catalog Match", "status": "Matched"})
            else:
                # Unsupported demo question
                total_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
                return {
                    "success": False,
                    "status": "UNSUPPORTED_DEMO_QUERY",
                    "error": (
                        "QueryMind AI is running in Demo Mode without a live Groq API key. "
                        "This specific question is not in the built-in demo catalog. "
                        "Please select one of the suggested sample questions or provide a GROQ_API_KEY."
                    ),
                    "total_time_ms": total_time_ms,
                    "generated_sql": None,
                    "rows": [],
                    "columns": [],
                    "evidence_docs": retrieved_docs,
                    "diagnostics": pipeline_diagnostics
                }

        # Check for ambiguity
        if is_ambiguous:
            total_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return {
                "success": False,
                "status": "AMBIGUOUS_QUESTION",
                "clarification": clarification_question or "The question is ambiguous. Please specify the business metric or time horizon.",
                "total_time_ms": total_time_ms,
                "generated_sql": None,
                "rows": [],
                "columns": [],
                "evidence_docs": retrieved_docs,
                "diagnostics": pipeline_diagnostics
            }

        # 5. SQL Security & Syntax Validation (SQLGlot AST)
        try:
            val_res = self.sql_validator.validate_and_sanitize(generated_sql)
            sanitized_sql = val_res["sanitized_sql"]
            tables_used = val_res["tables_used"]
            pipeline_diagnostics["stages"].append({
                "stage": "SQL Security Validation",
                "status": "PASSED",
                "tables": tables_used
            })
        except SQLValidationError as ve:
            total_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            self._log_query(clean_question, generated_sql, "VALIDATION_ERROR", total_time_ms, 0, str(ve))
            return {
                "success": False,
                "status": "VALIDATION_REJECTED",
                "error": str(ve),
                "generated_sql": generated_sql,
                "total_time_ms": total_time_ms,
                "rows": [],
                "columns": [],
                "diagnostics": pipeline_diagnostics
            }

        # 6. Database Execution (PostgreSQL with read-only transaction & timeout)
        exec_res = self.query_executor.execute_query(sanitized_sql)
        pipeline_diagnostics["stages"].append({
            "stage": "PostgreSQL Execution",
            "success": exec_res["success"],
            "execution_time_ms": exec_res["execution_time_ms"],
            "row_count": exec_res["row_count"]
        })

        total_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # 7. Grounded Plain-English Summary Generation
        grounded_explanation = explanation
        if exec_res["success"]:
            row_count = exec_res["row_count"]
            if row_count == 0:
                grounded_explanation += " The query executed successfully but found 0 matching database records."
            elif row_count == 1:
                first_row = exec_res["rows"][0]
                summary_vals = ", ".join(f"{k}: {v}" for k, v in list(first_row.items())[:3])
                grounded_explanation += f" Verified database result: {summary_vals}."
            else:
                grounded_explanation += f" Returned {row_count} records from PostgreSQL."

        # 8. Log Query History to PostgreSQL
        self._log_query(
            clean_question,
            sanitized_sql,
            "SUCCESS" if exec_res["success"] else "EXECUTION_ERROR",
            total_time_ms,
            exec_res["row_count"],
            exec_res.get("error_category")
        )

        return {
            "success": exec_res["success"],
            "status": "SUCCESS" if exec_res["success"] else "EXECUTION_ERROR",
            "user_question": clean_question,
            "generated_sql": sanitized_sql,
            "explanation": grounded_explanation,
            "columns": exec_res["columns"],
            "rows": exec_res["rows"],
            "row_count": exec_res["row_count"],
            "tables_used": tables_used,
            "execution_time_ms": exec_res["execution_time_ms"],
            "total_time_ms": total_time_ms,
            "evidence_docs": retrieved_docs,
            "error": exec_res.get("error"),
            "diagnostics": pipeline_diagnostics
        }

    def _log_query(
        self,
        question: str,
        sql: Optional[str],
        status: str,
        duration_ms: float,
        row_count: int,
        error_cat: Optional[str]
    ):
        """Asynchronously or safely writes query logs to the DB."""
        try:
            session = SessionLocal()
            log_entry = QueryLog(
                user_question=question,
                generated_sql=sql,
                query_status=status,
                execution_time_ms=duration_ms,
                result_row_count=row_count,
                error_category=error_cat,
                retrieval_strategy="hybrid_rrf",
                selected_model="groq" if self.llm_provider.is_available() else "deterministic_demo"
            )
            session.add(log_entry)
            session.commit()
            session.close()
        except Exception as e:
            logger.error(f"Failed to log query execution: {e}")
