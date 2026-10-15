"""add vote uniqueness constraint

Revision ID: 852cf976f459
Revises: 
Create Date: 2026-10-15 09:34:45.444541

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '852cf976f459'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("votes", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "uq_vote_proposal_user",
            ["proposal_id", "user_id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("votes", schema=None) as batch_op:
        batch_op.drop_constraint(
            "uq_vote_proposal_user",
            type_="unique",
        )
