"""Tag search, suggest, and learning tests."""

from models import TagMaster


# ========== Tag Search API ==========


def test_search_tags(client, sample_tags):
    """Prefix search returns matching tags ordered by usage_count."""
    resp = client.get("/tags/search", params={"q": "결"})
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 1
    assert results[0]["name"] == "결제"
    assert "usage_count" in results[0]


def test_search_tags_empty(client, sample_tags):
    """No matching prefix returns empty list."""
    resp = client.get("/tags/search", params={"q": "zzzznotexist"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_search_tags_auth_required(unauth_client):
    """Tag search requires authentication."""
    resp = unauth_client.get("/tags/search", params={"q": "test"})
    assert resp.status_code == 401


# ========== Tag Suggest API ==========


def test_suggest_tags_with_seed(client, sample_tags):
    """Seed tags with matching keywords are suggested."""
    resp = client.get("/tags/suggest", params={"title": "결제 오류 문의"})
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 1
    names = [r["name"] for r in results]
    assert "결제" in names
    assert "score" in results[0]
    assert "usage_count" in results[0]


def test_suggest_tags_empty_input(client, sample_tags):
    """Empty title returns empty suggestions."""
    resp = client.get("/tags/suggest", params={"title": "   "})
    assert resp.status_code == 200
    assert resp.json() == []


def test_suggest_tags_auth_required(unauth_client):
    """Tag suggest requires authentication."""
    resp = unauth_client.get("/tags/suggest", params={"title": "test"})
    assert resp.status_code == 401


# ========== Tag Learning ==========


def test_learn_from_case(client, db_session):
    """Creating a case with tags triggers keyword learning via Celery eager."""
    resp = client.post("/cases/", json={
        "title": "결제 오류 발생 문의",
        "content": "신용카드 결제가 안됩니다",
        "requester": "Customer",
        "tags": ["결제문제"],
    })
    assert resp.status_code == 201

    tag = db_session.query(TagMaster).filter(TagMaster.name == "결제문제").first()
    assert tag is not None
    assert tag.usage_count >= 1
    assert tag.keyword_weights is not None
    assert len(tag.keyword_weights) > 0


def test_learn_from_case_no_tags(client, db_session):
    """Case without tags does not create any TagMaster records."""
    before_count = db_session.query(TagMaster).count()
    client.post("/cases/", json={
        "title": "Simple question",
        "content": "No tags here",
        "requester": "Customer",
    })
    after_count = db_session.query(TagMaster).count()
    assert after_count == before_count


def test_learn_creates_new_tag(client, db_session):
    """New tag name in case creates a TagMaster entry automatically."""
    resp = client.post("/cases/", json={
        "title": "New feature request",
        "content": "Please add dark mode",
        "requester": "Customer",
        "tags": ["신규기능요청"],
    })
    assert resp.status_code == 201

    tag = db_session.query(TagMaster).filter(TagMaster.name == "신규기능요청").first()
    assert tag is not None
    assert tag.created_by == "user"
    assert tag.usage_count >= 1
