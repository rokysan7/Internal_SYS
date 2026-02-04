"""Checklist CRUD 테스트."""


def test_create_checklist(client, sample_case):
    resp = client.post(
        f"/cases/{sample_case['id']}/checklists",
        json={"content": "고객에게 연락"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["content"] == "고객에게 연락"
    assert data["is_done"] is False


def test_create_checklist_case_not_found(client):
    resp = client.post("/cases/99999/checklists", json={"content": "task"})
    assert resp.status_code == 404


def test_list_checklists(client, sample_case):
    client.post(f"/cases/{sample_case['id']}/checklists", json={"content": "Task 1"})
    client.post(f"/cases/{sample_case['id']}/checklists", json={"content": "Task 2"})
    resp = client.get(f"/cases/{sample_case['id']}/checklists")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_toggle_checklist_done(client, sample_case):
    create_resp = client.post(
        f"/cases/{sample_case['id']}/checklists",
        json={"content": "Toggle test"},
    )
    cl_id = create_resp.json()["id"]

    resp = client.patch(f"/checklists/{cl_id}", json={"is_done": True})
    assert resp.status_code == 200
    assert resp.json()["is_done"] is True


def test_toggle_checklist_undone(client, sample_case):
    create_resp = client.post(
        f"/cases/{sample_case['id']}/checklists",
        json={"content": "Toggle back"},
    )
    cl_id = create_resp.json()["id"]

    client.patch(f"/checklists/{cl_id}", json={"is_done": True})
    resp = client.patch(f"/checklists/{cl_id}", json={"is_done": False})
    assert resp.status_code == 200
    assert resp.json()["is_done"] is False


def test_toggle_checklist_not_found(client):
    resp = client.patch("/checklists/99999", json={"is_done": True})
    assert resp.status_code == 404
