"""User schemas."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserPreferences(BaseModel):
    """User preference settings."""

    theme: str = "light"  # light, dark, auto
    feed_filter_type: str | None = None  # Filter events by type
    feed_filter_agent: str | None = None  # Filter events by agent
    notifications_enabled: bool = True
    sound_enabled: bool = False


class UserCreate(BaseModel):
    """Schema for user registration."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """Schema for user login."""

    username: str
    password: str


class UserResponse(BaseModel):
    """Schema for user response (no sensitive data)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    is_active: bool
    is_admin: bool
    created_at: float
    last_login: float | None
    preferences: dict = {}


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    email: EmailStr | None = None
    preferences: UserPreferences | None = None


class PasswordChange(BaseModel):
    """Schema for changing password."""

    current_password: str
    new_password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    """Schema for token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""

    refresh_token: str
