# QueryMind AI System Architecture

```mermaid
flowchart TD
    User([User / Browser]) <--> StreamlitUI[Streamlit UI :8501]
    StreamlitUI <--> FastAPI[FastAPI Backend :8000]
    
    subgraph Query_Pipeline [QueryMind Processing Pipeline]
        FastAPI --> Guardrail[Input Guardrails & Security Check]
        Guardrail --> SchemaRouter[Trainable ML Schema Router]
        Guardrail --> Retriever[Hybrid RAG Retriever]
        
        subgraph Knowledge_Layer [Knowledge & Retrieval]
            SchemaRouter --> TopTables[(Predicted Tables)]
            Retriever --> BM25[(BM25 Lexical Engine)]
            Retriever --> Qdrant[(Qdrant Vector Store)]
            BM25 & Qdrant --> RRF[Reciprocal Rank Fusion]
        end
        
        RRF & TopTables --> PromptBuilder[Bounded Context Prompt Builder]
        PromptBuilder --> Generator[SQL Generator: Groq LLM / Demo Catalog]
        
        Generator --> Validator[SQLGlot AST Security Validator]
        Validator --> ReadOnlyPolicy{Read-Only & Allowlist Valid?}
        
        ReadOnlyPolicy -- No --> RejectionLog[Security / Syntax Rejection]
        ReadOnlyPolicy -- Yes --> Executor[PostgreSQL Execution Engine]
    end
    
    subgraph Storage [PostgreSQL Database :5433]
        Executor --> LivePG[(querymind_db)]
        Executor --> QueryHistory[(query_logs)]
    end
    
    Executor --> ResultProcessor[Result Processor & Grounded Summary]
    ResultProcessor --> FastAPI
```

## Architecture Highlights
1. **Source of Truth**: Numerical data is never hallucinated or calculated by the LLM. PostgreSQL is the source of truth for all quantitative values.
2. **Trainable ML Schema Router**: Lightweight multi-label OneVsRest Logistic Regression classifier with TF-IDF features predicting relevant tables (Achieving >98% Micro F1).
3. **Hybrid Search**: Fuses dense semantic embeddings (`all-MiniLM-L6-v2`) and sparse BM25 keyword matching using Reciprocal Rank Fusion ($RRF$).
4. **Dual Execution Mode**: Supports both live generative SQL via Groq API (`llama-3.3-70b-versatile`) and offline deterministic mode with parameterized SQL templates.
5. **AST Guardrails**: SQLGlot parses every generated SQL statement before execution to guarantee zero write operations and restrict access exclusively to 10 allowed tables.
