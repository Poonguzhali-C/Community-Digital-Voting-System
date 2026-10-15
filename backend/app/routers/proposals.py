from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..auth_dependencies import get_current_admin, get_current_user, get_optional_user
from ..config import ALLOW_USER_PROPOSALS
from ..database import get_db
from ..models import Proposal, User, Vote, utcnow
from ..schemas import (
    ProposalCreate,
    ProposalResponse,
    ResultsResponse,
    VoteCreate,
    VoteResponse,
    default_deadline,
)
from ..services import (
    build_proposal_responses,
    build_results,
    ensure_votable,
    expire_overdue,
    get_proposal_or_404,
    vote_to_response,
)

router = APIRouter(prefix="/proposals", tags=["Proposals"])


@router.post("/", response_model=ProposalResponse, status_code=status.HTTP_201_CREATED)
def create_proposal(
    payload: ProposalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not ALLOW_USER_PROPOSALS and current_user.role != "ADMIN":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only admins can create proposals")
    now = utcnow()
    deadline = payload.deadline or default_deadline(now)
    if deadline <= now:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Deadline must be in the future")
    proposal = Proposal(
        title=payload.title.strip(),
        description=payload.description.strip(),
        deadline=deadline,
        status="ACTIVE",
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return build_proposal_responses(db, [proposal], current_user.id)[0]


@router.get("/", response_model=list[ProposalResponse])
def list_proposals(
    status_filter: Optional[str] = Query(None, alias="status", pattern="^(ACTIVE|CLOSED|EXPIRED)$"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    expire_overdue(db)
    query = db.query(Proposal)
    if status_filter:
        query = query.filter(Proposal.status == status_filter)
    proposals = query.order_by(Proposal.created_at.desc(), Proposal.id.desc()).all()
    return build_proposal_responses(db, proposals, current_user.id if current_user else None)


@router.get("/{proposal_id}", response_model=ProposalResponse)
def get_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    proposal = get_proposal_or_404(db, proposal_id)
    return build_proposal_responses(db, [proposal], current_user.id if current_user else None)[0]


@router.get("/{proposal_id}/results", response_model=ResultsResponse)
def proposal_results(proposal_id: int, db: Session = Depends(get_db)):
    return build_results(db, get_proposal_or_404(db, proposal_id))


@router.post(
    "/{proposal_id}/vote",
    response_model=VoteResponse,
    status_code=status.HTTP_201_CREATED,
)
def cast_vote(
    proposal_id: int,
    payload: VoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The voter is ALWAYS the authenticated user (never taken from the request body)."""
    proposal = get_proposal_or_404(db, proposal_id)
    ensure_votable(proposal, "cast")
    already = (
        db.query(Vote)
        .filter(Vote.proposal_id == proposal_id, Vote.user_id == current_user.id)
        .first()
    )
    if already:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "You have already voted on this proposal. Revoke your vote to change it.",
        )
    vote = Vote(proposal_id=proposal_id, user_id=current_user.id, vote=payload.vote)
    db.add(vote)
    try:
        db.commit()
    except IntegrityError:  # uq_vote_proposal_user: race between two simultaneous requests
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "You have already voted on this proposal.")
    db.refresh(vote)
    return vote_to_response(vote)


@router.patch("/{proposal_id}/close", response_model=ProposalResponse)
def close_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    proposal = get_proposal_or_404(db, proposal_id)
    if proposal.status == "CLOSED":
        raise HTTPException(status.HTTP_409_CONFLICT, "Proposal is already closed")
    if proposal.status == "EXPIRED":
        raise HTTPException(status.HTTP_409_CONFLICT, "Proposal has already expired")
    proposal.status = "CLOSED"
    db.commit()
    db.refresh(proposal)
    return build_proposal_responses(db, [proposal], admin.id)[0]
