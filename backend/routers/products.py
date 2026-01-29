"""
Product CRUD 라우터.
"""

import csv
import io
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from database import get_db
from models import License, Product
from schemas import BulkUploadResult, LicenseRead, ProductCreate, ProductRead

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


@router.post("/bulk", response_model=BulkUploadResult, status_code=201)
async def bulk_upload_products(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """CSV 파일로 Product + License 일괄 등록.

    CSV 포맷 (헤더 필수):
    product,license
    ChatGPT,Free
    ChatGPT,Plus
    DALL-E,Basic
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="CSV 파일만 지원합니다.")

    content = await file.read()
    try:
        decoded = content.decode("utf-8")
    except UnicodeDecodeError:
        decoded = content.decode("cp949")  # 한글 Windows 환경 대응

    reader = csv.DictReader(io.StringIO(decoded))
    if not {"product", "license"}.issubset(set(reader.fieldnames or [])):
        raise HTTPException(
            status_code=400,
            detail="CSV 헤더에 'product', 'license' 컬럼이 필요합니다.",
        )

    products_created = 0
    products_existing = 0
    licenses_created = 0
    licenses_existing = 0
    errors = []

    for row_num, row in enumerate(reader, start=2):
        product_name = row.get("product", "").strip()
        license_name = row.get("license", "").strip()

        if not product_name or not license_name:
            errors.append(f"Row {row_num}: product 또는 license 값이 비어있음")
            continue

        # Product: get or create
        product = db.query(Product).filter(Product.name == product_name).first()
        if not product:
            product = Product(name=product_name)
            db.add(product)
            db.flush()
            products_created += 1
        else:
            products_existing += 1

        # License: get or create
        license_obj = (
            db.query(License)
            .filter(License.product_id == product.id, License.name == license_name)
            .first()
        )
        if not license_obj:
            license_obj = License(product_id=product.id, name=license_name)
            db.add(license_obj)
            licenses_created += 1
        else:
            licenses_existing += 1

    db.commit()

    return BulkUploadResult(
        products_created=products_created,
        products_existing=products_existing,
        licenses_created=licenses_created,
        licenses_existing=licenses_existing,
        errors=errors,
    )
