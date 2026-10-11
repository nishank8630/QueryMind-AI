import json
import sys
from pathlib import Path

# Add project root to sys.path so 'app' and 'frontend' packages are always discoverable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.config import get_settings
from frontend.styles.theme import CUSTOM_CSS

# Page Configuration
st.set_page_config(
    page_title="QueryMind AI — Database Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Theme
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

settings = get_settings()
API_BASE_URL = f"http://{settings.API_HOST}:{settings.API_PORT}"

# Helper function to query backend with fallback to direct service
def fetch_api(endpoint: str, method: str = "GET", payload: dict = None):
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            resp = requests.get(url, timeout=10)
        else:
            resp = requests.post(url, json=payload, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception:
        return None

# =============================================================================
# SIDEBAR NAVIGATION & SYSTEM HEALTH BADGES
# =============================================================================
with st.sidebar:
    st.markdown("""
    <div class="brand-container">
        <div class="brand-logo-icon">Q</div>
        <div>
            <h1 class="brand-title">QueryMind AI</h1>
            <p class="brand-tagline">Database Intelligence</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        [
            "Overview Dashboard",
            "Ask QueryMind",
            "Data Explorer",
            "RAG Knowledge Base",
            "Model Lab",
            "Evaluation Center",
            "Query History",
            "Live Update Demo",
            "Settings & System Health"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("### **System Status**")
    
    # Live health check
    health_data = fetch_api("/health")
    if health_data and health_data.get("status") == "healthy":
        st.markdown('<span class="badge-status badge-success">● PostgreSQL Connected</span>', unsafe_allow_html=True)
        mode_label = "Groq Live LLM" if health_data["llm_provider"]["configured"] else "Deterministic Demo"
        st.caption(f"Mode: **{mode_label}**")
        st.caption(f"Vector Index: **Qdrant (Local)**")
    else:
        st.markdown('<span class="badge-status badge-warning">● Local Direct Engine</span>', unsafe_allow_html=True)
        st.caption("PostgreSQL Port: **5433**")

# =============================================================================
# 1. OVERVIEW DASHBOARD
# =============================================================================
if page == "Overview Dashboard":
    st.title("Enterprise Overview Dashboard")
    st.markdown("Live operational metrics and revenue KPIs sourced directly from PostgreSQL.")

    overview_data = fetch_api("/api/overview")
    if overview_data:
        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
        
        with kpi_col1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Total Customers</div>
                <div class="kpi-value">{overview_data['total_customers']:,}</div>
                <div class="kpi-subtitle">Across 50 states</div>
            </div>
            """, unsafe_allow_html=True)

        with kpi_col2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Total Orders</div>
                <div class="kpi-value">{overview_data['total_orders']:,}</div>
                <div class="kpi-subtitle">Completed & processed</div>
            </div>
            """, unsafe_allow_html=True)

        with kpi_col3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Net Sales Revenue</div>
                <div class="kpi-value">${overview_data['net_revenue']:,.2f}</div>
                <div class="kpi-subtitle">Excl. cancelled & refunds</div>
            </div>
            """, unsafe_allow_html=True)

        with kpi_col4:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Catalog Products</div>
                <div class="kpi-value">{overview_data['total_products']:,}</div>
                <div class="kpi-subtitle">10 active categories</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        chart_col1, chart_col2 = st.columns([3, 2])

        with chart_col1:
            st.subheader("Top Category Performance")
            cat_df = pd.DataFrame(overview_data.get("top_categories", []))
            if not cat_df.empty:
                fig = px.bar(
                    cat_df,
                    x="category",
                    y="revenue",
                    labels={"category": "Product Category", "revenue": "Net Sales Revenue ($)"},
                    color="revenue",
                    color_continuous_scale="Blues"
                )
                fig.update_layout(
                    template="plotly_dark",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=20, t=30, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)

        with chart_col2:
            st.subheader("Architecture Stack")
            st.markdown("""
            - **PostgreSQL Database**: Port 5433 (`querymind_db`)
            - **Embedding Model**: `all-MiniLM-L6-v2` (CPU Optimized)
            - **Vector Store**: Qdrant Local Engine
            - **Lexical Engine**: BM25 In-Memory Inverted Index
            - **Hybrid Fusion**: Reciprocal Rank Fusion (RRF)
            - **Schema Routing Classifier**: TF-IDF + Logistic Regression
            - **AST Safety Guardrail**: SQLGlot PostgreSQL Parser
            """)
    else:
        st.info("FastAPI backend service is initializing. Please start the backend or refresh.")

# =============================================================================
# 2. ASK QUERYMIND (CORE Q&A)
# =============================================================================
elif page == "Ask QueryMind":
    st.title("Ask QueryMind AI")
    st.markdown("Ask business questions in plain English. Queries are converted to SQL, validated, and executed against PostgreSQL.")

    # Suggested Prompts
    st.markdown("##### **Sample Business Questions**")
    suggestions = [
        "Who are the five customers who spent the most?",
        "What was our monthly net sales revenue?",
        "Which categories generate the most net sales?",
        "What is the average order value?",
        "Which products have low inventory?",
        "Which traffic sources generate the most conversions?",
        "Which customers have never placed an order?",
        "How many payments failed?"
    ]

    selected_suggestion = st.selectbox("Or choose a pre-formulated query template:", ["-- Select a template --"] + suggestions)

    user_query = st.text_area(
        "Enter your business question:",
        value=selected_suggestion if selected_suggestion != "-- Select a template --" else "",
        placeholder="e.g. Which categories generate the highest net revenue?",
        height=100
    )

    col_btn, col_mode = st.columns([1, 4])
    with col_btn:
        run_btn = st.button("Run Analytics 🚀", use_container_width=True)
    with col_mode:
        mode_opt = st.selectbox("Execution Mode", ["Auto (Demo/Live)", "Strict Demo Mode"], label_visibility="collapsed")

    if run_btn and user_query:
        with st.spinner("Processing through Schema Router, Hybrid RAG, SQL Parser & PostgreSQL..."):
            req_payload = {
                "question": user_query,
                "mode": "demo" if "Demo" in mode_opt else None
            }
            res = fetch_api("/api/query", method="POST", payload=req_payload)

            # Fallback direct execution if backend server not yet started
            if res is None:
                from app.services.query_pipeline import QueryPipeline
                p = QueryPipeline()
                res = p.process_query(user_query, app_mode="demo" if "Demo" in mode_opt else None)

            if res:
                # Diagnostics stages pill bar
                if res.get("diagnostics") and res["diagnostics"].get("stages"):
                    stage_pills = "".join(
                        f'<span class="stage-pill">✓ {s.get("stage", "Stage")}</span> '
                        for s in res["diagnostics"]["stages"]
                    )
                    st.markdown(f'<div class="stage-pill-container">{stage_pills}</div>', unsafe_allow_html=True)

                if res.get("success"):
                    st.success(f"Executed in {res.get('execution_time_ms', 0)} ms | Total pipeline: {res.get('total_time_ms', 0)} ms")
                    st.markdown(f"**Grounded Explanation**: {res.get('explanation')}")

                    # Generated SQL
                    with st.expander("Generated & Sanitized PostgreSQL Query", expanded=True):
                        st.code(res.get("generated_sql"), language="sql")
                        st.caption(f"Tables Referenced: {', '.join(res.get('tables_used', []))}")

                    # Results Table
                    rows = res.get("rows", [])
                    if rows:
                        df = pd.DataFrame(rows)
                        st.markdown(f"##### **Query Results ({len(df)} rows)**")
                        st.dataframe(df, use_container_width=True)

                        # Automatic Interactive Chart
                        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
                        str_cols = df.select_dtypes(include=["object"]).columns.tolist()

                        if len(num_cols) >= 1 and len(str_cols) >= 1:
                            st.markdown("##### **Interactive Visualization**")
                            x_col = str_cols[0]
                            y_col = num_cols[0]
                            fig = px.bar(
                                df.head(15),
                                x=x_col,
                                y=y_col,
                                title=f"{y_col.replace('_', ' ').title()} by {x_col.replace('_', ' ').title()}",
                                template="plotly_dark",
                                color=y_col,
                                color_continuous_scale="Blues"
                            )
                            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                            st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Query executed successfully but returned 0 rows.")

                    # Retrieved Evidence
                    with st.expander("Retrieved RAG Evidence & Knowledge Context", expanded=False):
                        for doc in res.get("evidence_docs", []):
                            st.markdown(f"**[{doc.get('document_type', 'doc')}] {doc.get('title')}**")
                            st.markdown(doc.get("content"))
                            st.markdown("---")
                else:
                    st.error(f"Execution Error: {res.get('error') or res.get('status')}")
                    if res.get("generated_sql"):
                        st.code(res.get("generated_sql"), language="sql")

# =============================================================================
# 3. DATA EXPLORER
# =============================================================================
elif page == "Data Explorer":
    st.title("Database Schema & Live Table Explorer")
    st.markdown("Inspect connected PostgreSQL tables, columns, data types, and primary/foreign keys.")

    schema_data = fetch_api("/api/schema")
    if not schema_data:
        from app.database.schema_inspector import SchemaInspector
        schema_data = SchemaInspector().get_schema_summary()

    if schema_data:
        tables = list(schema_data["tables"].keys())
        selected_tbl = st.selectbox("Select a table to inspect:", sorted(tables))

        tbl_meta = schema_data["tables"][selected_tbl]
        col1, col2 = st.columns([1, 2])

        with col1:
            st.metric("Total Records", f"{tbl_meta['row_count']:,}")
            st.markdown(f"**Primary Key**: `{', '.join(tbl_meta['primary_key']) or 'None'}`")
            if tbl_meta["foreign_keys"]:
                st.markdown("**Foreign Keys**:")
                for fk in tbl_meta["foreign_keys"]:
                    st.caption(f"- `{', '.join(fk['constrained_columns'])}` -> `{fk['referred_table']}`")

        with col2:
            st.markdown("##### **Columns & Data Types**")
            cols_df = pd.DataFrame(tbl_meta["columns"])
            st.dataframe(cols_df, use_container_width=True)

# =============================================================================
# 4. RAG KNOWLEDGE BASE
# =============================================================================
elif page == "RAG Knowledge Base":
    st.title("RAG Knowledge Base & Vector Index")
    st.markdown("Manage metadata, business metric definitions, verified SQL queries, and schema documents.")

    col_reindex, col_info = st.columns([1, 4])
    with col_reindex:
        if st.button("Re-Index Knowledge 🔄"):
            fetch_api("/api/schema/refresh", method="POST")
            st.success("Re-indexing complete!")

    kb_data = fetch_api("/api/knowledge/documents")
    if not kb_data:
        from app.rag.document_loader import KnowledgeDocumentLoader
        docs = KnowledgeDocumentLoader().load_all_documents()
        kb_data = {"count": len(docs), "documents": docs}

    if kb_data:
        st.caption(f"Total Indexed Documents: **{kb_data['count']}**")
        for doc in kb_data.get("documents", []):
            with st.expander(f"[{doc.get('document_type')}] {doc.get('title')}"):
                st.markdown(doc.get("content"))
                st.caption(f"ID: {doc.get('document_id')}")

# =============================================================================
# 5. MODEL LAB (SCHEMA ROUTER)
# =============================================================================
elif page == "Model Lab":
    st.title("Model Lab — Schema Router Classifier")
    st.markdown("Trainable Multi-Label Text Classifier predicting relevant database tables from natural-language questions.")

    status_data = fetch_api("/api/models/status")
    if not status_data:
        from app.ml.schema_router import SchemaRouter
        r = SchemaRouter()
        status_data = {"is_trained": r.model is not None, "classes": r.classes, "metadata": r.metadata}

    st.markdown("##### **Model Training & Artifact Status**")
    meta = status_data.get("metadata", {})
    if meta.get("test_metrics"):
        tm = meta["test_metrics"]
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        mcol1.metric("Micro F1 Score", f"{tm['micro_f1'] * 100:.2f}%")
        mcol2.metric("Precision", f"{tm['precision'] * 100:.2f}%")
        mcol3.metric("Recall", f"{tm['recall'] * 100:.2f}%")
        mcol4.metric("Baseline Orders F1", f"{tm['baseline_orders_micro_f1'] * 100:.2f}%")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### **Per-Table Classification Performance**")
        per_tbl = meta.get("per_table_metrics", {})
        if per_tbl:
            pt_df = pd.DataFrame(per_tbl).T.reset_index().rename(columns={"index": "Table Name"})
            st.dataframe(pt_df, use_container_width=True)

    if st.button("Retrain Schema Router Model 🚀"):
        with st.spinner("Generating labeled dataset and fitting OneVsRest Logistic Regression..."):
            from app.ml.training import train_and_evaluate_router
            res = train_and_evaluate_router()
            st.success(f"Model retrained! New Micro F1: {res['test_metrics']['micro_f1'] * 100:.2f}%")
            st.rerun()

# =============================================================================
# 6. EVALUATION CENTER
# =============================================================================
elif page == "Evaluation Center":
    st.title("Evaluation Center & Benchmarks")
    st.markdown("Multi-dimensional evaluation over 100+ benchmark questions measuring schema routing, security rejection, and execution accuracy.")

    if st.button("Run Live Benchmark Suite ⚡"):
        with st.spinner("Executing benchmark evaluation cases..."):
            from app.evaluation.runner import EvaluationRunner
            runner = EvaluationRunner()
            report = runner.run_benchmark(limit=25)
            st.session_state["last_eval_report"] = report

    report = st.session_state.get("last_eval_report")
    if report:
        st.markdown("##### **Latest Benchmark Summary**")
        ecol1, ecol2, ecol3, ecol4 = st.columns(4)
        ecol1.metric("Security Block Rate", f"{report['security_tests']['block_rate_pct']}%", f"{report['security_tests']['blocked']}/{report['security_tests']['total']} attacks")
        ecol2.metric("Schema Router Recall", f"{report['schema_router_accuracy']['recall_at_predicted_pct']}%")
        ecol3.metric("Execution Success", f"{report['sql_execution']['execution_rate_pct']}%")
        ecol4.metric("Avg Latency", f"{report['latency']['avg_latency_ms']} ms")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### **Detailed Benchmark Questions**")
        res_df = pd.DataFrame(report["detailed_results"])
        st.dataframe(res_df, use_container_width=True)

# =============================================================================
# 7. QUERY HISTORY
# =============================================================================
elif page == "Query History":
    st.title("Persisted Query History")
    st.markdown("Audit log of executed questions, generated SQL, durations, and statuses.")

    hist_data = fetch_api("/api/query-history")
    if hist_data:
        h_df = pd.DataFrame(hist_data)
        st.dataframe(h_df, use_container_width=True)
    else:
        st.info("No query logs found yet.")

# =============================================================================
# 8. LIVE UPDATE DEMO
# =============================================================================
elif page == "Live Update Demo":
    st.title("Live Database Update Demonstration")
    st.markdown("Demonstrate real-time query reactivity upon new transactional events **without retraining the LLM**.")

    st.markdown("""
    1. Check how many completed orders exist right now.
    2. Click the button below to inject an authentic synthetic purchase transaction.
    3. Run the question again to see live, instant numerical updates!
    """)

    if st.button("Inject Synthetic Live Order 📦"):
        from app.demo.demo_data_service import DemoDataService
        res = DemoDataService().insert_synthetic_order()
        st.success(f"Order #{res['order_id']} inserted successfully for customer {res['customer_name']} (Total: ${res['total_amount']:.2f})!")

# =============================================================================
# 9. SETTINGS & SYSTEM HEALTH
# =============================================================================
elif page == "Settings & System Health":
    st.title("Settings & System Health")
    st.markdown("Centralized environment configuration, database credentials, and service topology.")

    st.markdown(f"""
    - **Database Connection**: `{settings.DATABASE_URL.split('@')[-1]}`
    - **Query Timeout**: `{settings.QUERY_TIMEOUT_SECONDS} seconds`
    - **Row Limit**: `{settings.MAX_QUERY_ROWS} rows`
    - **Embedding Model**: `{settings.EMBEDDING_MODEL}`
    - **Vector Store**: `Qdrant Local Storage`
    - **LLM Model**: `{settings.GROQ_MODEL}`
    - **Operating Mode**: `{settings.APP_MODE}`
    """)
