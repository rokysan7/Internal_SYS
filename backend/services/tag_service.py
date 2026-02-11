"""
Tag CRUD, keyword learning, and suggestion service.
Uses TagMaster table and extract_keywords() from similarity module.
"""

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from models import TagMaster
from services.similarity import extract_keywords


def get_or_create_tag(name: str, db: Session, created_by: str = "user") -> TagMaster:
    """Find an existing tag or create a new one.

    Tag names are stored stripped but case-preserved.
    Lookup is case-insensitive.
    """
    normalized = name.strip()
    if not normalized:
        raise ValueError("Tag name cannot be empty")

    tag = db.query(TagMaster).filter(TagMaster.name.ilike(normalized)).first()
    if tag:
        return tag

    tag = TagMaster(name=normalized, created_by=created_by, keyword_weights={})
    db.add(tag)
    db.flush()
    return tag


def learn_from_case(
    tags: list[str], title: str, content: str, db: Session
) -> int:
    """Learn keyword associations for each tag based on case text.

    For every tag the user assigned, extracts keywords from title+content
    and increments the tag's keyword_weights. Returns the number of
    keywords extracted.
    """
    keywords = extract_keywords(f"{title} {content}")
    if not keywords:
        return 0

    for tag_name in tags:
        tag = get_or_create_tag(tag_name, db)
        tag.usage_count += 1
        weights = dict(tag.keyword_weights) if tag.keyword_weights else {}
        for word in keywords:
            weights[word] = weights.get(word, 0) + 1
        tag.keyword_weights = weights
        flag_modified(tag, "keyword_weights")

    db.commit()
    return len(keywords)


def suggest_tags(
    title: str, content: str, db: Session, top_k: int = 5
) -> list[dict]:
    """Suggest tags based on keyword matching against TagMaster weights.

    Returns top_k tags sorted by score (keyword overlap / usage_count).
    """
    keywords = extract_keywords(f"{title} {content}")
    if not keywords:
        return []

    all_tags = db.query(TagMaster).all()
    scores: list[tuple[str, float, int]] = []

    for tag in all_tags:
        if not tag.keyword_weights:
            continue
        score = sum(tag.keyword_weights.get(w, 0) for w in keywords)
        if score > 0:
            normalized_score = score / max(tag.usage_count, 1)
            scores.append((tag.name, normalized_score, tag.usage_count))

    scores.sort(key=lambda x: x[1], reverse=True)
    return [
        {"name": name, "score": round(sc, 2), "usage_count": uc}
        for name, sc, uc in scores[:top_k]
    ]


def search_tags(query: str, db: Session, limit: int = 10) -> list[dict]:
    """Prefix search on TagMaster names, ordered by usage_count desc."""
    q = query.strip()
    if not q:
        return []

    tags = (
        db.query(TagMaster)
        .filter(TagMaster.name.ilike(f"{q}%"))
        .order_by(TagMaster.usage_count.desc())
        .limit(limit)
        .all()
    )
    return [{"name": t.name, "usage_count": t.usage_count} for t in tags]
