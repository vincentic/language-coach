"""
Authentication routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db, models

router = APIRouter()


# Pydantic schemas
class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    native_language: str
    target_language: str

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    username: str | None = None
    email: str | None = None
    native_language: str | None = None
    target_language: str | None = None


@router.get("/me", response_model=UserResponse)
async def get_current_user(db: Session = Depends(get_db)):
    """Get current user"""
    user = db.query(models.User).filter(models.User.id == 1).first()
    if not user:
        # Create demo user if not exists
        user = models.User(
            id=1,
            username="demo",
            email="demo@example.com",
            password_hash="demo",
            native_language="en",
            target_language="es"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@router.put("/me", response_model=UserResponse)
async def update_user(
    username: str = None,
    email: str = None,
    native_language: str = None,
    target_language: str = None,
    db: Session = Depends(get_db)
):
    """Update user profile"""
    user = db.query(models.User).filter(models.User.id == 1).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if username:
        user.username = username
    if email:
        user.email = email
    if native_language:
        user.native_language = native_language
    if target_language:
        user.target_language = target_language

    db.commit()
    db.refresh(user)
    return user


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register new user"""
    # Check if user exists
    existing = db.query(models.User).filter(
        (models.User.email == user_data.email) |
        (models.User.username == user_data.username)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    # Create new user
    user = models.User(
        username=user_data.username,
        email=user_data.email,
        password_hash=user_data.password,  # In production, hash the password
        native_language="en",
        target_language="es"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login")
async def login(email: str, password: str, db: Session = Depends(get_db)):
    """Login user"""
    user = db.query(models.User).filter(models.User.email == email).first()
    if user and user.password_hash == password:  # In production, verify password hash
        return {"token": "mock-jwt-token", "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }}
    return {"error": "Invalid credentials"}, 401
