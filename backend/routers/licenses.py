"""
License CRUD 라우터.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import License, Product
from schemas import LicenseCreate, LicenseRead

router = APIRouter(prefix="/licenses", tags=["Licenses"])


@router.post("/", response_model=LicenseRead, status_code=201)
def create_license(data: LicenseCreate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    license_obj = License(**data.model_dump())
    db.add(license_obj)
    db.commit()
    db.refresh(license_obj)
    return license_obj


@router.get("/{license_id}", response_model=LicenseRead)
def get_license(license_id: int, db: Session = Depends(get_db)):
    license_obj = db.query(License).filter(License.id == license_id).first()
    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")
    return license_obj
