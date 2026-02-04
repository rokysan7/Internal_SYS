"""
License CRUD 라우터.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import CSCase, License, LicenseMemo, Product, User, UserRole
from routers.auth import get_current_user
from schemas import LicenseCreate, LicenseRead, LicenseUpdate

router = APIRouter(prefix="/licenses", tags=["Licenses"])


@router.post("/", response_model=LicenseRead, status_code=201)
def create_license(data: LicenseCreate, db: Session = Depends(get_db)):
    """Create a new license under a product."""
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
    """Get a single license by ID."""
    license_obj = db.query(License).filter(License.id == license_id).first()
    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")
    return license_obj


@router.put("/{license_id}", response_model=LicenseRead)
def update_license(
    license_id: int,
    data: LicenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update license. ADMIN only."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="ADMIN only")
    license_obj = db.query(License).filter(License.id == license_id).first()
    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(license_obj, key, value)
    db.commit()
    db.refresh(license_obj)
    return license_obj


@router.delete("/{license_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_license(
    license_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete license. ADMIN only. Cannot delete if linked to CS Cases."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="ADMIN only")
    license_obj = db.query(License).filter(License.id == license_id).first()
    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")
    # Check if linked to any CS Cases
    case_count = db.query(CSCase).filter(CSCase.license_id == license_id).count()
    if case_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete: {case_count} CS Case(s) linked to this license",
        )
    # Delete related memos
    db.query(LicenseMemo).filter(LicenseMemo.license_id == license_id).delete()
    db.delete(license_obj)
    db.commit()
