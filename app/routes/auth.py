from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin
from app.utils.security import get_password_hash, verify_password, create_access_token

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/register",
    summary="Register a new user",
    description="Creates a new user account with the provided email and password. Email must be unique.",
    responses={
        201: {"description": "User registered successfully"},
        400: {"description": "Email already registered"},
        500: {"description": "Internal server error"},
    },
)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_pw)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return JSONResponse(
        status_code=201, content={"message": "User registered successfully"}
    )


@router.post(
    "/login",
    summary="Authenticate user and retrieve JWT",
    description="Validates user credentials and returns a JWT token for use in authenticated endpoints.",
    responses={
        200: {"description": "Authentication successful, returns JWT"},
        401: {"description": "Invalid credentials"},
        500: {"description": "Internal server error"},
    },
)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    token = create_access_token({"sub": db_user.email})
    return {"access_token": token, "token_type": "bearer"}