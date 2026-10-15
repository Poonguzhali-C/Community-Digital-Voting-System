from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth_dependencies import get_current_admin
from ..database import get_db
from ..models import Proposal, User, Vote
from ..schemas import AdminStats, AdminUser
from ..services import expire_overdue

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(get_current_admin)])


@router.get("/stats", response_model=AdminStats)
def stats(db: Session = Depends(get_db)):
    expire_overdue(db)

    def count_status(s: str) -> int:
        return db.query(Proposal).filter(Proposal.status == s).count()

    return AdminStats(
        users=db.query(User).count(),
        admins=db.query(User).filter(User.role == "ADMIN").count(),
        proposals=db.query(Proposal).count(),
        active=count_status("ACTIVE"),
        closed=count_status("CLOSED"),
        expired=count_status("EXPIRED"),
        votes=db.query(Vote).count(),
    )


@router.get("/users", response_model=list[AdminUser])
def users(db: Session = Depends(get_db)):
    rows = (
        db.query(User, func.count(Vote.id))
        .outerjoin(Vote, Vote.user_id == User.id)
        .group_by(User.id)
        .order_by(User.id)
        .all()
    )
    return [AdminUser(id=u.id, username=u.username, role=u.role, votes_cast=n) for u, n in rows]
