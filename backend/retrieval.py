"""
Retrieval Layer (RAG)
----------------------
Grounds the LLM's reasoning in a curated dataset of conditions instead of
letting it answer purely from memory. Uses TF-IDF + cosine similarity —
lightweight, deterministic, and requires no external model downloads,
so this runs reliably on any machine immediately after install.
"""

import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "conditions.csv")


class ConditionRetriever:
    def __init__(self, csv_path: str = DATA_PATH):
        self.df = pd.read_csv(csv_path)
        # Combine condition name + symptoms into one searchable text field
        self.corpus = (self.df["condition"] + ". Symptoms: " + self.df["symptoms"]).tolist()
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = self.vectorizer.fit_transform(self.corpus)

    def retrieve(self, query: str, k: int = 4) -> list[dict]:
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.matrix).flatten()
        top_idx = scores.argsort()[::-1][:k]

        results = []
        for idx in top_idx:
            if scores[idx] <= 0:
                continue
            row = self.df.iloc[idx].to_dict()
            row["relevance_score"] = round(float(scores[idx]), 3)
            results.append(row)
        return results


retriever = ConditionRetriever()
