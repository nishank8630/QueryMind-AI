"""Strict SQL parsing, AST inspection, read-only enforcement and security allowlist."""
import logging
import re
from typing import Dict, Any, List, Set, Optional
import sqlglot
from sqlglot import exp

logger = logging.getLogger("querymind.sql_validator")

# Approved Business Tables
ALLOWED_TABLES: Set[str] = {
    "customers", "products", "categories", "suppliers", "orders",
    "order_items", "payments", "returns", "inventory", "website_sessions"
}

# Forbidden AST Expression Types (Data Modification / DDL / Admin)
FORBIDDEN_EXPRESSION_TYPES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Create,
    exp.Alter,
    exp.Command,
    exp.TruncateTable,
    exp.Grant,
    exp.Revoke,
    exp.Transaction,
    exp.Commit,
    exp.Rollback,
    exp.Merge
)

# Forbidden keywords / comments
FORBIDDEN_KEYWORDS = [
    r"\bpg_sleep\b", r"\bpg_catalog\b", r"\binformation_schema\b",
    r"\bcurrent_user\b", r"\bsession_user\b", r"\bpg_user\b",
    r"\bpg_shadow\b", r"\bpg_authid\b", r"\bcopy\b", r"\bexecute\b",
    r"\binto\s+outfile\b", r"\bload_file\b", r"\bgrant\b", r"\brevoke\b"
]

class SQLValidationError(Exception):
    """Raised when SQL fails security or schema validation."""
    pass

class SQLValidator:
    """Multi-stage SQL security validator with AST analysis."""

    def __init__(self, allowed_tables: Optional[Set[str]] = None, max_row_limit: int = 500):
        self.allowed_tables = allowed_tables or ALLOWED_TABLES
        self.max_row_limit = max_row_limit

    def validate_and_sanitize(self, sql_query: str) -> Dict[str, Any]:
        """
        Parses SQL using SQLGlot, validates read-only constraints,
        restricts to approved tables, and injects safe row limits.
        """
        raw_sql = sql_query.strip().rstrip(";")

        # 1. Reject Multiple Statements
        if ";" in raw_sql:
            raise SQLValidationError("Security Violation: Multiple SQL statements are strictly forbidden.")

        # 2. Check Blacklisted System / Admin Keywords
        for pattern in FORBIDDEN_KEYWORDS:
            if re.search(pattern, raw_sql, re.IGNORECASE):
                raise SQLValidationError(f"Security Violation: Query references restricted keyword/catalog '{pattern}'.")

        # 3. Parse AST using SQLGlot (PostgreSQL dialect)
        try:
            parsed = sqlglot.parse_one(raw_sql, read="postgres")
        except Exception as e:
            raise SQLValidationError(f"SQL Syntax Error: Unable to parse query AST ({str(e)}).")

        # 4. Enforce Read-Only AST Expressions
        if not isinstance(parsed, (exp.Select, exp.Union)):
            raise SQLValidationError(f"Security Violation: Only SELECT / UNION read-only queries are permitted. Got: {type(parsed).__name__}")

        # Check for any nested forbidden statements
        for forbidden in FORBIDDEN_EXPRESSION_TYPES:
            if list(parsed.find_all(forbidden)):
                raise SQLValidationError(f"Security Violation: Found forbidden data modification command ({forbidden.__name__}).")

        # 5. Extract and Validate Referenced Tables
        referenced_tables = set()
        for tbl_exp in parsed.find_all(exp.Table):
            t_name = tbl_exp.name.lower()
            if t_name:
                referenced_tables.add(t_name)

        if not referenced_tables:
            raise SQLValidationError("Invalid Query: No database tables referenced.")

        # Ignore CTE aliases
        cte_aliases = {cte.alias_or_name.lower() for cte in parsed.find_all(exp.CTE) if cte.alias_or_name}
        actual_db_tables = referenced_tables - cte_aliases

        unauthorized_tables = actual_db_tables - self.allowed_tables
        if unauthorized_tables:
            raise SQLValidationError(
                f"Security Violation: Access to table(s) {list(unauthorized_tables)} is not permitted. "
                f"Allowed tables: {sorted(list(self.allowed_tables))}"
            )

        # 6. Row Limit Enforcement
        # Ensure a LIMIT clause exists and does not exceed max_row_limit
        limit_clause = parsed.args.get("limit")
        if limit_clause is None:
            parsed = parsed.limit(self.max_row_limit)
        else:
            try:
                curr_limit = int(limit_clause.expression.name)
                if curr_limit > self.max_row_limit:
                    parsed.set("limit", exp.Limit(expression=exp.Literal.number(self.max_row_limit)))
            except Exception:
                parsed.set("limit", exp.Limit(expression=exp.Literal.number(self.max_row_limit)))

        sanitized_sql = parsed.sql(dialect="postgres")

        return {
            "is_valid": True,
            "sanitized_sql": sanitized_sql,
            "tables_used": sorted(list(actual_db_tables)),
            "dialect": "postgres"
        }
