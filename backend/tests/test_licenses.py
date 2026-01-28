"""License CRUD + License Memo 테스트."""


def test_create_license(client, sample_product):
    resp = client.post("/licenses/", json={
        "name": "Pro Plan",
        "product_id": sample_product["id"],
        "description": "프로 플랜",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Pro Plan"
    assert data["product_id"] == sample_product["id"]


def test_create_license_invalid_product(client, test_user):
    resp = client.post("/licenses/", json={
        "name": "Invalid",
        "product_id": 99999,
    })
    assert resp.status_code == 404


def test_get_license(client, sample_license):
    resp = client.get(f"/licenses/{sample_license['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Test License"


def test_get_license_not_found(client):
    resp = client.get("/licenses/99999")
    assert resp.status_code == 404


def test_create_license_memo(client, test_user, sample_license):
    resp = client.post(
        f"/licenses/{sample_license['id']}/memos",
        json={"content": "라이선스 메모"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["content"] == "라이선스 메모"
    assert data["license_id"] == sample_license["id"]


def test_list_license_memos(client, test_user, sample_license):
    client.post(f"/licenses/{sample_license['id']}/memos", json={"content": "Memo A"})
    client.post(f"/licenses/{sample_license['id']}/memos", json={"content": "Memo B"})
    resp = client.get(f"/licenses/{sample_license['id']}/memos")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_create_license_memo_not_found(client, test_user):
    resp = client.post("/licenses/99999/memos", json={"content": "memo"})
    assert resp.status_code == 404
