
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, update
from sqlalchemy.orm import Session

from .models import Proposal, Vote, utcnow
from .schemas import ProposalResponse, ResultsResponse


def expire_overdue(db: Session) -> None:
    """Flip every ACTIVE proposal whose deadline has passed to EXPIRED (automatic expiry)."""
    db.execute(
        update(Proposal)
        .where(Proposal.status == "ACTIVE", Proposal.deadline <= utcnow())
        .values(status="EXPIRED")
    )
    db.commit()


def get_proposal_or_404(db: Session, proposal_id: int) -> Proposal:
    """Fetch a proposal and apply lazy expiry so the status is always current."""
    proposal = db.get(Proposal, proposal_id)
    if proposal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proposal not found")
    if proposal.status == "ACTIVE" and proposal.deadline <= utcnow():
        proposal.status = "EXPIRED"
        db.commit()
        db.refresh(proposal)
    return proposal


def ensure_votable(proposal: Proposal, action: str) -> None:
    """Rule: votes can be cast / changed / revoked ONLY while the proposal is active."""
    if proposal.status == "CLOSED":
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Proposal is closed; cannot {action} a vote"
        )
    if proposal.status == "EXPIRED" or proposal.deadline <= utcnow():
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Proposal has expired; cannot {action} a vote"
        )


def tally(db: Session, proposal_ids: list[int]) -> dict[int, dict[str, int]]:
    """Vote counts per proposal, computed from the votes table (never cached/hardcoded)."""
    counts = {pid: {"YES": 0, "NO": 0, "ABSTAIN": 0} for pid in proposal_ids}
    if not proposal_ids:
        return counts
    rows = (
        db.query(Vote.proposal_id, Vote.vote, func.count(Vote.id))
        .filter(Vote.proposal_id.in_(proposal_ids))
        .group_by(Vote.proposal_id, Vote.vote)
        .all()
    )
    for pid, choice, n in rows:
        counts[pid][choice] = n
    return counts


def build_proposal_responses(
    db: Session, proposals: list[Proposal], user_id: Optional[int]
) -> list[ProposalResponse]:
    counts = tally(db, [p.id for p in proposals])
    mine: dict[int, Vote] = {}
    if user_id is not None and proposals:
        for v in (
            db.query(Vote)
            .filter(Vote.user_id == user_id, Vote.proposal_id.in_([p.id for p in proposals]))
            .all()
        ):
            mine[v.proposal_id] = v
    out = []
    for p in proposals:
        c = counts[p.id]
        v = mine.get(p.id)
        out.append(
            ProposalResponse(
                id=p.id,
                title=p.title,
                description=p.description,
                created_at=p.created_at,
                deadline=p.deadline,
                status=p.status,
                yes=c["YES"],
                no=c["NO"],
                abstain=c["ABSTAIN"],
                total=sum(c.values()),
                my_vote=v.vote if v else None,
                my_vote_id=v.id if v else None,
            )
        )
    return out


def build_results(db: Session, proposal: Proposal) -> ResultsResponse:
    c = tally(db, [proposal.id])[proposal.id]
    total = sum(c.values())

    def pct(n: int) -> float:
        return round(n * 100 / total, 1) if total else 0.0

    return ResultsResponse(
        proposal_id=proposal.id,
        status=proposal.status,
        yes=c["YES"],
        no=c["NO"],
        abstain=c["ABSTAIN"],
        total=total,
        yes_percent=pct(c["YES"]),
        no_percent=pct(c["NO"]),
        abstain_percent=pct(c["ABSTAIN"]),
    )


def vote_to_response(vote: Vote) -> dict:
    return {
        "id": vote.id,
        "proposal_id": vote.proposal_id,
        "user_id": vote.user_id,
        "voter_name": vote.user.username,
        "vote": vote.vote,
        "created_at": vote.created_at,
    }


__all__ = [
    "expire_overdue",
    "get_proposal_or_404",
    "ensure_votable",
    "tally",
    "build_proposal_responses",
    "build_results",
    "vote_to_response",
]
