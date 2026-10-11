"""Qdrant vector store integration supporting local in-memory/file storage."""
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from app.config import get_settings

logger = logging.getLogger("querymind.vector_store")
settings = get_settings()

class QdrantVectorStore:
    """Vector store manager backed by Qdrant (local file/memory or service)."""

    def __init__(self, collection_name: str = None):
        self.collection_name = collection_name or settings.QDRANT_COLLECTION
        self.client = self._init_client()

    def _init_client(self) -> QdrantClient:
        try:
            if settings.QDRANT_URL.startswith("http"):
                logger.info(f"Connecting to Qdrant service at {settings.QDRANT_URL}...")
                client = QdrantClient(url=settings.QDRANT_URL, timeout=5)
            else:
                logger.info(f"Initializing local Qdrant storage at {settings.QDRANT_PATH}...")
                client = QdrantClient(path=str(settings.QDRANT_PATH))
            return client
        except Exception as e:
            logger.warning(f"Failed to initialize persistent Qdrant ({e}). Using in-memory Qdrant client.")
            return QdrantClient(":memory:")

    def recreate_collection(self, vector_size: int = 384):
        """Creates or resets the Qdrant collection."""
        try:
            collections = [c.name for c in self.client.get_collections().collections]
            if self.collection_name in collections:
                self.client.delete_collection(self.collection_name)
            
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=qmodels.VectorParams(
                    size=vector_size,
                    distance=qmodels.Distance.COSINE
                )
            )
            logger.info(f"Collection '{self.collection_name}' initialized.")
        except Exception as e:
            logger.error(f"Error creating collection: {e}")

    def upsert_documents(self, documents: List[Dict[str, Any]], vectors: List[List[float]]):
        """Indexes knowledge documents and dense vectors."""
        points = []
        for idx, (doc, vec) in enumerate(zip(documents, vectors)):
            points.append(
                qmodels.PointStruct(
                    id=idx + 1,
                    vector=vec,
                    payload={
                        "document_id": doc.get("document_id"),
                        "document_type": doc.get("document_type"),
                        "title": doc.get("title"),
                        "content": doc.get("content"),
                        "metadata": doc.get("metadata", {})
                    }
                )
            )

        if points:
            self.client.upsert(collection_name=self.collection_name, points=points)
            logger.info(f"Successfully indexed {len(points)} points into '{self.collection_name}'.")

    def search(self, query_vector: List[float], top_k: int = 5, doc_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Dense similarity vector search compatible with qdrant-client >= 1.10 & earlier."""
        query_filter = None
        if doc_type:
            query_filter = qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="document_type",
                        match=qmodels.MatchValue(value=doc_type)
                    )
                ]
            )

        try:
            # Check if client has query_points (newer API) or search (older API)
            if hasattr(self.client, "query_points"):
                response = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    limit=top_k,
                    query_filter=query_filter
                )
                results = response.points
            else:
                results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    limit=top_k,
                    query_filter=query_filter
                )

            hits = []
            for hit in results:
                payload = hit.payload or {}
                hits.append({
                    "document_id": payload.get("document_id"),
                    "document_type": payload.get("document_type"),
                    "title": payload.get("title"),
                    "content": payload.get("content"),
                    "metadata": payload.get("metadata"),
                    "score": float(hit.score)
                })
            return hits
        except Exception as e:
            logger.error(f"Search error in vector store: {e}")
            return []
