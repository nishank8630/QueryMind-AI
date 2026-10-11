"""BM25 and lexical keyword search over knowledge documents."""
import math
import re
from typing import List, Dict, Any

class LexicalSearch:
    """In-memory BM25 lexical ranker for keyword retrieval."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents: List[Dict[str, Any]] = []
        self.doc_len: List[int] = []
        self.avg_dl: float = 0.0
        self.doc_freq: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\w+", text.lower())

    def fit(self, documents: List[Dict[str, Any]]):
        """Index documents for BM25 search."""
        self.documents = documents
        total_len = 0
        self.doc_freq = {}
        self.doc_len = []

        for doc in documents:
            tokens = set(self._tokenize(doc["content"] + " " + doc.get("title", "")))
            words = self._tokenize(doc["content"] + " " + doc.get("title", ""))
            self.doc_len.append(len(words))
            total_len += len(words)

            for token in tokens:
                self.doc_freq[token] = self.doc_freq.get(token, 0) + 1

        n_docs = len(documents)
        self.avg_dl = (total_len / n_docs) if n_docs > 0 else 1.0

        # Calculate IDF
        self.idf = {}
        for token, freq in self.doc_freq.items():
            self.idf[token] = math.log((n_docs - freq + 0.5) / (freq + 0.5) + 1.0)

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Score documents against keyword query using BM25."""
        if not self.documents:
            return []

        query_tokens = self._tokenize(query)
        scores = []

        for idx, doc in enumerate(self.documents):
            score = 0.0
            doc_words = self._tokenize(doc["content"] + " " + doc.get("title", ""))
            word_counts = {}
            for w in doc_words:
                word_counts[w] = word_counts.get(w, 0) + 1

            d_len = self.doc_len[idx]
            for token in query_tokens:
                if token in word_counts:
                    tf = word_counts[token]
                    idf = self.idf.get(token, 0.0)
                    denom = tf + self.k1 * (1.0 - self.b + self.b * (d_len / self.avg_dl))
                    score += idf * (tf * (self.k1 + 1.0)) / (denom if denom > 0 else 1.0)

            scores.append((score, doc))

        scores.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, doc in scores[:top_k]:
            if score > 0:
                item = dict(doc)
                item["score"] = float(score)
                results.append(item)

        return results
