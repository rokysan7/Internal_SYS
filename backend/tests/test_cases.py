"""CS Case CRUD, 필터, 유사검색, 알림 생성 테스트."""


def test_create_case(client, sample_product, sample_license):
    resp = client.post("/cases/", json={
        "title": "New Case",
        "content": "Case content",
        "product_id": sample_product["id"],
        "license_id": sample_license["id"],
        "requester": "Customer B",
        "priority": "HIGH",
        "tags": ["urgent"],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "New Case"
    assert data["status"] == "OPEN"
    assert data["priority"] == "HIGH"
    assert "urgent" in data["tags"]


def test_create_case_with_assignee_creates_notification(
    client, assignee_user, sample_product
):
    resp = client.post("/cases/", json={
        "title": "Assigned Case",
        "content": "Content",
        "requester": "Cust",
        "assignee_ids": [assignee_user.id],
        "product_id": sample_product["id"],
    })
    assert resp.status_code == 201

    # 담당자에게 ASSIGNEE 알림이 생성되었는지 확인 (celery eager mode)
    notifs = client.get("/notifications/", params={"user_id": assignee_user.id})
    assert notifs.status_code == 200
    items = notifs.json()
    assert any(n["type"] == "ASSIGNEE" for n in items)


def test_create_case_without_assignee_no_notification(client, sample_product):
    client.post("/cases/", json={
        "title": "No Assignee",
        "content": "Content",
        "requester": "Cust",
        "product_id": sample_product["id"],
    })
    notifs = client.get("/notifications/")
    assert len(notifs.json()) == 0


def test_list_cases(client, sample_case):
    resp = client.get("/cases/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


def test_list_cases_filter_status(client, sample_case):
    resp = client.get("/cases/", params={"status": "OPEN"})
    assert resp.status_code == 200
    for c in resp.json()["items"]:
        assert c["status"] == "OPEN"


def test_list_cases_filter_assignee(client, sample_case, assignee_user):
    resp = client.get("/cases/", params={"assignee_id": assignee_user.id})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) >= 1


def test_list_cases_filter_product(client, sample_case, sample_product):
    resp = client.get("/cases/", params={"product_id": sample_product["id"]})
    assert resp.status_code == 200
    for c in resp.json()["items"]:
        assert c["product_id"] == sample_product["id"]


def test_get_case(client, sample_case):
    resp = client.get(f"/cases/{sample_case['id']}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Test Case Title"


def test_get_case_not_found(client):
    resp = client.get("/cases/99999")
    assert resp.status_code == 404


def test_update_case(client, sample_case):
    resp = client.put(f"/cases/{sample_case['id']}", json={
        "title": "Updated Title",
        "content": "Updated content",
    })
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated Title"


def test_update_case_change_assignee_creates_notification(
    client, assignee_user, sample_product
):
    # 담당자 없이 케이스 생성
    case_resp = client.post("/cases/", json={
        "title": "Reassign Test",
        "content": "Content",
        "requester": "Cust",
        "product_id": sample_product["id"],
    })
    case_id = case_resp.json()["id"]

    # 담당자 변경
    client.put(f"/cases/{case_id}", json={"assignee_ids": [assignee_user.id]})

    notifs = client.get("/notifications/", params={"user_id": assignee_user.id})
    assert any(n["type"] == "ASSIGNEE" for n in notifs.json())


def test_update_case_not_found(client):
    resp = client.put("/cases/99999", json={"title": "X"})
    assert resp.status_code == 404


def test_update_case_status_to_done(client, sample_case):
    resp = client.patch(
        f"/cases/{sample_case['id']}/status",
        json={"status": "DONE"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "DONE"
    assert data["completed_at"] is not None


def test_update_case_status_to_in_progress(client, sample_case):
    resp = client.patch(
        f"/cases/{sample_case['id']}/status",
        json={"status": "IN_PROGRESS"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "IN_PROGRESS"
    assert data["completed_at"] is None


def test_similar_cases(client, sample_product):
    client.post("/cases/", json={
        "title": "ChatGPT 결제 오류",
        "content": "결제가 안됩니다",
        "requester": "Cust",
        "tags": ["결제", "오류"],
    })
    resp = client.get("/cases/similar", params={"title": "결제 오류 문의", "tags": ["결제"]})
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 1
    assert any("결제" in r["title"] for r in results)


def test_similar_cases_no_match(client):
    resp = client.get("/cases/similar", params={"title": "zzzznonexistent unique query"})
    assert resp.status_code == 200
    assert len(resp.json()) == 0


# ========== GET /cases/similar Extended Tests ==========


def test_similar_cases_with_tags(client, sample_cases_for_similarity):
    """Tag parameter boosts matching cases."""
    resp = client.get("/cases/similar", params={
        "title": "결제 문의",
        "tags": ["결제"],
    })
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 1
    assert any("결제" in r["title"] for r in results)


def test_similar_cases_with_content(client, sample_cases_for_similarity):
    """Content parameter contributes to similarity score."""
    resp = client.get("/cases/similar", params={
        "title": "결제 오류",
        "content": "신용카드 결제 시 오류가 발생합니다",
        "tags": ["결제"],
    })
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 1


def test_similar_cases_response_format(client, sample_cases_for_similarity):
    """Response includes similarity_score, matched_tags, comment_count, resolved_at."""
    resp = client.get("/cases/similar", params={
        "title": "결제 오류 문의",
        "tags": ["결제"],
    })
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 1
    first = results[0]
    assert "id" in first
    assert "title" in first
    assert "status" in first
    assert "similarity_score" in first
    assert "matched_tags" in first
    assert "comment_count" in first
    assert isinstance(first["similarity_score"], float)
    assert isinstance(first["matched_tags"], list)


def test_similar_cases_score_ordering(client, sample_cases_for_similarity):
    """Results are ordered by similarity_score descending."""
    resp = client.get("/cases/similar", params={
        "title": "결제 오류 문의",
        "tags": ["결제"],
    })
    assert resp.status_code == 200
    results = resp.json()
    if len(results) >= 2:
        scores = [r["similarity_score"] for r in results]
        assert scores == sorted(scores, reverse=True)


# ========== GET /cases/{id}/similar Tests ==========


def test_case_similar_by_id(client, sample_cases_for_similarity):
    """Get similar cases for an existing case."""
    case_id = sample_cases_for_similarity[0]["id"]
    resp = client.get(f"/cases/{case_id}/similar")
    assert resp.status_code == 200
    results = resp.json()
    # The payment case should find at least one similar case
    assert isinstance(results, list)


def test_case_similar_not_found(client):
    """Non-existent case ID returns 404."""
    resp = client.get("/cases/99999/similar")
    assert resp.status_code == 404


def test_case_similar_auth_required(unauth_client):
    """Similar cases endpoint requires authentication."""
    resp = unauth_client.get("/cases/1/similar")
    assert resp.status_code == 401
