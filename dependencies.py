from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pathlib import Path
from sqlalchemy.orm import Session
import crud.user
from db.database import SessionLocal, engine, Base as db_Base
from models.user import User
from core.config import config

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_TIME = 2

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

db_Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def verify_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    db_user: User | None = None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        db_user = crud.user.get_user_by_username(db, username)
        if (db_user == None):
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return db_user

async def get_path(dirname: str, relative_path: str | None = None) -> str:
    source_path: str | None = config.get_dirpath(dirname)
    if source_path == None:
        raise Exception(f'dirname {dirname} is not exist!')
    if relative_path is None:
        relative_path = ''
    pathObject = Path(str(source_path)).joinpath(str(relative_path)).resolve()
    # 判断文件是否存在，并且文件不在源目录的上级目录
    if pathObject.exists() == False or pathObject.is_relative_to(str(source_path)) == False:
        raise Exception(f"The file path {str(pathObject)} is not exist!")
    return str(pathObject)


async def get_file(file: str, path: str = Depends(get_path)):
    pathObject = Path(path).joinpath(file).resolve()
    if pathObject.exists() == False or pathObject.is_relative_to(path) == False or pathObject.is_file() == False:
        raise Exception(f"The file {str(pathObject)} is not exist!")
    return str(pathObject)