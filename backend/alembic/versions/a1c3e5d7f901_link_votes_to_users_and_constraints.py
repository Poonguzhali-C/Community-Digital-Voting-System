"""link votes to users, add CASCADE + CHECK constraints

Revision ID: a1c3e5d7f901
Revises: 6f9740da17eb
Create Date: 2026-10-15 15:00:00

votes.user_id used to be a free-text string supplied by the client (insecure: anyone could
vote as anyone). It becomes an INTEGER foreign key to users.id.  Legacy free-text voters
are preserved: a placeholder user (no usable password, role USER) is created for each
distinct legacy value so that no existing vote is lost and results stay identical.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1c3e5d7f901"
down_revision: Union[str, Sequence[str], None] = "6f9740da17eb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

LEGACY_PASSWORD = "!legacy-voter-no-login"  # not a valid bcrypt hash -> can never log in


def upgrade() -> None:
    bind = op.get_bind()

    # 1) proposals: enforce allowed statuses at database level
    with op.batch_alter_table("proposals", recreate="always") as batch:
        batch.create_check_constraint(
            "ck_proposal_status", "status IN ('ACTIVE','CLOSED','EXPIRED')"
        )

    # 2) placeholder users for legacy free-text voters
    legacy = [r[0] for r in bind.execute(sa.text("SELECT DISTINCT user_id FROM votes")).fetchall()]
    for name in legacy:
        exists = bind.execute(
            sa.text("SELECT id FROM users WHERE username = :u"), {"u": str(name)}
        ).fetchone()
        if not exists:
            bind.execute(
                sa.text("INSERT INTO users (username, password, role) VALUES (:u, :p, 'USER')"),
                {"u": str(name), "p": LEGACY_PASSWORD},
            )

    # 3) rebuild votes with INTEGER user_id FK, CASCADE, UNIQUE and CHECK
    op.create_table(
        "votes_new",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("proposal_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("vote", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["proposal_id"], ["proposals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("proposal_id", "user_id", name="uq_vote_proposal_user"),
        sa.CheckConstraint("vote IN ('YES','NO','ABSTAIN')", name="ck_vote_value"),
    )
    op.execute(
        """
        INSERT INTO votes_new (id, proposal_id, user_id, vote, created_at)
        SELECT v.id, v.proposal_id, u.id, UPPER(v.vote), v.created_at
        FROM votes v JOIN users u ON u.username = v.user_id
        """
    )
    op.drop_table("votes")
    op.rename_table("votes_new", "votes")
    op.create_index("ix_votes_id", "votes", ["id"])
    op.create_index("ix_votes_proposal_id", "votes", ["proposal_id"])
    op.create_index("ix_votes_user_id", "votes", ["user_id"])


def downgrade() -> None:
    op.create_table(
        "votes_old",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("proposal_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=100), nullable=False),
        sa.Column("vote", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["proposal_id"], ["proposals.id"]),
        sa.UniqueConstraint("proposal_id", "user_id", name="uq_vote_proposal_user"),
    )
    op.execute(
        """
        INSERT INTO votes_old (id, proposal_id, user_id, vote, created_at)
        SELECT v.id, v.proposal_id, u.username, v.vote, v.created_at
        FROM votes v JOIN users u ON u.id = v.user_id
        """
    )
    op.drop_table("votes")
    op.rename_table("votes_old", "votes")
    op.create_index("ix_votes_id", "votes", ["id"])
    op.create_index("ix_votes_proposal_id", "votes", ["proposal_id"])
    op.create_index("ix_votes_user_id", "votes", ["user_id"])
    with op.batch_alter_table("proposals", recreate="always") as batch:
        batch.drop_constraint("ck_proposal_status", type_="check")
