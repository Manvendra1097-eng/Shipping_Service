"""fix delivery_partner user columns

Revision ID: 7b1c9f2a4d3e
Revises: ec540a10a71a
Create Date: 2026-06-07 12:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7b1c9f2a4d3e"
down_revision: Union[str, Sequence[str], None] = "ec540a10a71a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("delivery_partner", sa.Column("name", sa.String(), nullable=True))
    op.add_column("delivery_partner", sa.Column("email", sa.String(), nullable=True))
    op.add_column("delivery_partner", sa.Column("password", sa.String(), nullable=True))

    op.create_unique_constraint(
        "uq_delivery_partner_email", "delivery_partner", ["email"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_delivery_partner_email", "delivery_partner", type_="unique")
    op.drop_column("delivery_partner", "password")
    op.drop_column("delivery_partner", "email")
    op.drop_column("delivery_partner", "name")
