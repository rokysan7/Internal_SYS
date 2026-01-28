"""Comment CRUD + Celery 태스크 mock 테스트."""

from unittest.mock import patch


def test_create_comment(client, sample_case):
    with patch("routers.comments.notify_comment.delay"):
        resp = client.post(
            f"/cases/{sample_case['id']}/comments",
            json={"content": "첫 번째 댓글", "is_internal": False},
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["content"] == "첫 번째 댓글"
    assert data["case_id"] == sample_case["id"]
    assert data["is_internal"] is False


def test_create_comment_case_not_found(client, test_user):
    resp = client.post("/cases/99999/comments", json={"content": "댓글"})
    assert resp.status_code == 404


def test_list_comments(client, sample_case):
    with patch("routers.comments.notify_comment.delay"):
        client.post(f"/cases/{sample_case['id']}/comments", json={"content": "Comment 1"})
        client.post(f"/cases/{sample_case['id']}/comments", json={"content": "Comment 2"})

    resp = client.get(f"/cases/{sample_case['id']}/comments")
    assert resp.status_code == 200
    comments = resp.json()
    assert len(comments) == 2
    # ASC 정렬 확인
    assert comments[0]["content"] == "Comment 1"
    assert comments[1]["content"] == "Comment 2"


def test_list_comments_case_not_found(client, test_user):
    resp = client.get("/cases/99999/comments")
    assert resp.status_code == 404


def test_create_comment_triggers_celery(client, sample_case, assignee_user):
    """댓글 작성 시 담당자에게 Celery 태스크가 호출되는지 확인.
    author_id=1(hardcode) != assignee_user.id 이므로 delay 호출됨.
    """
    with patch("routers.comments.notify_comment.delay") as mock_delay:
        resp = client.post(
            f"/cases/{sample_case['id']}/comments",
            json={"content": "알림 테스트 댓글"},
        )
        assert resp.status_code == 201
        mock_delay.assert_called_once_with(
            sample_case["id"], 1, "알림 테스트 댓글"
        )


def test_create_comment_no_celery_when_no_assignee(client, test_user, sample_product):
    """담당자 없는 케이스에 댓글 → Celery 호출 안됨."""
    case_resp = client.post("/cases/", json={
        "title": "No Assignee Case",
        "content": "Content",
        "requester": "Cust",
        "product_id": sample_product["id"],
    })
    case_id = case_resp.json()["id"]

    with patch("routers.comments.notify_comment.delay") as mock_delay:
        client.post(f"/cases/{case_id}/comments", json={"content": "댓글"})
        mock_delay.assert_not_called()
