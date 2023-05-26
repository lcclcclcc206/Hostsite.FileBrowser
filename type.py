from typing import List
from dataclasses import dataclass

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