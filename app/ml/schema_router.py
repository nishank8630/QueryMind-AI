"""Schema routing multi-label machine learning classifier."""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import Pipeline
from app.config import get_settings

logger = logging.getLogger("querymind.schema_router")
settings = get_settings()

ALL_TABLES = [
    "customers", "products", "categories", "suppliers", "orders",
    "order_items", "payments", "returns", "inventory", "website_sessions"
]

class SchemaRouter:
    """Classifies user queries to predict relevant database tables."""

    def __init__(self, model_path: Path = None):
        self.model_path = model_path or (settings.MODELS_DIR / "schema_router.joblib")
        self.metadata_path = self.model_path.with_suffix(".json")
        self.model: Optional[Pipeline] = None
        self.classes: List[str] = ALL_TABLES
        self.metadata: Dict[str, Any] = {}
        self.load_model()

    def load_model(self) -> bool:
        """Loads trained model and metadata if available."""
        if self.model_path.exists():
            try:
                self.model = joblib.load(self.model_path)
                if self.metadata_path.exists():
                    self.metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
                    self.classes = self.metadata.get("classes", ALL_TABLES)
                logger.info(f"Loaded schema router model from {self.model_path}.")
                return True
            except Exception as e:
                logger.error(f"Failed to load schema router: {e}")
        return False

    def predict(self, query: str, threshold: float = 0.3) -> Dict[str, Any]:
        """
        Predicts relevant tables for a user question.
        Returns predicted table list and table probability scores.
        """
        if self.model is None:
            # Fallback heuristic if ML model artifact not found
            matched = [t for t in ALL_TABLES if t in query.lower() or t[:-1] in query.lower()]
            return {
                "tables": matched if matched else ["orders", "order_items", "customers"],
                "confidence": 0.5,
                "scores": {t: 0.5 for t in matched},
                "is_fallback": True
            }

        try:
            # Predict probabilities
            probs = self.model.predict_proba([query])[0]
            scores = {tbl: float(prob) for tbl, prob in zip(self.classes, probs)}
            predicted = [tbl for tbl, prob in scores.items() if prob >= threshold]

            # Ensure at least top 1 table is returned
            if not predicted:
                top_tbl = max(scores.items(), key=lambda x: x[1])[0]
                predicted = [top_tbl]

            max_prob = float(max(probs))
            return {
                "tables": predicted,
                "confidence": max_prob,
                "scores": scores,
                "is_fallback": False
            }
        except Exception as e:
            logger.error(f"Error during schema routing inference: {e}")
            return {
                "tables": ["orders", "order_items", "customers"],
                "confidence": 0.5,
                "scores": {},
                "is_fallback": True
            }
