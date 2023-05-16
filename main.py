from fastapi import FastAPI
from fastapi.responses import FileResponse
from pathlib import Path
import os,sys,json
from typing import Dict, List

dirs: List[Dict[str, str]] = []

with open(Path(sys.path[0]).joinpath('config.json'), 'r', encoding='utf-8') as f:
    data = json.load(f)
    dirs = data['dir']

for d in dirs:
    d['path'] = Path(d['path']).resolve().as_posix()

app = FastAPI()

@app.get('/')
def get_dirs() -> List[str]:
    dirlist: List[str] = []
    for d in dirs:
        dirlist.append(d['name'])
    return dirlist


@app.get('/{dirname}')
def get_dircontent(dirname: str, filepath: str | None = None):
    if (filepath is None):
        return None
    else:
        lpath: str | None = None
        rpath = filepath
        for d in dirs:
            if d['name'] == dirname:
                lpath = d['path']
                break
        if lpath != None:
            pathObject = Path(str(lpath)).joinpath(rpath).resolve()
            if pathObject.exists() == False or pathObject.is_relative_to(str(lpath)) == False:
                return None
            fileResponse = FileResponse(path=pathObject.as_posix())
            fileResponse.headers['content-disposition'] = f'inline; filename="{pathObject.name}"'
            fileResponse.headers['cache-control'] = 'no-cache'
            return fileResponse
