"""Product CRUD + Product Memo 테스트."""


def test_create_product(client):
    resp = client.post("/products/", json={"name": "ChatGPT", "description": "AI chatbot"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "ChatGPT"
    assert "id" in data


def test_list_products(client):
    client.post("/products/", json={"name": "Product A"})
    client.post("/products/", json={"name": "Product B"})
    resp = client.get("/products/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_list_products_search(client):
    client.post("/products/", json={"name": "ChatGPT"})
    client.post("/products/", json={"name": "DALL-E"})
    resp = client.get("/products/", params={"search": "chat"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "ChatGPT"


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


def test_create_product_memo(client, sample_product):
    resp = client.post(
        f"/products/{sample_product['id']}/memos",
        json={"content": "제품 메모 내용"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["content"] == "제품 메모 내용"
    assert data["product_id"] == sample_product["id"]


def test_list_product_memos(client, sample_product):
    client.post(f"/products/{sample_product['id']}/memos", json={"content": "Memo 1"})
    client.post(f"/products/{sample_product['id']}/memos", json={"content": "Memo 2"})
    resp = client.get(f"/products/{sample_product['id']}/memos")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_create_product_memo_not_found(client):
    resp = client.post("/products/99999/memos", json={"content": "memo"})
    assert resp.status_code == 404


# ==================== Bulk Upload Tests ====================


def test_bulk_upload_products_success(client):
    """CSV 파일로 product + license 일괄 등록 테스트."""
    csv_content = b"product,license\nChatGPT,Free\nChatGPT,Plus\nDALL-E,Basic\n"
    files = {"file": ("products.csv", csv_content, "text/csv")}
    resp = client.post("/products/bulk", files=files)
    assert resp.status_code == 201
    data = resp.json()
    assert data["products_created"] == 2  # ChatGPT, DALL-E
    assert data["licenses_created"] == 3  # Free, Plus, Basic
    assert data["products_existing"] == 0  # cache hit, not counted as existing
    assert data["licenses_existing"] == 0
    assert data["errors"] == []


def test_bulk_upload_products_dedup(client, sample_product, sample_license):
    """기존 product/license가 있으면 중복 생성하지 않음."""
    csv_content = f"product,license\n{sample_product['name']},{sample_license['name']}\n".encode()
    files = {"file": ("products.csv", csv_content, "text/csv")}
    resp = client.post("/products/bulk", files=files)
    assert resp.status_code == 201
    data = resp.json()
    assert data["products_created"] == 0
    assert data["products_existing"] == 1
    assert data["licenses_created"] == 0
    assert data["licenses_existing"] == 1


def test_bulk_upload_invalid_file_type(client):
    """CSV가 아닌 파일 업로드 시 400 에러."""
    files = {"file": ("products.txt", b"some text", "text/plain")}
    resp = client.post("/products/bulk", files=files)
    assert resp.status_code == 400
    assert "CSV" in resp.json()["detail"]


def test_bulk_upload_missing_columns(client):
    """필수 컬럼 누락 시 400 에러."""
    csv_content = b"name,description\nChatGPT,AI\n"
    files = {"file": ("products.csv", csv_content, "text/csv")}
    resp = client.post("/products/bulk", files=files)
    assert resp.status_code == 400
    assert "product" in resp.json()["detail"] or "license" in resp.json()["detail"]


def test_bulk_upload_empty_values(client):
    """빈 값이 포함된 행은 errors에 기록."""
    csv_content = b"product,license\nChatGPT,Free\n,Plus\nDALL-E,\n"
    files = {"file": ("products.csv", csv_content, "text/csv")}
    resp = client.post("/products/bulk", files=files)
    assert resp.status_code == 201
    data = resp.json()
    assert data["products_created"] == 1  # ChatGPT only
    assert data["licenses_created"] == 1  # Free only
    assert len(data["errors"]) == 2  # Row 3 and Row 4
