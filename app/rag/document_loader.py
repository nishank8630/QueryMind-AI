"""Document loader to prepare structured knowledge chunks from schema and business rules."""
import hashlib
import os
import re
from pathlib import Path
from typing import List, Dict, Any
from app.config import get_settings
from app.database.schema_inspector import SchemaInspector

settings = get_settings()

class KnowledgeDocumentLoader:
    """Loads and chunks knowledge base markdown files and live schema metadata."""

    def __init__(self, kb_dir: Path = None):
        self.kb_dir = kb_dir or settings.KNOWLEDGE_BASE_DIR
        self.schema_inspector = SchemaInspector()

    def _hash_content(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    def load_business_rules(self) -> List[Dict[str, Any]]:
        """Parses business rules markdown into distinct metric documents."""
        file_path = self.kb_dir / "business_rules.md"
        if not file_path.exists():
            return []

        content = file_path.read_text(encoding="utf-8")
        sections = re.split(r"\n##\s+", content)
        documents = []

        for idx, sec in enumerate(sections):
            sec = sec.strip()
            if not sec or sec.startswith("# Centralized"):
                continue

            lines = sec.split("\n", 1)
            title = lines[0].strip()
            body = lines[1].strip() if len(lines) > 1 else ""

            # Extract metric tag
            metric_tag = re.sub(r"^\d+\.\s*", "", title).strip().lower().replace(" ", "_")

            documents.append({
                "document_id": f"metric_{metric_tag}",
                "document_type": "business_rule",
                "title": f"Business Metric: {title}",
                "content": f"## {title}\n{body}",
                "metadata": {
                    "source": "business_rules.md",
                    "metric_name": title,
                    "content_hash": self._hash_content(sec)
                }
            })

        return documents

    def load_sql_examples(self) -> List[Dict[str, Any]]:
        """Parses verified SQL examples into query documents."""
        file_path = self.kb_dir / "sql_examples.md"
        if not file_path.exists():
            return []

        content = file_path.read_text(encoding="utf-8")
        sections = re.split(r"\n##\s+", content)
        documents = []

        for idx, sec in enumerate(sections):
            sec = sec.strip()
            if not sec or sec.startswith("# Verified"):
                continue

            lines = sec.split("\n", 1)
            title = lines[0].strip()
            body = lines[1].strip() if len(lines) > 1 else ""

            documents.append({
                "document_id": f"sql_example_{idx}",
                "document_type": "sql_example",
                "title": f"Verified SQL Example: {title}",
                "content": f"## {title}\n{body}",
                "metadata": {
                    "source": "sql_examples.md",
                    "example_title": title,
                    "content_hash": self._hash_content(sec)
                }
            })

        return documents

    def load_schema_documents(self) -> List[Dict[str, Any]]:
        """Extracts schema documentation dynamically from the live database or falls back to static metadata."""
        try:
            return self.schema_inspector.generate_ddl_and_descriptions()
        except Exception as e:
            # Fallback to static schema descriptions markdown if live DB is not connected
            schema_file = self.kb_dir / "schema_descriptions.md"
            if schema_file.exists():
                return [{
                    "document_id": "schema_fallback",
                    "document_type": "schema",
                    "title": "Database Schema Reference (Fallback)",
                    "content": schema_file.read_text(encoding="utf-8"),
                    "metadata": {"source": "schema_descriptions.md"}
                }]
            return []

    def load_all_documents(self) -> List[Dict[str, Any]]:
        """Aggregates all schema, business rule, and SQL example documents."""
        all_docs = []
        all_docs.extend(self.load_schema_documents())
        all_docs.extend(self.load_business_rules())
        all_docs.extend(self.load_sql_examples())
        return all_docs
