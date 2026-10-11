"""Prompt templates for Text-to-SQL generation and ambiguity detection."""
from typing import List, Dict, Any

SQL_SYSTEM_PROMPT = """You are QueryMind AI, an enterprise Database Intelligence Engine.
Convert natural language business questions into strictly READ-ONLY PostgreSQL queries.

RULES:
1. ONLY generate SELECT or WITH CTE SELECT queries. Never use INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, or DDL.
2. Only reference tables and columns provided in the SCHEMA context. Never invent tables or columns.
3. Obey business definitions (e.g. Net Sales Revenue excludes cancelled orders and subtracts approved refunds).
4. Do NOT multiply totals by blindly joining order_items, payments, and returns; use aggregation subqueries or CTEs when needed.
5. If the question is fundamentally ambiguous (e.g., 'show best customers' with no metric specified), set "is_ambiguous": true and propose a clear clarification question.
6. Return your response strictly as a JSON object with this schema:
{
    "sql": "SELECT ...;",
    "explanation": "Brief description of what this query calculates...",
    "tables_used": ["table1", "table2"],
    "is_ambiguous": false,
    "clarification_question": null,
    "assumptions": ["Assumed Completed order status only"]
}
"""

def build_sql_prompt(
    question: str,
    retrieved_contexts: List[Dict[str, Any]],
    predicted_tables: List[str]
) -> str:
    """Builds comprehensive structured context for the LLM prompt."""
    context_chunks = []
    
    for idx, ctx in enumerate(retrieved_contexts, 1):
        doc_type = ctx.get("document_type", "document")
        title = ctx.get("title", f"Doc {idx}")
        content = ctx.get("content", "")
        context_chunks.append(f"### [Ref #{idx}] ({doc_type}) {title}\n{content}\n")

    combined_context = "\n".join(context_chunks)

    prompt = f"""CONTEXT KNOWLEDGE BASE & SCHEMA:
---------------------------------------------
{combined_context}

MACHINE LEARNING ROUTER HINT:
Likely relevant tables: {', '.join(predicted_tables)}

USER QUESTION:
\"{question}\"

Generate the PostgreSQL query in strict JSON format.
"""
    return prompt
