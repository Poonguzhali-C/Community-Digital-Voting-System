from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth_dependencies import get_current_user
from ..database import get_db
from ..models import User, Vote
from ..schemas import MessageResponse, VoteResponse, VoteUpdate
from ..services import ensure_votable, get_proposal_or_404, vote_to_response

router = APIRouter(prefix="/votes", tags=["Votes"])


def _own_vote_or_error(db: Session, vote_id: int, user: User) -> Vote:
    vote = db.get(Vote, vote_id)
    if vote is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vote not found")
    if vote.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only modify your own vote")
    return vote


@router.get("/me", response_model=list[VoteResponse])
def my_votes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    votes = (
        db.query(Vote)
        .filter(Vote.user_id == current_user.id)
        .order_by(Vote.created_at.desc())
        .all()
    )
    return [vote_to_response(v) for v in votes]


@router.put("/{vote_id}", response_model=VoteResponse)
def change_vote(
    vote_id: int,
    payload: VoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change an existing vote (allowed only while the proposal is active)."""
    vote = _own_vote_or_error(db, vote_id, current_user)
    ensure_votable(get_proposal_or_404(db, vote.proposal_id), "change")
    vote.vote = payload.vote
    db.commit()
    db.refresh(vote)
    return vote_to_response(vote)


@router.delete("/{vote_id}", response_model=MessageResponse)
def revoke_vote(
    vote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revoke a vote (allowed only while the proposal is active)."""
    vote = _own_vote_or_error(db, vote_id, current_user)
    ensure_votable(get_proposal_or_404(db, vote.proposal_id), "revoke")
    db.delete(vote)
    db.commit()
    return {"message": "Vote revoked successfully"}
