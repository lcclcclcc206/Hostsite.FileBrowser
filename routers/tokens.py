from fastapi import HTTPException,  Depends, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import crud.user
from models.user import User
from dependencies import get_db, verify_token
from dependencies import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_TIME
from schemas.token import Token

router = APIRouter(
    tags=["token"]
)

def verify_user(db_user: User, password: str):
    if db_user is None:
        return False
    elif password != db_user.password:
        return False
    return True

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.post('/token', response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_user = crud.user.get_user_by_username(db, form_data.username)
    if verify_user(db_user, form_data.password) == False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(hours=ACCESS_TOKEN_EXPIRE_TIME)
    access_token = create_access_token(
        data={"sub": db_user.username},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "username": db_user.username, "active_time": datetime.utcnow().timestamp(), "expire_time": (datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_TIME)).timestamp(), }


@router.post('/token/refresh', response_model=Token)
async def refresh_token(db_user: User = Depends(verify_token)):
    access_token_expires = timedelta(hours=ACCESS_TOKEN_EXPIRE_TIME)
    access_token = create_access_token(
        data={"sub": db_user.username},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "username": db_user.username, "active_time": datetime.utcnow().timestamp(), "expire_time": (datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_TIME)).timestamp(), }


@router.post('/token/verify', dependencies=[Depends(verify_token)])
async def verify_token_api():
    return None
