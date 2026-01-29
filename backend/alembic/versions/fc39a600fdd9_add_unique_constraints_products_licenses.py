"""add_unique_constraints_products_licenses

Revision ID: fc39a600fdd9
Revises: 0f1649a11052
Create Date: 2026-01-29 12:20:09.615433

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fc39a600fdd9'
down_revision: Union[str, Sequence[str], None] = '0f1649a11052'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint("uq_products_name", "products", ["name"])
    op.create_unique_constraint("uq_licenses_product_name", "licenses", ["product_id", "name"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_licenses_product_name", "licenses", type_="unique")
    op.drop_constraint("uq_products_name", "products", type_="unique")
