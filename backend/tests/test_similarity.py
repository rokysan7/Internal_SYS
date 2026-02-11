"""Similarity engine unit tests: keyword extraction, cosine, jaccard, combined."""

from services.similarity import (
    CaseSimilarityEngine,
    compute_combined_similarity,
    compute_tag_similarity,
    extract_keywords,
)


# ========== Keyword Extraction ==========


def test_extract_keywords_korean():
    """Korean morphological analysis extracts nouns and verbs."""
    keywords = extract_keywords("결제 오류가 발생했습니다")
    assert len(keywords) >= 1
    lower_kw = [k.lower() for k in keywords]
    assert "결제" in lower_kw or "오류" in lower_kw


def test_extract_keywords_english():
    """English/foreign words are extracted via SL tag."""
    keywords = extract_keywords("ChatGPT login error")
    lower_kw = [k.lower() for k in keywords]
    assert any(w in lower_kw for w in ["chatgpt", "login", "error"])


def test_extract_keywords_mixed():
    """Mixed Korean-English text extracts from both."""
    keywords = extract_keywords("ChatGPT 결제 오류 발생")
    assert len(keywords) >= 2


def test_extract_keywords_empty():
    """Empty string returns empty list."""
    assert extract_keywords("") == []
    assert extract_keywords("   ") == []
    assert extract_keywords(None) == []


# ========== Cosine Similarity ==========


def test_cosine_identical():
    """Identical texts should have similarity ~1.0."""
    engine = CaseSimilarityEngine()
    texts = ["결제 오류 발생", "결제 오류 발생", "로그인 문제"]
    engine.fit(texts, texts)

    vec_a = engine.get_title_vector("결제 오류 발생")
    vec_b = engine.get_title_vector("결제 오류 발생")
    sim = engine.compute_similarity(vec_a, vec_b)
    assert sim > 0.99


def test_cosine_different():
    """Completely different texts should have similarity ~0.0."""
    engine = CaseSimilarityEngine()
    titles = ["결제 오류 발생", "로그인 비밀번호 문제", "설치 다운로드 안됨"]
    contents = ["카드 결제가 안됩니다", "비밀번호를 잊어버렸어요", "프로그램 설치가 안됩니다"]
    engine.fit(titles, contents)

    vec_a = engine.get_title_vector("결제 오류 발생")
    vec_b = engine.get_title_vector("설치 다운로드 안됨")
    sim = engine.compute_similarity(vec_a, vec_b)
    assert sim < 0.3


def test_cosine_partial():
    """Partially overlapping texts should have 0 < similarity < 1."""
    engine = CaseSimilarityEngine()
    titles = ["결제 오류 발생", "결제 취소 문의", "로그인 문제"]
    engine.fit(titles, titles)

    vec_a = engine.get_title_vector("결제 오류 발생")
    vec_b = engine.get_title_vector("결제 취소 문의")
    sim = engine.compute_similarity(vec_a, vec_b)
    assert 0.0 < sim < 1.0


# ========== Jaccard (Tag) Similarity ==========


def test_jaccard_identical():
    """Identical tag lists should have similarity 1.0."""
    assert compute_tag_similarity(["결제", "오류"], ["결제", "오류"]) == 1.0


def test_jaccard_no_overlap():
    """No overlapping tags should have similarity 0.0."""
    assert compute_tag_similarity(["결제", "오류"], ["로그인", "인증"]) == 0.0


def test_jaccard_partial():
    """Partial overlap: Jaccard = |intersection| / |union|."""
    sim = compute_tag_similarity(["결제", "오류"], ["결제", "환불"])
    # intersection={"결제"}, union={"결제","오류","환불"} → 1/3
    assert abs(sim - 1 / 3) < 0.01


def test_jaccard_both_empty():
    """Both empty tag lists should return 0.0."""
    assert compute_tag_similarity([], []) == 0.0


# ========== Combined Similarity ==========


def test_combined_similarity():
    """Weighted: tag 50% + title 30% + content 20%."""
    result = compute_combined_similarity(
        tag_sim=1.0, title_sim=0.5, content_sim=0.3,
    )
    expected = 1.0 * 0.5 + 0.5 * 0.3 + 0.3 * 0.2  # = 0.71
    assert abs(result - expected) < 0.001
