from fastapi import FastAPI, HTTPException, UploadFile, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from pathlib import Path
from pydantic import BaseModel
from type import FileInfo, DirContentInfo, ConfigInfo, DirInfo
import sys
import json
from datetime import datetime, timedelta
from typing import List
import uvicorn
import urllib.parse
from sqlalchemy.orm import Session
import dataEntry.crud
import dataEntry.models
import dataEntry.schemas
from dataEntry.database import SessionLocal, engine

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_TIME = 2

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

dataEntry.models.Base.metadata.create_all(bind=engine)


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
    db_user: dataEntry.models.User | None = None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        db_user = dataEntry.crud.get_user_by_username(db, username)
        if (db_user == None):
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return db_user

config = ConfigInfo()
# region init
with open(Path(sys.path[0]).joinpath('config.json'), 'r', encoding='utf-8') as f:
    config_data = json.load(f)
    dirs: List[DirInfo] = []
    for dir in config_data['dir']:
        dir_info = DirInfo(dir['name'], dir['path'])
        dirs.append(dir_info)
    for dir in dirs:
        config.dir_dictionary[dir.name] = dir

for dirname in config.dir_dictionary:
    config.dir_dictionary[dirname].path = Path(
        config.dir_dictionary[dirname].path).resolve().as_posix()
# endregion


app = FastAPI()

origins = [
    '*',
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get('/')
async def get_alldirs() -> List[str]:
    dirlist: List[str] = []
    for dir in config.dir_dictionary.values():
        dirlist.append(dir.name)
    return dirlist


@app.get('/{dirname}/info')
async def get_dirinfo(path: str = Depends(get_path)):
    dirContentInfo = DirContentInfo(path)
    for child_path in Path(dirContentInfo.source_path).iterdir():
        file = FileInfo(child_path.is_file(), child_path.name,
                        child_path.stat().st_mtime, child_path.stat().st_size)
        if child_path.is_file():
            dirContentInfo.fileList.append(file)
        else:
            dirContentInfo.dirlist.append(file)
    response = {
        'dirlist': dirContentInfo.dirlist,
        'filelist': dirContentInfo.fileList
    }
    return response


@app.get('/{dirname}/download')
async def download_file(inline: bool = True, file_path: str = Depends(get_file)):
    pathObject = Path(file_path)
    fileResponse = FileResponse(path=pathObject.as_posix())
    filename_encode = urllib.parse.urlencode({
        'filename': f"{pathObject.name}"
    })
    fileResponse.headers['content-disposition'] = f'{"inline" if inline else "attachment"}; {filename_encode}'
    fileResponse.headers['cache-control'] = 'no-cache'
    fileResponse.charset = 'utf-8'
    return fileResponse


@app.post('/{dirname}/upload', dependencies=[Depends(verify_token)])
async def upload_file(file: UploadFile, path: str = Depends(get_path)):
    pathObject = Path(path)
    file_path = Path(str(pathObject), str(file.filename))
    with open(str(file_path), mode='wb') as f:
        f.write(await file.read())


@app.post('/{dirname}/delete', dependencies=[Depends(verify_token)])
async def delete_file(file_path: str = Depends(get_file)):
    Path.unlink(Path(file_path))


class Token(BaseModel):
    access_token: str
    token_type: str
    username: str
    active_time: float
    expire_time: float


def verify_user(db_user: dataEntry.models.User, password: str):
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


@app.post('/token', response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_user = dataEntry.crud.get_user_by_username(db, form_data.username)
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


@app.post('/token/refresh', response_model=Token)
async def refresh_token(db_user: dataEntry.models.User = Depends(verify_token)):
    access_token_expires = timedelta(hours=ACCESS_TOKEN_EXPIRE_TIME)
    access_token = create_access_token(
        data={"sub": db_user.username},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "username": db_user.username, "active_time": datetime.utcnow().timestamp(), "expire_time": (datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_TIME)).timestamp(), }


if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000, log_level='error')
