"""Model training pipeline for Multi-Label Schema Routing."""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score, precision_score, recall_score
from app.config import get_settings
from app.ml.schema_router import ALL_TABLES
from app.ml.training_data import generate_schema_router_dataset

logger = logging.getLogger("querymind.training")
settings = get_settings()

def train_and_evaluate_router(
    num_samples: int = 600,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Trains a Multi-Label Logistic Regression schema router using TF-IDF features.
    Saves model weights, metadata, and evaluation metrics.
    """
    logger.info("Generating labeled training dataset for schema routing...")
    dataset = generate_schema_router_dataset(num_samples=num_samples, seed=seed)

    questions = [d["question"] for d in dataset]
    labels = [d["tables"] for d in dataset]

    # Binarize multi-label targets
    mlb = MultiLabelBinarizer(classes=ALL_TABLES)
    y_bin = mlb.fit_transform(labels)

    # 70% Train, 15% Validation, 15% Test
    X_train, X_temp, y_train, y_temp = train_test_split(
        questions, y_bin, test_size=0.30, random_state=seed
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=seed
    )

    logger.info(f"Dataset split: {len(X_train)} Train, {len(X_val)} Val, {len(X_test)} Test.")

    # Model Pipeline
    clf = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.95)),
        ("ovr_logreg", OneVsRestClassifier(LogisticRegression(C=2.0, max_iter=200, random_state=seed)))
    ])

    logger.info("Fitting TF-IDF and OneVsRest Logistic Regression...")
    clf.fit(X_train, y_train)

    # Predictions on Test set
    y_pred_test = clf.predict(X_test)

    # Metrics
    micro_f1 = float(f1_score(y_test, y_pred_test, average="micro", zero_division=0))
    macro_f1 = float(f1_score(y_test, y_pred_test, average="macro", zero_division=0))
    micro_precision = float(precision_score(y_test, y_pred_test, average="micro", zero_division=0))
    micro_recall = float(recall_score(y_test, y_pred_test, average="micro", zero_division=0))

    report = classification_report(
        y_test, y_pred_test, target_names=ALL_TABLES, output_dict=True, zero_division=0
    )

    # Naive baseline comparison (random guessing according to class frequencies)
    y_naive = np.zeros_like(y_test)
    y_naive[:, 4] = 1  # Always guess 'orders' table
    naive_f1 = float(f1_score(y_test, y_naive, average="micro", zero_division=0))

    metrics_result = {
        "model_version": "1.0.0",
        "algorithm": "TF-IDF + OneVsRest LogisticRegression",
        "trained_at": datetime.utcnow().isoformat(),
        "train_samples": len(X_train),
        "val_samples": len(X_val),
        "test_samples": len(X_test),
        "classes": ALL_TABLES,
        "test_metrics": {
            "micro_f1": round(micro_f1, 4),
            "macro_f1": round(macro_f1, 4),
            "precision": round(micro_precision, 4),
            "recall": round(micro_recall, 4),
            "baseline_orders_micro_f1": round(naive_f1, 4)
        },
        "per_table_metrics": {
            tbl: {
                "precision": round(report[tbl]["precision"], 3),
                "recall": round(report[tbl]["recall"], 3),
                "f1": round(report[tbl]["f1-score"], 3),
                "support": int(report[tbl]["support"])
            }
            for tbl in ALL_TABLES if tbl in report
        }
    }

    # Save artifacts
    model_file = settings.MODELS_DIR / "schema_router.joblib"
    meta_file = settings.MODELS_DIR / "schema_router.json"
    joblib.dump(clf, model_file)
    meta_file.write_text(json.dumps(metrics_result, indent=2), encoding="utf-8")

    logger.info(f"Model saved to {model_file} with Test Micro F1: {micro_f1:.4f}")
    return metrics_result

if __name__ == "__main__":
    res = train_and_evaluate_router()
    print("Training Results Summary:")
    print(json.dumps(res["test_metrics"], indent=2))
