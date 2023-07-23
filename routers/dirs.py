from fastapi import UploadFile, Depends, APIRouter
from fastapi.responses import FileResponse
from pathlib import Path
from type import FileInfo, DirContentInfo
from typing import List
import urllib.parse
from core.config import config
from dependencies import get_file, get_path, verify_token

router = APIRouter(
    tags=["dir"]
)

@router.get('/')
async def get_alldirs() -> List[str]:
    dirlist: List[str] = []
    for dir in config.dir_dictionary.values():
        dirlist.append(dir.name)
    return dirlist


@router.get('/{dirname}/info')
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


@router.get('/{dirname}/download')
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


@router.post('/{dirname}/upload', dependencies=[Depends(verify_token)])
async def upload_file(file: UploadFile, path: str = Depends(get_path)):
    pathObject = Path(path)
    file_path = Path(str(pathObject), str(file.filename))
    with open(str(file_path), mode='wb') as f:
        f.write(await file.read())


@router.post('/{dirname}/delete', dependencies=[Depends(verify_token)])
async def delete_file(file_path: str = Depends(get_file)):
    Path.unlink(Path(file_path))
