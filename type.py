from typing import List,Dict
from dataclasses import dataclass

@dataclass
class DirInfo:
    name: str
    path: str


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


@dataclass
class FileInfo:
    is_file: bool
    name: str
    modify_time: float
    file_size: int


class DirContentInfo:
    def __init__(self, source_path) -> None:
        self.source_path: str = source_path
        self.dirlist: List[FileInfo] = []
        self.fileList: List[FileInfo] = []
