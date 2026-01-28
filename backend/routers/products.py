"""
Product CRUD 라우터.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import License, Product
from schemas import LicenseRead, ProductCreate, ProductRead

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", response_model=List[ProductRead])
def list_products(
    search: Optional[str] = Query(None, description="제품명 검색"),
    db: Session = Depends(get_db),
):
    query = db.query(Product)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    return query.order_by(Product.created_at.desc()).all()


@router.post("/", response_model=ProductRead, status_code=201)
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    product = Product(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/{product_id}/licenses", response_model=List[LicenseRead])
def get_product_licenses(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return (
        db.query(License)
        .filter(License.product_id == product_id)
        .order_by(License.created_at.desc())
        .all()
    )
