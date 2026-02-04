"""
Common validation utilities.
"""

from fastapi import HTTPException, status


def validate_password(password: str) -> None:
    """Validate password meets minimum requirements (8+ characters)."""
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long",
        )
