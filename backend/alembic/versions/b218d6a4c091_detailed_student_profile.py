"""Add academic and portfolio details to profiles.

Revision ID: b218d6a4c091
Revises: 7c78ce448787
Create Date: 2026-10-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b218d6a4c091"
down_revision: Union[str, None] = "7c78ce448787"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("profiles") as batch_op:
        batch_op.add_column(sa.Column("degree", sa.String(length=160), nullable=True))
        batch_op.add_column(sa.Column("field_of_study", sa.String(length=160), nullable=True))
        batch_op.add_column(sa.Column("academic_year", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("gpa", sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column("academic_summary", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("portfolio_url", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("linkedin_url", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("github_url", sa.String(length=500), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("profiles") as batch_op:
        batch_op.drop_column("github_url")
        batch_op.drop_column("linkedin_url")
        batch_op.drop_column("portfolio_url")
        batch_op.drop_column("academic_summary")
        batch_op.drop_column("gpa")
        batch_op.drop_column("academic_year")
        batch_op.drop_column("field_of_study")
        batch_op.drop_column("degree")
