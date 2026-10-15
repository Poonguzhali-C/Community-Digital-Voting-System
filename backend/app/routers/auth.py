from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..auth_dependencies import get_current_user
from ..database import get_db
from ..models import User
from ..schemas import MessageResponse, TokenResponse, UserLogin, UserRegister, UserResponse
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Public registration. The role is ALWAYS USER (admins are created with create_admin.py)."""
    exists = (
        db.query(User)
        .filter(func.lower(User.username) == user_data.username.lower())
        .first()
    )
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already exists")
    user = User(
        username=user_data.username,
        password=hash_password(user_data.password),
        role="USER",
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already exists")
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user or not verify_password(user_data.password, user.password):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(user_id=user.id, role=user.role)
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout", response_model=MessageResponse)
def logout(_: User = Depends(get_current_user)):
    """JWTs are stateless: the client discards the token. Endpoint validates the session
    and gives the SPA a server-confirmed logout step."""
    return {"message": "Logged out. Please discard your token."}
