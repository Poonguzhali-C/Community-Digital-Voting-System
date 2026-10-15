from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal, Optional

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    PlainSerializer,
)


def _to_naive_utc(value: datetime) -> datetime:
    """Aware datetimes are converted to UTC; naive ones are assumed to already be UTC."""
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def _serialize_utc(value: datetime) -> str:
    """Emit ISO-8601 with an explicit 'Z' so browsers never mistake UTC for local time."""
    return value.replace(microsecond=0).isoformat() + "Z"


InputDateTime = Annotated[datetime, AfterValidator(_to_naive_utc)]
OutputDateTime = Annotated[datetime, PlainSerializer(_serialize_utc, return_type=str)]

VoteChoice = Literal["YES", "NO", "ABSTAIN"]


# ---------- auth ----------
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(..., min_length=8, max_length=72)


class UserLogin(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: int
    username: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    message: str


# ---------- proposals ----------
class ProposalCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=3, max_length=5000)
    # Optional: defaults to 2 days from creation (PDF requirement)
    deadline: Optional[InputDateTime] = None


class ProposalResponse(BaseModel):
    id: int
    title: str
    description: str
    created_at: OutputDateTime
    deadline: OutputDateTime
    status: Literal["ACTIVE", "CLOSED", "EXPIRED"]
    yes: int = 0
    no: int = 0
    abstain: int = 0
    total: int = 0
    my_vote: Optional[VoteChoice] = None
    my_vote_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class ResultsResponse(BaseModel):
    proposal_id: int
    status: str
    yes: int
    no: int
    abstain: int
    total: int
    yes_percent: float
    no_percent: float
    abstain_percent: float


# ---------- votes ----------
class VoteCreate(BaseModel):
    vote: VoteChoice


class VoteUpdate(BaseModel):
    vote: VoteChoice


class VoteResponse(BaseModel):
    id: int
    proposal_id: int
    user_id: int
    voter_name: str
    vote: VoteChoice
    created_at: OutputDateTime


# ---------- admin ----------
class AdminStats(BaseModel):
    users: int
    admins: int
    proposals: int
    active: int
    closed: int
    expired: int
    votes: int


class AdminUser(BaseModel):
    id: int
    username: str
    role: str
    votes_cast: int


def default_deadline(now: datetime) -> datetime:
    return now + timedelta(days=2)
