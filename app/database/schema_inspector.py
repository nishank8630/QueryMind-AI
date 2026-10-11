"""Live PostgreSQL schema inspection and relation discovery."""
from typing import Dict, List, Any
from sqlalchemy import inspect, text
from app.database.connection import engine

class SchemaInspector:
    """Discovers live database metadata, tables, columns, constraints, and relationships."""

    def __init__(self, db_engine=None):
        self.engine = db_engine or engine

    def get_schema_summary(self) -> Dict[str, Any]:
        """
        Extract full live schema metadata from PostgreSQL.
        Includes tables, columns, data types, primary keys, foreign keys, and row counts.
        """
        inspector = inspect(self.engine)
        tables = inspector.get_table_names()
        # Filter out system and internal tables
        business_tables = [t for t in tables if not t.startswith("pg_") and not t.startswith("sql_")]

        schema_data = {
            "database": self.engine.url.database,
            "table_count": len(business_tables),
            "tables": {}
        }

        with self.engine.connect() as conn:
            for tbl in business_tables:
                # Get row count
                try:
                    count = conn.execute(text(f"SELECT COUNT(*) FROM {tbl};")).scalar()
                except Exception:
                    count = 0

                columns = []
                for col in inspector.get_columns(tbl):
                    columns.append({
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col.get("nullable", True),
                        "default": str(col.get("default", "")) if col.get("default") is not None else None
                    })

                pk = inspector.get_pk_constraint(tbl)
                fks = inspector.get_foreign_keys(tbl)
                indexes = inspector.get_indexes(tbl)

                schema_data["tables"][tbl] = {
                    "row_count": count,
                    "columns": columns,
                    "primary_key": pk.get("constrained_columns", []),
                    "foreign_keys": [
                        {
                            "constrained_columns": fk.get("constrained_columns", []),
                            "referred_table": fk.get("referred_table"),
                            "referred_columns": fk.get("referred_columns", [])
                        }
                        for fk in fks
                    ],
                    "indexes": [idx.get("name") for idx in indexes]
                }

        return schema_data

    def generate_ddl_and_descriptions(self) -> List[Dict[str, Any]]:
        """
        Generates readable markdown documentation chunks for each table,
        ready to be embedded into the RAG vector store.
        """
        schema_summary = self.get_schema_summary()
        documents = []

        for tbl, details in schema_summary["tables"].items():
            col_lines = []
            for c in details["columns"]:
                pk_marker = " [PRIMARY KEY]" if c["name"] in details["primary_key"] else ""
                col_lines.append(f"  - `{c['name']}` ({c['type']}){pk_marker}")

            fk_lines = []
            for fk in details["foreign_keys"]:
                fk_lines.append(
                    f"  - `{', '.join(fk['constrained_columns'])}` -> `{fk['referred_table']}({', '.join(fk['referred_columns'])})`"
                )

            doc_text = f"### Table: `{tbl}`\n"
            doc_text += f"- **Current Row Count**: {details['row_count']:,}\n"
            doc_text += f"- **Columns**:\n" + "\n".join(col_lines) + "\n"
            if fk_lines:
                doc_text += f"- **Foreign Key Relationships**:\n" + "\n".join(fk_lines) + "\n"

            documents.append({
                "document_id": f"schema_{tbl}",
                "document_type": "schema",
                "table_name": tbl,
                "title": f"Database Table Schema: {tbl}",
                "content": doc_text,
                "metadata": {
                    "table_name": tbl,
                    "columns": [c["name"] for c in details["columns"]],
                    "relationships": [fk["referred_table"] for fk in details["foreign_keys"]],
                    "row_count": details["row_count"]
                }
            })

        return documents
