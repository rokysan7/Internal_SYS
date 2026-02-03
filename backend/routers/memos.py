"""
Product Memo / License Memo CRUD 라우터.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import License, LicenseMemo, Product, ProductMemo, User, UserRole
from routers.auth import get_current_user
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
        .options(joinedload(ProductMemo.author))
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
    current_user: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    memo = ProductMemo(
        product_id=product_id, author_id=current_user.id, **data.model_dump()
    )
    db.add(memo)
    db.commit()
    db.refresh(memo)
    memo.author = current_user
    return memo


@router.delete("/product-memos/{memo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_memo(
    memo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete product memo. Only author or ADMIN can delete."""
    memo = db.query(ProductMemo).filter(ProductMemo.id == memo_id).first()
    if not memo:
        raise HTTPException(status_code=404, detail="Memo not found")
    if memo.author_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Permission denied")
    db.delete(memo)
    db.commit()


# ---------- License Memo ----------


@router.get("/licenses/{license_id}/memos", response_model=List[LicenseMemoRead])
def list_license_memos(license_id: int, db: Session = Depends(get_db)):
    license_obj = db.query(License).filter(License.id == license_id).first()
    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")
    return (
        db.query(LicenseMemo)
        .options(joinedload(LicenseMemo.author))
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
    current_user: User = Depends(get_current_user),
):
    license_obj = db.query(License).filter(License.id == license_id).first()
    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")
    memo = LicenseMemo(
        license_id=license_id, author_id=current_user.id, **data.model_dump()
    )
    db.add(memo)
    db.commit()
    db.refresh(memo)
    memo.author = current_user
    return memo


@router.delete("/license-memos/{memo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_license_memo(
    memo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete license memo. Only author or ADMIN can delete."""
    memo = db.query(LicenseMemo).filter(LicenseMemo.id == memo_id).first()
    if not memo:
        raise HTTPException(status_code=404, detail="Memo not found")
    if memo.author_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Permission denied")
    db.delete(memo)
    db.commit()
