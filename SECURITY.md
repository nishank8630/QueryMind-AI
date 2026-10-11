# QueryMind AI Security & Safety Architecture

## 1. Security Overview
QueryMind AI is designed under a **Zero-Trust, Read-Only Data Governance** philosophy. Even if an LLM is prompted maliciously or hallucinated into producing harmful SQL commands, the system guarantees multi-layered defense-in-depth enforcement.

---

## 2. Multi-Layer Defense-in-Depth Model

### Layer 1: Prompt & Natural Language Injection Defense
- Natural language questions are checked against regular expression patterns (`drop table`, `delete from`, `insert into`, `update`, `grant`, `pg_shadow`, `pg_catalog`).
- Queries attempting prompt extraction or database destruction are intercepted and rejected immediately at the ingress gateway.

### Layer 2: Abstract Syntax Tree (AST) Validation with SQLGlot
- The generated SQL string is parsed into a PostgreSQL AST using SQLGlot.
- **Strict Read-Only Grammar**: Only `exp.Select` and `exp.Union` root AST expressions are permitted.
- Any AST expression inheriting from `exp.Insert`, `exp.Update`, `exp.Delete`, `exp.Drop`, `exp.Alter`, `exp.Create`, `exp.TruncateTable`, or `exp.Command` immediately triggers a `SQLValidationError`.
- Multiple statements (`semicolon ; chaining`) are strictly prohibited.

### Layer 3: Database Table & Schema Allowlist
- Queries are restricted exclusively to approved business tables:
  `customers`, `products`, `categories`, `suppliers`, `orders`, `order_items`, `payments`, `returns`, `inventory`, `website_sessions`.
- Any attempt to query system catalogs (`pg_catalog`, `information_schema`, `pg_shadow`, `pg_authid`) is blocked before reaching the database.

### Layer 4: Execution Guardrails & Row Limits
- Automatic LIMIT injection: If an unbounded `SELECT` query is parsed, a configurable `LIMIT 500` is enforced into the AST.
- Execution Timeout: PostgreSQL transaction session sets `statement_timeout = 15000` (15 seconds) to prevent denial-of-service / runaway recursive CTE attacks.
- Read-Only Transactions: Every session sets `SET default_transaction_read_only = on`.

### Layer 5: Database Credential Isolation
- Database credentials and passwords are strictly loaded from `.env` and are never exposed in UI responses, query history logs, or LLM prompts.
- Destructive operations (like synthetic database reset) enforce DB name validation (`querymind_db`) to prevent targeting external or production databases.
