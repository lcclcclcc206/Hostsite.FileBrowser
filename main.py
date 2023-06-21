from fastapi import FastAPI, HTTPException, UploadFile, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from type import FileInfo, DirContentInfo, ConfigInfo, DirInfo
import sys, json
from typing import List
import uvicorn
import urllib.parse
from sqlalchemy.orm import Session
import crud, models, schemas
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


config = ConfigInfo()
# region init
with open(Path(sys.path[0]).joinpath('config.json'), 'r', encoding='utf-8') as f:
    data = json.load(f)
    dirs: List[DirInfo] = []
    for dir in data['dir']:
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


@app.post('/{dirname}/upload')
async def upload_file(file: UploadFile, path: str = Depends(get_path)):
    pathObject = Path(path)
    file_path = Path(str(pathObject), str(file.filename))
    with open(str(file_path), mode='wb') as f:
        f.write(await file.read())


@app.post('/{dirname}/delete')
async def delete_file(file_path: str = Depends(get_file)):
    Path.unlink(Path(file_path))

@app.post('/user', response_model=schemas.User)
def get_user(username: str, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000, log_level='error')
