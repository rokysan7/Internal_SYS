"""통계 API 테스트."""


def test_stat_by_assignee(client, assignee_user, sample_product):
    client.post("/cases/", json={
        "title": "Open Case",
        "content": "C",
        "requester": "Cust",
        "assignee_ids": [assignee_user.id],
    })
    resp = client.get("/cases/statistics/", params={"by": "assignee"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assignee_stat = next(s for s in data if s["assignee_id"] == assignee_user.id)
    assert assignee_stat["open_count"] >= 1


def test_stat_by_assignee_empty(client):
    resp = client.get("/cases/statistics/", params={"by": "assignee"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_stat_by_status(client, sample_product):
    client.post("/cases/", json={
        "title": "S1", "content": "C", "requester": "Cust",
    })
    client.post("/cases/", json={
        "title": "S2", "content": "C", "requester": "Cust",
    })
    resp = client.get("/cases/statistics/", params={"by": "status"})
    assert resp.status_code == 200
    data = resp.json()
    open_stat = next((s for s in data if s["status"] == "OPEN"), None)
    assert open_stat is not None
    assert open_stat["count"] >= 2


def test_stat_by_status_empty(client):
    resp = client.get("/cases/statistics/", params={"by": "status"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_stat_by_time_with_completed(client, sample_product):
    case_resp = client.post("/cases/", json={
        "title": "Done Case",
        "content": "C",
        "requester": "Cust",
    })
    case_id = case_resp.json()["id"]
    client.patch(f"/cases/{case_id}/status", json={"status": "DONE"})

    resp = client.get("/cases/statistics/", params={"by": "time"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_completed"] >= 1
    assert data["avg_hours"] is not None


def test_stat_by_time_no_completed(client):
    resp = client.get("/cases/statistics/", params={"by": "time"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_completed"] == 0
    assert data["avg_hours"] is None


def test_stat_invalid_by(client):
    resp = client.get("/cases/statistics/", params={"by": "invalid"})
    assert resp.status_code == 400
