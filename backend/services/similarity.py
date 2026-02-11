"""
Korean keyword extraction and TF-IDF similarity engine.
Shared by tag_service (Phase 1) and similarity engine (Phase 2).
"""

import logging
import os
import pickle

import numpy as np
from kiwipiepy import Kiwi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.3"))

_kiwi = Kiwi()

# POS tags to keep: NNG=common noun, NNP=proper noun, VV=verb,
# VA=adjective, SL=foreign (English), SH=Chinese character
_KEEP_TAGS = {"NNG", "NNP", "VV", "VA", "SL", "SH"}

# Minimum token length to avoid noise
_MIN_TOKEN_LEN = 2


def extract_keywords(text: str) -> list[str]:
    """Extract meaningful keywords from Korean/mixed text.

    Uses kiwipiepy morphological analysis to extract nouns, verbs,
    adjectives, and foreign words.  Returns deduplicated keywords
    preserving first-occurrence order.
    """
    if not text or not text.strip():
        return []

    tokens = _kiwi.tokenize(text)
    seen: set[str] = set()
    keywords: list[str] = []
    for t in tokens:
        if t.tag not in _KEEP_TAGS:
            continue
        form = t.form.strip()
        if len(form) < _MIN_TOKEN_LEN:
            continue
        lower = form.lower()
        if lower not in seen:
            seen.add(lower)
            keywords.append(form)
    return keywords


# ---------- TF-IDF Similarity Engine ----------


def _tokenize_for_tfidf(text: str) -> str:
    """Extract keywords and join as space-separated string for TfidfVectorizer."""
    return " ".join(extract_keywords(text))


class CaseSimilarityEngine:
    """TF-IDF based similarity engine for CS cases."""

    def __init__(self):
        self.title_vectorizer = TfidfVectorizer(
            tokenizer=str.split, lowercase=False, token_pattern=None
        )
        self.content_vectorizer = TfidfVectorizer(
            tokenizer=str.split, lowercase=False, token_pattern=None
        )
        self._fitted = False

    def fit(self, titles: list[str], contents: list[str]):
        """Fit TF-IDF vectorizers on preprocessed title/content corpus."""
        n = len(titles)
        min_df = 1 if n < 5 else 2

        title_docs = [_tokenize_for_tfidf(t) for t in titles]
        content_docs = [_tokenize_for_tfidf(c) for c in contents]

        self.title_vectorizer = TfidfVectorizer(
            tokenizer=str.split, lowercase=False, token_pattern=None, min_df=min_df
        )
        self.content_vectorizer = TfidfVectorizer(
            tokenizer=str.split, lowercase=False, token_pattern=None, min_df=min_df
        )

        # Guard against empty vocabulary (all docs have no extractable tokens)
        try:
            self.title_vectorizer.fit(title_docs)
        except ValueError:
            self.title_vectorizer = TfidfVectorizer(
                tokenizer=str.split, lowercase=False, token_pattern=None, min_df=1
            )
            # Fit with raw whitespace-split fallback
            fallback_docs = [t if t.strip() else "empty" for t in title_docs]
            self.title_vectorizer.fit(fallback_docs)

        try:
            self.content_vectorizer.fit(content_docs)
        except ValueError:
            self.content_vectorizer = TfidfVectorizer(
                tokenizer=str.split, lowercase=False, token_pattern=None, min_df=1
            )
            fallback_docs = [c if c.strip() else "empty" for c in content_docs]
            self.content_vectorizer.fit(fallback_docs)

        self._fitted = True

    def get_title_vector(self, title: str):
        """Transform a single title to TF-IDF vector."""
        return self.title_vectorizer.transform([_tokenize_for_tfidf(title)])

    def get_content_vector(self, content: str):
        """Transform a single content to TF-IDF vector."""
        return self.content_vectorizer.transform([_tokenize_for_tfidf(content)])

    def batch_title_vectors(self, titles: list[str]):
        """Transform all titles at once (batch). Returns sparse matrix."""
        docs = [_tokenize_for_tfidf(t) for t in titles]
        return self.title_vectorizer.transform(docs)

    def batch_content_vectors(self, contents: list[str]):
        """Transform all contents at once (batch). Returns sparse matrix."""
        docs = [_tokenize_for_tfidf(c) for c in contents]
        return self.content_vectorizer.transform(docs)

    @staticmethod
    def compute_similarity(vec_a, vec_b) -> float:
        """Compute cosine similarity between two sparse vectors."""
        sim = cosine_similarity(vec_a, vec_b)
        return float(sim[0][0])

    @staticmethod
    def batch_similarities(target_vec, all_vecs) -> np.ndarray:
        """Cosine similarity between one vector and a batch (sparse). Returns 1-D array."""
        return cosine_similarity(target_vec, all_vecs).flatten()


def compute_tag_similarity(tags_a: list[str], tags_b: list[str]) -> float:
    """Jaccard similarity between two tag lists."""
    if not tags_a and not tags_b:
        return 0.0
    set_a = set(t.lower() for t in tags_a)
    set_b = set(t.lower() for t in tags_b)
    union = set_a | set_b
    if not union:
        return 0.0
    return len(set_a & set_b) / len(union)


def compute_combined_similarity(
    tag_sim: float, title_sim: float, content_sim: float
) -> float:
    """Weighted combination: tag 50% + title 30% + content 20%."""
    return tag_sim * 0.5 + title_sim * 0.3 + content_sim * 0.2


# ---------- Model Serialization ----------


def serialize_engine(engine: CaseSimilarityEngine) -> bytes:
    """Serialize engine to bytes via pickle."""
    return pickle.dumps(engine)


def deserialize_engine(data: bytes) -> CaseSimilarityEngine:
    """Deserialize engine from bytes via pickle."""
    return pickle.loads(data)  # noqa: S301


REDIS_MODEL_KEY = "tfidf_model"


def save_model_to_redis(engine: CaseSimilarityEngine):
    """Save serialized engine to Redis DB 2."""
    from services.cache import cache_redis

    data = serialize_engine(engine)
    cache_redis.set(REDIS_MODEL_KEY, data)
    logger.info("TF-IDF model saved to Redis (%d bytes)", len(data))


def load_model_from_redis() -> CaseSimilarityEngine | None:
    """Load engine from Redis DB 2. Returns None if not found or deserialization fails."""
    from services.cache import cache_redis

    data = cache_redis.get(REDIS_MODEL_KEY)
    if data is None:
        return None
    try:
        return deserialize_engine(data)
    except Exception:
        logger.warning("Failed to deserialize TF-IDF model from Redis, returning None")
        return None
