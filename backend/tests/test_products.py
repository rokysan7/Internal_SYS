"""Product CRUD + Product Memo 테스트."""


def test_create_product(client, test_user):
    resp = client.post("/products/", json={"name": "ChatGPT", "description": "AI chatbot"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "ChatGPT"
    assert "id" in data


def test_list_products(client, test_user):
    client.post("/products/", json={"name": "Product A"})
    client.post("/products/", json={"name": "Product B"})
    resp = client.get("/products/")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_products_search(client, test_user):
    client.post("/products/", json={"name": "ChatGPT"})
    client.post("/products/", json={"name": "DALL-E"})
    resp = client.get("/products/", params={"search": "chat"})
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["name"] == "ChatGPT"


def test_get_product(client, sample_product):
    resp = client.get(f"/products/{sample_product['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Test Product"


def test_get_product_not_found(client):
    resp = client.get("/products/99999")
    assert resp.status_code == 404


def test_get_product_licenses(client, sample_product, sample_license):
    resp = client.get(f"/products/{sample_product['id']}/licenses")
    assert resp.status_code == 200
    licenses = resp.json()
    assert len(licenses) == 1
    assert licenses[0]["name"] == "Test License"


def test_create_product_memo(client, test_user, sample_product):
    resp = client.post(
        f"/products/{sample_product['id']}/memos",
        json={"content": "제품 메모 내용"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["content"] == "제품 메모 내용"
    assert data["product_id"] == sample_product["id"]


def test_list_product_memos(client, test_user, sample_product):
    client.post(f"/products/{sample_product['id']}/memos", json={"content": "Memo 1"})
    client.post(f"/products/{sample_product['id']}/memos", json={"content": "Memo 2"})
    resp = client.get(f"/products/{sample_product['id']}/memos")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_create_product_memo_not_found(client, test_user):
    resp = client.post("/products/99999/memos", json={"content": "memo"})
    assert resp.status_code == 404
