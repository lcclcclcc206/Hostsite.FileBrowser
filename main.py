from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse
from pathlib import Path
from type import FileInfo, DirContentInfo
import sys
import json
from typing import Dict, List
import uvicorn

dirs: List[Dict[str, str]] = []

with open(Path(sys.path[0]).joinpath('config.json'), 'r', encoding='utf-8') as f:
    data = json.load(f)
    dirs = data['dir']

for d in dirs:
    d['path'] = Path(d['path']).resolve().as_posix()


def getdir(dirname: str) -> str | None:
    source_path: str | None = None
    for d in dirs:
        if d['name'] == dirname:
            source_path = d['path']
            break
    # 判断 dirname 是否存在
    if source_path == None:
        return None
    else:
        return source_path

app = FastAPI()


@app.get('/')
async def get_alldirs() -> List[str]:
    dirlist: List[str] = []
    for d in dirs:
        dirlist.append(d['name'])
    return dirlist


@app.get('/{dirname}/info')
async def get_dirinfo(dirname: str, relative_path: str | None = None):
    source_path: str | None = getdir(dirname)
    if source_path == None:
        print(f'dirname {dirname} is not exist!')
        return None
    relative_path = '' if relative_path == None else relative_path
    pathObject = Path(str(source_path)).joinpath(
        str(relative_path)).resolve()
    # 判断文件是否存在，并且文件不在源目录的上级目录
    if pathObject.exists() == False or pathObject.is_relative_to(str(source_path)) == False:
        print(f"The file path {str(pathObject)} is not exist!")
        return {"message": "The file path is not exist!"}
    dirContentInfo = DirContentInfo(str(pathObject))
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
async def get_file(dirname: str, file: str, relative_path: str | None = None):
    source_path: str | None = getdir(dirname)
    if source_path == None:
        print(f'dirname {dirname} is not exist!')
        return None
    relative_path = '' if relative_path == None else relative_path
    pathObject = Path(str(source_path)).joinpath(
        str(relative_path), file).resolve()
    # 判断文件是否存在，并且文件不在源目录的上级目录，并且下载的路径为文件
    if pathObject.exists() == False or pathObject.is_relative_to(str(source_path)) == False or pathObject.is_file() == False:
        return {"message": f"The file path is not exist!"}
    fileResponse = FileResponse(path=pathObject.as_posix())
    fileResponse.headers['content-disposition'] = f'inline; filename="{pathObject.name}"'
    fileResponse.headers['cache-control'] = 'no-cache'
    return fileResponse


@app.post('/upload')
async def upload_files(dirname: str, files: List[UploadFile], relative_path: str | None = None):
    source_path: str | None = getdir(dirname)
    if source_path == None:
        print(f'dirname {dirname} is not exist!')
        return None
    relative_path = '' if relative_path == None else relative_path
    pathObject = Path(str(source_path)).joinpath(str(relative_path)).resolve()
    # 文件夹不存在就创建文件夹
    if (pathObject.exists() == False):
        pathObject.mkdir()
    for file in files:
        file_path = Path(str(pathObject), str(file.filename))
        with open(str(file_path), mode='wb') as f:
            f.write(await file.read())


if __name__ == '__main__':
    uvicorn.run('main:app', log_level='info')