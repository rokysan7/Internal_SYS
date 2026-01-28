"""크로스 도메인 통합 시나리오 테스트."""

from unittest.mock import patch


def test_full_case_lifecycle(client, test_user, assignee_user):
    """Product → License → Case → Comment → Checklist → DONE 전체 흐름."""
    # 1. Product 생성
    prod = client.post("/products/", json={"name": "Lifecycle Product"}).json()

    # 2. License 생성
    lic = client.post("/licenses/", json={
        "name": "Pro Plan",
        "product_id": prod["id"],
    }).json()

    # 3. Case 생성 (with assignee)
    case = client.post("/cases/", json={
        "title": "Lifecycle Case",
        "content": "Full lifecycle test",
        "product_id": prod["id"],
        "license_id": lic["id"],
        "requester": "Customer",
        "assignee_id": assignee_user.id,
        "priority": "HIGH",
        "tags": ["lifecycle"],
    }).json()
    assert case["status"] == "OPEN"

    # 4. Comment 추가
    with patch("routers.comments.notify_comment.delay"):
        comment = client.post(
            f"/cases/{case['id']}/comments",
            json={"content": "Working on it", "is_internal": True},
        ).json()
    assert comment["is_internal"] is True

    # 5. Checklist 추가
    cl = client.post(
        f"/cases/{case['id']}/checklists",
        json={"content": "고객 확인 완료"},
    ).json()
    assert cl["is_done"] is False

    # 6. Checklist 완료
    client.patch(f"/checklists/{cl['id']}", json={"is_done": True})

    # 7. 상태 IN_PROGRESS → DONE
    client.patch(f"/cases/{case['id']}/status", json={"status": "IN_PROGRESS"})
    done_resp = client.patch(
        f"/cases/{case['id']}/status", json={"status": "DONE"}
    )
    assert done_resp.json()["status"] == "DONE"
    assert done_resp.json()["completed_at"] is not None


def test_assignment_notification_flow(client, test_user, assignee_user, sample_product):
    """케이스 배정 → 알림 생성 → 읽음 처리 플로우."""
    client.post("/cases/", json={
        "title": "Notify Flow",
        "content": "C",
        "requester": "Cust",
        "assignee_id": assignee_user.id,
        "product_id": sample_product["id"],
    })

    # 알림 확인
    notifs = client.get(
        "/notifications/", params={"user_id": assignee_user.id}
    ).json()
    assert len(notifs) == 1
    assert notifs[0]["type"] == "ASSIGNEE"
    assert notifs[0]["is_read"] is False

    # 읽음 처리
    client.patch(f"/notifications/{notifs[0]['id']}/read")

    # 미읽음 없음 확인
    unread = client.get(
        "/notifications/",
        params={"user_id": assignee_user.id, "unread_only": True},
    ).json()
    assert len(unread) == 0


def test_comment_notification_trigger(client, sample_case, assignee_user):
    """댓글 작성 → notify_comment.delay() 호출 검증."""
    with patch("routers.comments.notify_comment.delay") as mock_delay:
        client.post(
            f"/cases/{sample_case['id']}/comments",
            json={"content": "Integration comment"},
        )
        mock_delay.assert_called_once()
        args = mock_delay.call_args[0]
        assert args[0] == sample_case["id"]  # case_id
        assert args[1] == 1                  # author_id (hardcoded)


def test_memo_create_read_flow(client, test_user, sample_product, sample_license):
    """Product Memo + License Memo 생성 → 조회 플로우."""
    # Product memo
    client.post(
        f"/products/{sample_product['id']}/memos",
        json={"content": "제품 관련 메모"},
    )
    p_memos = client.get(f"/products/{sample_product['id']}/memos").json()
    assert len(p_memos) == 1
    assert p_memos[0]["content"] == "제품 관련 메모"

    # License memo
    client.post(
        f"/licenses/{sample_license['id']}/memos",
        json={"content": "라이선스 관련 메모"},
    )
    l_memos = client.get(f"/licenses/{sample_license['id']}/memos").json()
    assert len(l_memos) == 1
    assert l_memos[0]["content"] == "라이선스 관련 메모"


def test_statistics_accuracy(client, test_user, assignee_user, sample_product):
    """다양한 상태의 케이스 생성 → 통계 정확성 검증."""
    # OPEN 2건
    for i in range(2):
        client.post("/cases/", json={
            "title": f"Open {i}", "content": "C", "requester": "Cust",
            "assignee_id": assignee_user.id,
        })

    # DONE 1건
    done_resp = client.post("/cases/", json={
        "title": "Done Case", "content": "C", "requester": "Cust",
        "assignee_id": assignee_user.id,
    })
    client.patch(f"/cases/{done_resp.json()['id']}/status", json={"status": "DONE"})

    # by=status
    status_stat = client.get("/cases/statistics/", params={"by": "status"}).json()
    open_stat = next((s for s in status_stat if s["status"] == "OPEN"), None)
    done_stat = next((s for s in status_stat if s["status"] == "DONE"), None)
    assert open_stat["count"] == 2
    assert done_stat["count"] == 1

    # by=assignee
    assignee_stat = client.get("/cases/statistics/", params={"by": "assignee"}).json()
    stat = next(s for s in assignee_stat if s["assignee_id"] == assignee_user.id)
    assert stat["open_count"] == 2
    assert stat["done_count"] == 1

    # by=time
    time_stat = client.get("/cases/statistics/", params={"by": "time"}).json()
    assert time_stat["total_completed"] == 1
    assert time_stat["avg_hours"] is not None


def test_similar_cases_flow(client, test_user):
    """유사 케이스 검색 플로우."""
    client.post("/cases/", json={
        "title": "결제 오류 문의", "content": "카드 결제 실패", "requester": "Cust",
    })
    client.post("/cases/", json={
        "title": "결제 환불 요청", "content": "환불 처리 요청", "requester": "Cust",
    })
    client.post("/cases/", json={
        "title": "로그인 문제", "content": "비밀번호 초기화", "requester": "Cust",
    })

    results = client.get("/cases/similar", params={"query": "결제"}).json()
    assert len(results) == 2


def test_case_filter_combinations(client, test_user, assignee_user, sample_product):
    """필터 조합 테스트."""
    # assignee + product 연결 케이스
    client.post("/cases/", json={
        "title": "Filter Case",
        "content": "C",
        "requester": "Cust",
        "assignee_id": assignee_user.id,
        "product_id": sample_product["id"],
    })
    # 다른 케이스
    client.post("/cases/", json={
        "title": "Other Case", "content": "C", "requester": "Cust",
    })

    # product 필터
    by_prod = client.get(
        "/cases/", params={"product_id": sample_product["id"]}
    ).json()
    assert len(by_prod) == 1

    # assignee 필터
    by_assign = client.get(
        "/cases/", params={"assignee_id": assignee_user.id}
    ).json()
    assert len(by_assign) == 1

    # 전체
    all_cases = client.get("/cases/").json()
    assert len(all_cases) == 2


def test_product_license_cascade(client, test_user):
    """Product → License 연쇄 조회."""
    prod = client.post("/products/", json={"name": "Multi-License Product"}).json()
    for name in ["Free", "Plus", "Pro"]:
        client.post("/licenses/", json={"name": name, "product_id": prod["id"]})

    licenses = client.get(f"/products/{prod['id']}/licenses").json()
    assert len(licenses) == 3
    names = {l["name"] for l in licenses}
    assert names == {"Free", "Plus", "Pro"}


def test_checklist_toggle_flow(client, sample_case):
    """체크리스트 추가 → 토글 → 상태 확인."""
    items = []
    for content in ["Step 1", "Step 2", "Step 3"]:
        resp = client.post(
            f"/cases/{sample_case['id']}/checklists",
            json={"content": content},
        )
        items.append(resp.json())

    # 모두 미완료
    all_cl = client.get(f"/cases/{sample_case['id']}/checklists").json()
    assert all(not cl["is_done"] for cl in all_cl)

    # 첫 두 개 완료
    for item in items[:2]:
        client.patch(f"/checklists/{item['id']}", json={"is_done": True})

    updated = client.get(f"/cases/{sample_case['id']}/checklists").json()
    done_count = sum(1 for cl in updated if cl["is_done"])
    assert done_count == 2
