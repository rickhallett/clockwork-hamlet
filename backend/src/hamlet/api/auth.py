"""Authentication API routes."""

import time

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from hamlet.api.deps import get_db
from hamlet.auth.deps import get_current_active_user
from hamlet.auth.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from hamlet.db.models import RefreshToken, User
from hamlet.schemas.user import (
    PasswordChange,
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserPreferences,
    UserResponse,
    UserUpdate,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if username exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        created_at=time.time(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return _user_to_response(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Login and get access/refresh tokens."""
    # Find user by username
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    # Update last login
    user.last_login = time.time()

    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token_str, expires_at = create_refresh_token()

    # Store refresh token
    refresh_token = RefreshToken(
        token=refresh_token_str,
        user_id=user.id,
        created_at=time.time(),
        expires_at=expires_at,
    )
    db.add(refresh_token)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """Refresh access token using refresh token."""
    # Find the refresh token
    refresh_token = (
        db.query(RefreshToken)
        .filter(RefreshToken.token == request.refresh_token)
        .first()
    )

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Check if token is revoked or expired
    if refresh_token.revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )

    if refresh_token.expires_at < time.time():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )

    # Get user
    user = db.query(User).filter(User.id == refresh_token.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Revoke old refresh token
    refresh_token.revoked = True
    refresh_token.revoked_at = time.time()

    # Create new tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token_str, expires_at = create_refresh_token()

    # Store new refresh token
    new_refresh_token = RefreshToken(
        token=new_refresh_token_str,
        user_id=user.id,
        created_at=time.time(),
        expires_at=expires_at,
    )
    db.add(new_refresh_token)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token_str,
    )


@router.post("/logout")
async def logout(
    request: RefreshTokenRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Logout and revoke refresh token."""
    # Find and revoke the refresh token
    refresh_token = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token == request.refresh_token,
            RefreshToken.user_id == current_user.id,
        )
        .first()
    )

    if refresh_token and not refresh_token.revoked:
        refresh_token.revoked = True
        refresh_token.revoked_at = time.time()
        db.commit()

    return {"message": "Successfully logged out"}


@router.post("/logout-all")
async def logout_all(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Logout from all sessions by revoking all refresh tokens."""
    now = time.time()
    db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.revoked == False,
    ).update({"revoked": True, "revoked_at": now})
    db.commit()

    return {"message": "Successfully logged out from all sessions"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
):
    """Get current user profile."""
    return _user_to_response(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update current user profile."""
    if update_data.email is not None:
        # Check if email is taken by another user
        existing = (
            db.query(User)
            .filter(User.email == update_data.email, User.id != current_user.id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        current_user.email = update_data.email

    if update_data.preferences is not None:
        current_user.preferences_dict = update_data.preferences.model_dump()

    db.commit()
    db.refresh(current_user)

    return _user_to_response(current_user)


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Change current user's password."""
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )

    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()

    return {"message": "Password changed successfully"}


@router.get("/preferences", response_model=UserPreferences)
async def get_preferences(
    current_user: User = Depends(get_current_active_user),
):
    """Get current user's preferences."""
    prefs = current_user.preferences_dict
    return UserPreferences(**prefs) if prefs else UserPreferences()


@router.put("/preferences", response_model=UserPreferences)
async def update_preferences(
    preferences: UserPreferences,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update current user's preferences."""
    current_user.preferences_dict = preferences.model_dump()
    db.commit()

    return preferences


def _user_to_response(user: User) -> UserResponse:
    """Convert User model to response schema."""
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        is_admin=user.is_admin,
        created_at=user.created_at,
        last_login=user.last_login,
        preferences=user.preferences_dict,
    )
