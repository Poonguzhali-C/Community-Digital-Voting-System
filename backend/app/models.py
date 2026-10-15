from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    """Naive UTC timestamp (all datetimes are stored as naive UTC in SQLite)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)  # bcrypt hash
    role: Mapped[str] = mapped_column(String(20), default="USER", nullable=False)

    votes: Mapped[list["Vote"]] = relationship(back_populates="user")


class Proposal(Base):
    __tablename__ = "proposals"
    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE','CLOSED','EXPIRED')", name="ck_proposal_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    deadline: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)

    votes: Mapped[list["Vote"]] = relationship(
        back_populates="proposal", cascade="all, delete-orphan", passive_deletes=True
    )


class Vote(Base):
    __tablename__ = "votes"
    __table_args__ = (
        UniqueConstraint("proposal_id", "user_id", name="uq_vote_proposal_user"),
        CheckConstraint("vote IN ('YES','NO','ABSTAIN')", name="ck_vote_value"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    proposal_id: Mapped[int] = mapped_column(
        ForeignKey("proposals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vote: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    proposal: Mapped[Proposal] = relationship(back_populates="votes")
    user: Mapped[User] = relationship(back_populates="votes")
