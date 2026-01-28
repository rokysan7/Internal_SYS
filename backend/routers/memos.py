"""
Product Memo / License Memo CRUD 라우터.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import License, LicenseMemo, Product, ProductMemo
from schemas import (
    LicenseMemoCreate,
    LicenseMemoRead,
    ProductMemoCreate,
    ProductMemoRead,
)

router = APIRouter(tags=["Memos"])


# ---------- Product Memo ----------


@router.get("/products/{product_id}/memos", response_model=List[ProductMemoRead])
def list_product_memos(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return (
        db.query(ProductMemo)
        .filter(ProductMemo.product_id == product_id)
        .order_by(ProductMemo.created_at.desc())
        .all()
    )


@router.post(
    "/products/{product_id}/memos",
    response_model=ProductMemoRead,
    status_code=201,
)
def create_product_memo(
    product_id: int,
    data: ProductMemoCreate,
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    # TODO: author_id는 인증 구현 후 토큰에서 추출. 현재는 임시로 1 사용.
    memo = ProductMemo(product_id=product_id, author_id=1, **data.model_dump())
    db.add(memo)
    db.commit()
    db.refresh(memo)
    return memo


# ---------- License Memo ----------


@router.get("/licenses/{license_id}/memos", response_model=List[LicenseMemoRead])
def list_license_memos(license_id: int, db: Session = Depends(get_db)):
    license_obj = db.query(License).filter(License.id == license_id).first()
    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")
    return (
        db.query(LicenseMemo)
        .filter(LicenseMemo.license_id == license_id)
        .order_by(LicenseMemo.created_at.desc())
        .all()
    )


@router.post(
    "/licenses/{license_id}/memos",
    response_model=LicenseMemoRead,
    status_code=201,
)
def create_license_memo(
    license_id: int,
    data: LicenseMemoCreate,
    db: Session = Depends(get_db),
):
    license_obj = db.query(License).filter(License.id == license_id).first()
    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")
    # TODO: author_id는 인증 구현 후 토큰에서 추출. 현재는 임시로 1 사용.
    memo = LicenseMemo(license_id=license_id, author_id=1, **data.model_dump())
    db.add(memo)
    db.commit()
    db.refresh(memo)
    return memo
