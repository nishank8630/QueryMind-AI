# QueryMind AI — RAG-Powered Database Intelligence & Natural Language Analytics Platform

QueryMind AI is an enterprise-grade database intelligence platform that converts natural-language business questions into validated, read-only PostgreSQL queries using Hybrid RAG (Reciprocal Rank Fusion), a trainable Machine Learning Schema Router, and AST-level security validation.

---

## 🌟 Key Features

1. **Deterministic Synthetic E-Commerce Generator**: 
   - 10 interrelated relational tables (`customers`, `products`, `categories`, `suppliers`, `orders`, `order_items`, `payments`, `returns`, `inventory`, `website_sessions`).
   - Realistic distributions (Zipf popularity, repeat purchasing patterns, seasonal date ranges, return rates).
2. **Trainable ML Schema Router**:
   - Multi-label classification with TF-IDF and OneVsRest Logistic Regression predicting relevant database tables (>98% Micro F1).
3. **Hybrid RAG Retrieval Engine**:
   - Combines Dense Vector Search (Sentence-Transformers `all-MiniLM-L6-v2` in Qdrant) and Sparse Lexical BM25 ranking via Reciprocal Rank Fusion ($RRF$).
4. **AST-Level SQL Security & Guardrails**:
   - Powered by SQLGlot: strict read-only enforcement (`SELECT`/`UNION` only), automatic query limit injection (`LIMIT 500`), statement timeouts, and table allowlists.
5. **Live & Deterministic Demo Operating Modes**:
   - Runs out-of-the-box in Deterministic Demo Mode without requiring any paid LLM API key.
   - Plug-and-play Groq API integration (`llama-3.3-70b-versatile`) for arbitrary natural language generation.
6. **Live Data Update Demonstration**:
   - Inject realistic transactional purchase events into the database on the fly and watch answers update immediately without retraining the LLM.
7. **Premium Streamlit Frontend**:
   - High-contrast enterprise dark theme (Midnight Blue `#081426`, Electric Blue `#2563EB`, White `#FFFFFF`) with interactive Plotly visualizations.

---

## 🚀 Quickstart Guide (Windows Local Setup)

### 1. Prerequisites
- Python 3.10+
- PostgreSQL 14+ installed and running (default port `5433` or `5432`)

### 2. Environment Configuration
Inspect or update `.env` in the project root:
```ini
DATABASE_URL=postgresql+psycopg://postgres:12345@localhost:5433/querymind_db
APP_ENV=development
APP_MODE=demo
MAX_QUERY_ROWS=500
QUERY_TIMEOUT_SECONDS=15
RAG_TOP_K=6
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Optional for Live LLM Mode
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

### 3. Generate Synthetic Business Dataset
Populate PostgreSQL with 2,000 customers and 10,000 orders:
```powershell
python scripts/generate_data.py --customers 2000 --orders 10000 --reset
```

### 4. Train the ML Schema Router Classifier
```powershell
python -m app.ml.training
```

### 5. Run Multi-Dimensional Benchmark Evaluation
```powershell
python scripts/run_evaluation.py --limit 25
```

### 6. Run Automated Test Suite
```powershell
python -m pytest tests/test_querymind.py -v
```

---

## 🖥️ Running the Application

### Terminal 1: Start FastAPI Backend
```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive OpenAPI documentation available at: `http://127.0.0.1:8000/docs`

### Terminal 2: Start Streamlit Frontend
```powershell
streamlit run frontend/streamlit_app.py --server.port 8501
```
Open your browser at: `http://localhost:8501`

---

## 📊 Evaluation & Performance Metrics
- **Schema Router Micro F1**: `98.11%` (Baseline orders model: `21.33%`)
- **Security Attack Block Rate**: `100.0%`
- **Execution Success Rate**: `84.62%`
- **Average Pipeline Latency**: `~100 ms`

---

## 🐳 Docker Deployment
```bash
docker-compose up --build
```
This runs PostgreSQL, Qdrant, FastAPI, and Streamlit in persistent Docker containers.
