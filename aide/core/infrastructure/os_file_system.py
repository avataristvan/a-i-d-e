import os
import shutil
from typing import Generator
from aide.core.domain.ports import FileSystemPort

class OsFileSystem(FileSystemPort):
    def walk_files(self, root_path: str) -> Generator[str, None, None]:
        for root, dirs, files in os.walk(root_path):
            ignores = {".git", "__pycache__", "node_modules", ".next", "build", ".gradle", ".idea", "bin", "obj"}
            # Use list(dirs) to avoid issues with modification during iteration
            for d in list(dirs):
                if d in ignores:
                    dirs.remove(d)
                
            for file in files:
                yield os.path.abspath(os.path.join(root, file))

    def read_file(self, file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    def write_file(self, file_path: str, content: str) -> None:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def move_path(self, src: str, dst: str) -> None:
        # Ensure destination parent directory exists
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(src, dst)

    def delete_path(self, path: str) -> None:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
