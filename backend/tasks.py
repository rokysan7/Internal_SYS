"""
Celery 비동기 태스크.
- check_pending_cases: 24시간 미처리 CS 리마인드 알림
- notify_comment: 댓글 등록 시 담당자 알림
- notify_case_assigned: 케이스 배정 시 담당자 알림
- notify_reply: 답글 등록 시 부모 댓글 작성자 알림
- cleanup_tag_keywords: 매주 저빈도 키워드/미사용 태그 정리
- compute_case_similarity: 케이스 유사도 계산 → Redis 캐시 (배치 최적화)
- rebuild_tfidf_model: 전체 TF-IDF 모델 재학습 (일배치, 배치 최적화)
"""

import logging
from contextlib import contextmanager
from datetime import datetime, timedelta

from celery_app import celery
from database import SessionLocal
from models import CaseStatus, CSCase, Notification, NotificationType
from services.push import send_push_to_user
from services.tag_service import learn_from_case

logger = logging.getLogger(__name__)

PUSH_TITLE = "CS Dashboard"


@contextmanager
def db_session():
    """Celery 태스크용 DB 세션 컨텍스트 매니저."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@celery.task
def check_pending_cases():
    """24시간 이상 미처리 상태인 CS Case의 담당자에게 리마인드 알림을 생성한다."""
    with db_session() as db:
        threshold = datetime.utcnow() - timedelta(hours=24)
        pending_cases = (
            db.query(CSCase)
            .filter(CSCase.status != CaseStatus.DONE, CSCase.created_at <= threshold)
            .all()
        )

        created = 0
        push_targets = []  # (user_id, message, case_id)
        for case in pending_cases:
            if not case.assignees:
                continue

            # 이미 동일 리마인드가 최근 24시간 내에 존재하면 중복 생성 방지
            existing = (
                db.query(Notification)
                .filter(
                    Notification.case_id == case.id,
                    Notification.type == NotificationType.REMINDER,
                    Notification.created_at >= threshold,
                )
                .first()
            )
            if existing:
                continue

            for assignee in case.assignees:
                msg = f"CS Case #{case.id} 미처리 24시간 경과: {case.title[:50]}"
                notif = Notification(
                    user_id=assignee.id,
                    case_id=case.id,
                    message=msg,
                    type=NotificationType.REMINDER,
                )
                db.add(notif)
                push_targets.append((assignee.id, msg, case.id))
                created += 1

        db.commit()

        for uid, msg, cid in push_targets:
            send_push_to_user(db, uid, PUSH_TITLE, msg, cid)
        return {"checked": len(pending_cases), "notifications_created": created}


@celery.task
def notify_comment(case_id: int, comment_author_id: int, comment_content: str):
    """댓글 작성 시 담당자에게 비동기 알림을 생성한다."""
    with db_session() as db:
        case = db.query(CSCase).filter(CSCase.id == case_id).first()
        if not case or not case.assignees:
            return {"notified": False, "reason": "no case or no assignee"}

        notified_ids = []
        msg = f"CS Case #{case.id}에 새로운 댓글: {comment_content[:50]}"
        for assignee in case.assignees:
            if assignee.id == comment_author_id:
                continue
            notif = Notification(
                user_id=assignee.id,
                case_id=case.id,
                message=msg,
                type=NotificationType.COMMENT,
            )
            db.add(notif)
            notified_ids.append(assignee.id)

        db.commit()

        for uid in notified_ids:
            send_push_to_user(db, uid, PUSH_TITLE, msg, case.id)

        if not notified_ids:
            return {"notified": False, "reason": "author is only assignee"}
        return {"notified": True, "notified_user_ids": notified_ids}


@celery.task
def notify_case_assigned(case_id: int, assignee_ids: list):
    """케이스 배정 시 담당자에게 비동기 알림을 생성한다."""
    with db_session() as db:
        case = db.query(CSCase).filter(CSCase.id == case_id).first()
        if not case or not assignee_ids:
            return {"notified": False, "reason": "no case or no assignees"}

        msg = f"CS Case #{case.id} '{case.title[:50]}' 담당으로 배정되었습니다."
        for uid in assignee_ids:
            notif = Notification(
                user_id=uid,
                case_id=case.id,
                message=msg,
                type=NotificationType.ASSIGNEE,
            )
            db.add(notif)

        db.commit()

        for uid in assignee_ids:
            send_push_to_user(db, uid, PUSH_TITLE, msg, case.id)

        return {"notified": True, "notified_user_ids": assignee_ids}


@celery.task
def notify_reply(case_id: int, parent_author_id: int, replier_name: str, replier_id: int):
    """답글 작성 시 부모 댓글 작성자에게 비동기 알림을 생성한다."""
    with db_session() as db:
        if parent_author_id == replier_id:
            return {"notified": False, "reason": "self-reply"}

        msg = f"{replier_name}님이 회원님의 댓글에 답글을 남겼습니다."
        notif = Notification(
            user_id=parent_author_id,
            case_id=case_id,
            message=msg,
            type=NotificationType.COMMENT,
        )
        db.add(notif)
        db.commit()

        send_push_to_user(db, parent_author_id, PUSH_TITLE, msg, case_id)

        return {"notified": True, "notified_user_id": parent_author_id}


@celery.task
def learn_tags_from_case(case_id: int):
    """Learn keyword weights for tags attached to a case (async)."""
    with db_session() as db:
        case = db.query(CSCase).filter(CSCase.id == case_id).first()
        if not case or not case.tags:
            return {"learned": False, "reason": "no case or no tags"}

        keywords_count = learn_from_case(
            tags=case.tags,
            title=case.title,
            content=case.content or "",
            db=db,
        )
        return {
            "learned": True,
            "tags": case.tags,
            "keywords_count": keywords_count,
        }


@celery.task
def cleanup_tag_keywords():
    """Weekly: remove low-frequency keywords and delete unused tags."""
    from sqlalchemy.orm.attributes import flag_modified

    from models import TagMaster

    with db_session() as db:
        all_tags = db.query(TagMaster).all()
        cleaned_tags = 0
        removed_tags = 0
        removed_keywords = 0

        for tag in all_tags:
            # Remove keywords with frequency <= 1
            if tag.keyword_weights:
                weights = dict(tag.keyword_weights)
                to_remove = [k for k, v in weights.items() if v <= 1]
                if to_remove:
                    for k in to_remove:
                        del weights[k]
                    removed_keywords += len(to_remove)
                    tag.keyword_weights = weights
                    flag_modified(tag, "keyword_weights")
                    cleaned_tags += 1

            # Delete unused tags (except seed tags)
            if tag.usage_count == 0 and tag.created_by != "seed":
                db.delete(tag)
                removed_tags += 1

        db.commit()
        logger.info(
            "Tag cleanup: cleaned=%d, removed=%d, keywords_removed=%d",
            cleaned_tags, removed_tags, removed_keywords,
        )
        return {
            "cleaned_tags": cleaned_tags,
            "removed_tags": removed_tags,
            "removed_keywords": removed_keywords,
        }


@celery.task
def compute_case_similarity(case_id: int):
    """Compute similar cases for a given case and cache results in Redis."""
    import numpy as np

    from services.cache import cache_similar_cases
    from services.similarity import (
        SIMILARITY_THRESHOLD,
        CaseSimilarityEngine,
        compute_tag_similarity,
        load_model_from_redis,
        save_model_to_redis,
    )

    with db_session() as db:
        target = db.query(CSCase).filter(CSCase.id == case_id).first()
        if not target:
            return {"case_id": case_id, "similar_count": 0, "reason": "case not found"}

        all_cases = db.query(CSCase).filter(CSCase.id != case_id).all()
        if not all_cases:
            return {"case_id": case_id, "similar_count": 0}

        # Load or build TF-IDF model
        engine = load_model_from_redis()
        if engine is None or not engine._fitted:
            corpus_cases = [target] + all_cases
            engine = CaseSimilarityEngine()
            engine.fit(
                [c.title for c in corpus_cases],
                [c.content or "" for c in corpus_cases],
            )
            save_model_to_redis(engine)

        # Batch transform (sparse matrix)
        target_title_vec = engine.get_title_vector(target.title)
        target_content_vec = engine.get_content_vector(target.content or "")
        all_title_vecs = engine.batch_title_vectors([c.title for c in all_cases])
        all_content_vecs = engine.batch_content_vectors([c.content or "" for c in all_cases])

        # Batch cosine similarity (sparse)
        title_sims = engine.batch_similarities(target_title_vec, all_title_vecs)
        content_sims = engine.batch_similarities(target_content_vec, all_content_vecs)

        target_tags = target.tags or []
        combined_scores = np.zeros(len(all_cases))
        for i, case in enumerate(all_cases):
            tag_sim = compute_tag_similarity(target_tags, case.tags or [])
            combined_scores[i] = tag_sim * 0.5 + title_sims[i] * 0.3 + content_sims[i] * 0.2

        # Top N via argsort
        top_indices = np.argsort(combined_scores)[::-1][:20]
        top = [
            {"case_id": all_cases[i].id, "score": round(float(combined_scores[i]), 4)}
            for i in top_indices
            if combined_scores[i] >= SIMILARITY_THRESHOLD
        ]

        cache_similar_cases(case_id, top)
        return {"case_id": case_id, "similar_count": len(top)}


@celery.task
def rebuild_tfidf_model():
    """Rebuild TF-IDF model from all cases and recompute similarity caches."""
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity as sk_cosine

    from services.cache import cache_similar_cases
    from services.similarity import (
        SIMILARITY_THRESHOLD,
        CaseSimilarityEngine,
        compute_tag_similarity,
        save_model_to_redis,
    )

    with db_session() as db:
        all_cases = db.query(CSCase).all()
        n = len(all_cases)
        if n < 2:
            return {"cases_count": n, "model_saved": False, "reason": "not enough cases"}

        engine = CaseSimilarityEngine()
        engine.fit(
            [c.title for c in all_cases],
            [c.content or "" for c in all_cases],
        )
        save_model_to_redis(engine)

        # Batch transform all at once (sparse matrices)
        title_vecs = engine.batch_title_vectors([c.title for c in all_cases])
        content_vecs = engine.batch_content_vectors([c.content or "" for c in all_cases])

        # Pairwise cosine similarity (n x n sparse matrices)
        title_sim_matrix = sk_cosine(title_vecs)
        content_sim_matrix = sk_cosine(content_vecs)

        # Recompute similarity cache for every case
        for i, target in enumerate(all_cases):
            target_tags = target.tags or []
            combined_scores = np.zeros(n)
            for j, other in enumerate(all_cases):
                if i == j:
                    continue
                tag_sim = compute_tag_similarity(target_tags, other.tags or [])
                combined_scores[j] = (
                    tag_sim * 0.5 + title_sim_matrix[i, j] * 0.3 + content_sim_matrix[i, j] * 0.2
                )

            # Top 20 via argsort (exclude self at index i)
            combined_scores[i] = -1.0
            top_indices = np.argsort(combined_scores)[::-1][:20]
            scored = [
                {"case_id": all_cases[j].id, "score": round(float(combined_scores[j]), 4)}
                for j in top_indices
                if combined_scores[j] >= SIMILARITY_THRESHOLD
            ]
            cache_similar_cases(target.id, scored)

        logger.info("TF-IDF model rebuilt for %d cases", n)
        return {"cases_count": n, "model_saved": True}
