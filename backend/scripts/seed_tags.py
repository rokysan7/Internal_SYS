"""
Seed TagMaster with default tags and migrate existing case tags.

Usage:
    cd backend
    .venv/bin/python scripts/seed_tags.py

Safe to re-run: skips existing tags and already-migrated cases.
"""

import sys
import os

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import SessionLocal
from models import CSCase, TagMaster
from services.similarity import extract_keywords
from sqlalchemy.orm.attributes import flag_modified

# ======================== Seed Data ========================

SEED_TAGS = {
    "로그인": {"로그인": 5, "인증": 3, "비밀번호": 3, "접속": 2, "login": 2},
    "라이선스": {"라이선스": 5, "만료": 3, "갱신": 3, "키": 2, "license": 2},
    "설치": {"설치": 5, "업데이트": 3, "설정": 2, "install": 2, "setup": 2},
    "에러": {"에러": 5, "오류": 3, "실패": 3, "error": 2, "crash": 2},
    "네트워크": {"네트워크": 5, "연결": 3, "VPN": 3, "timeout": 2, "방화벽": 2},
}


def seed_default_tags(db):
    """Insert seed tags if they don't already exist."""
    created = 0
    skipped = 0
    for name, weights in SEED_TAGS.items():
        existing = db.query(TagMaster).filter(TagMaster.name.ilike(name)).first()
        if existing:
            skipped += 1
            continue
        tag = TagMaster(
            name=name,
            keyword_weights=weights,
            usage_count=0,
            created_by="seed",
        )
        db.add(tag)
        created += 1
    db.commit()
    print(f"[Seed] Created: {created}, Skipped (existing): {skipped}")


def migrate_existing_case_tags(db):
    """Register tags from existing cases into TagMaster and learn keywords."""
    cases = db.query(CSCase).filter(CSCase.tags != None, CSCase.tags != []).all()  # noqa: E711
    if not cases:
        print("[Migration] No cases with tags found.")
        return

    tag_count = 0
    learn_count = 0

    for case in cases:
        if not case.tags:
            continue

        keywords = extract_keywords(f"{case.title} {case.content or ''}")

        for tag_name in case.tags:
            tag_name = tag_name.strip()
            if not tag_name:
                continue

            tag = db.query(TagMaster).filter(TagMaster.name.ilike(tag_name)).first()
            if not tag:
                tag = TagMaster(
                    name=tag_name,
                    keyword_weights={},
                    usage_count=0,
                    created_by="system",
                )
                db.add(tag)
                db.flush()
                tag_count += 1

            tag.usage_count += 1
            weights = dict(tag.keyword_weights) if tag.keyword_weights else {}
            for word in keywords:
                weights[word] = weights.get(word, 0) + 1
            tag.keyword_weights = weights
            flag_modified(tag, "keyword_weights")
            learn_count += 1

    db.commit()
    print(f"[Migration] Cases processed: {len(cases)}, "
          f"New tags registered: {tag_count}, "
          f"Tag-keyword learns: {learn_count}")


def main():
    db = SessionLocal()
    try:
        print("=== Seed Tags ===")
        seed_default_tags(db)
        print("\n=== Migrate Existing Case Tags ===")
        migrate_existing_case_tags(db)
        print("\nDone!")
    finally:
        db.close()


if __name__ == "__main__":
    main()
