"""Reciprocal Rank Fusion (RRF) and hybrid search retriever."""
import logging
from typing import List, Dict, Any, Optional
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import QdrantVectorStore
from app.rag.lexical_search import LexicalSearch
from app.rag.document_loader import KnowledgeDocumentLoader

logger = logging.getLogger("querymind.retriever")

class HybridRetriever:
    """Combines Dense Vector and BM25 Lexical search via Reciprocal Rank Fusion."""

    def __init__(self):
        self.doc_loader = KnowledgeDocumentLoader()
        self.embedding_service = EmbeddingService()
        self.vector_store = QdrantVectorStore()
        self.lexical_search = LexicalSearch()
        self._all_docs = []
        self._is_indexed = False

    def build_index(self):
        """Index all knowledge documents into vector store and lexical engine."""
        logger.info("Indexing knowledge base documents...")
        self._all_docs = self.doc_loader.load_all_documents()
        if not self._all_docs:
            logger.warning("No knowledge documents found.")
            return

        # Lexical search fit
        self.lexical_search.fit(self._all_docs)

        # Dense vectors
        texts_to_embed = [f"{d['title']}\n{d['content']}" for d in self._all_docs]
        vectors = self.embedding_service.embed_texts(texts_to_embed)

        dim = len(vectors[0]) if vectors else 384
        self.vector_store.recreate_collection(vector_size=dim)
        self.vector_store.upsert_documents(self._all_docs, vectors)
        self._is_indexed = True
        logger.info(f"Hybrid index successfully built ({len(self._all_docs)} documents).")

    def rrf(self, dense_results: List[Dict[str, Any]], lexical_results: List[Dict[str, Any]], k: int = 60) -> List[Dict[str, Any]]:
        """Reciprocal Rank Fusion algorithm."""
        scores: Dict[str, float] = {}
        doc_map: Dict[str, Dict[str, Any]] = {}

        for rank, item in enumerate(dense_results, 1):
            doc_id = item["document_id"]
            doc_map[doc_id] = item
            scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank))

        for rank, item in enumerate(lexical_results, 1):
            doc_id = item["document_id"]
            if doc_id not in doc_map:
                doc_map[doc_id] = item
            scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank))

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        fused = []
        for doc_id, score in ranked:
            doc_copy = dict(doc_map[doc_id])
            doc_copy["rrf_score"] = score
            fused.append(doc_copy)

        return fused

    def retrieve(
        self,
        query: str,
        top_k: int = 6,
        strategy: str = "hybrid",
        filter_doc_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves context using 'dense', 'lexical', or 'hybrid' (RRF) search.
        """
        if not self._is_indexed:
            self.build_index()

        if strategy == "dense":
            q_vec = self.embedding_service.embed_query(query)
            return self.vector_store.search(q_vec, top_k=top_k, doc_type=filter_doc_type)

        if strategy == "lexical":
            results = self.lexical_search.search(query, top_k=top_k)
            if filter_doc_type:
                results = [r for r in results if r.get("document_type") == filter_doc_type]
            return results[:top_k]

        # Hybrid search
        q_vec = self.embedding_service.embed_query(query)
        dense_hits = self.vector_store.search(q_vec, top_k=top_k * 2, doc_type=filter_doc_type)
        lexical_hits = self.lexical_search.search(query, top_k=top_k * 2)
        if filter_doc_type:
            lexical_hits = [r for r in lexical_hits if r.get("document_type") == filter_doc_type]

        fused = self.rrf(dense_hits, lexical_hits)
        return fused[:top_k]
