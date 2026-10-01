from fastapi.security import OAuth2PasswordRequestForm
from fastapi import HTTPException, status, Depends, APIRouter

from typing import Annotated
from database import Session, get_db
from auth import authenticate_user, create_token, get_user, password_hash
from schemas import Token, UserOut, UserCreate
from models import UserDB

router = APIRouter()


@router.post("/token", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
):

    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=("password or username are incorrect"),
        )

    access_token = create_token(user.username)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def registre(
    form_data: UserCreate, db: Annotated[Session, Depends(get_db)]
) -> UserOut:
    user = get_user(form_data.username, db)
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="username already registered"
        )
    user = UserDB(
        username=form_data.username,
        hashed_password=password_hash.hash(form_data.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user
