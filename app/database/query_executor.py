"""Safe PostgreSQL query executor with timeout, limits, and read-only transactions."""
import logging
import time
from typing import Dict, Any, List
from sqlalchemy import text
from app.database.connection import engine
from app.config import get_settings

logger = logging.getLogger("querymind.executor")
settings = get_settings()

class QueryExecutionError(Exception):
    """Raised when SQL execution encounters a database error or timeout."""
    pass

class QueryExecutor:
    """Executes validated read-only SQL queries against PostgreSQL with guardrails."""

    def __init__(self, db_engine=None):
        self.engine = db_engine or engine
        self.timeout_seconds = settings.QUERY_TIMEOUT_SECONDS

    def execute_query(self, sql_query: str) -> Dict[str, Any]:
        """
        Executes SQL query in a read-only transaction with execution timeout.
        Returns column headers, row records, and execution metrics.
        """
        start_time = time.perf_counter()

        if self.engine is None:
            raise QueryExecutionError("Database connection engine is unavailable.")

        try:
            with self.engine.connect() as conn:
                # Set statement timeout and read-only transaction mode
                conn.execute(text(f"SET statement_timeout = {int(self.timeout_seconds * 1000)};"))
                conn.execute(text("SET default_transaction_read_only = on;"))

                cursor = conn.execute(text(sql_query))
                columns = list(cursor.keys())
                raw_rows = cursor.fetchall()
                
                # Format rows into serializable dictionaries and list of values
                rows = []
                for r in raw_rows:
                    row_dict = {}
                    for col_name, val in zip(columns, r):
                        # Convert decimals / datetimes to serializable types
                        if hasattr(val, "isoformat"):
                            row_dict[col_name] = val.isoformat()
                        elif hasattr(val, "__float__"):
                            row_dict[col_name] = float(val)
                        else:
                            row_dict[col_name] = val
                    rows.append(row_dict)

                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                return {
                    "success": True,
                    "columns": columns,
                    "rows": rows,
                    "row_count": len(rows),
                    "execution_time_ms": duration_ms,
                    "sql": sql_query
                }

        except Exception as e:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            error_msg = str(e)
            logger.error(f"SQL execution failed ({duration_ms}ms): {error_msg}")
            
            # Categorize error
            category = "SYNTAX_OR_EXECUTION_ERROR"
            if "canceling statement due to statement timeout" in error_msg.lower():
                category = "QUERY_TIMEOUT"
            elif "permission denied" in error_msg.lower():
                category = "PERMISSION_DENIED"

            return {
                "success": False,
                "error": error_msg,
                "error_category": category,
                "execution_time_ms": duration_ms,
                "columns": [],
                "rows": [],
                "row_count": 0,
                "sql": sql_query
            }
