from typing import Dict, List
from pathlib import Path
import json
import sys
from schemas.io import DirInfo

class ConfigInfo:
    def __init__(self) -> None:
        self.dir_dictionary: Dict[str, DirInfo] = {}
        pass

    def get_dirpath(self, dirname: str) -> str | None:
        dirinfo = self.dir_dictionary.get(dirname)
        if not dirinfo:
            return None
        else:
            return dirinfo.path
        
config = ConfigInfo()
with open(Path(sys.path[0]).joinpath('core/config.json'), 'r', encoding='utf-8') as f:
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