import os
import shutil
from typing import Generator
from aide.core.domain.ports import FileSystemPort

class SecurityError(Exception):
    pass

class OsFileSystem(FileSystemPort):
    def __init__(self, jailed_root: str = None):
        # Default to the current working directory if no jail is provided
        self.jailed_root = os.path.abspath(jailed_root) if jailed_root else os.path.abspath(os.getcwd())

    def _secure_path(self, path: str) -> str:
        """Resolves the path and ensures it does not escape the jailed root."""
        resolved = os.path.abspath(path)
        if not resolved.startswith(self.jailed_root):
            raise SecurityError(f"AIDE Security: Path traversal prevented. Attempted to access '{resolved}' outside of jailed root '{self.jailed_root}'.")
        return resolved
    def walk_files(self, root_path: str) -> Generator[str, None, None]:
        safe_root = self._secure_path(root_path)
        if os.path.isfile(safe_root):
            yield safe_root
            return

        for root, dirs, files in os.walk(safe_root):
            ignores = {".git", "__pycache__", "node_modules", ".next", "build", ".gradle", ".idea", "bin", "obj"}
            # Use list(dirs) to avoid issues with modification during iteration
            for d in list(dirs):
                if d in ignores:
                    dirs.remove(d)
                
            for file in files:
                yield os.path.abspath(os.path.join(root, file))

    def read_file(self, file_path: str) -> str:
        safe_path = self._secure_path(file_path)
        with open(safe_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    def write_file(self, file_path: str, content: str) -> None:
        safe_path = self._secure_path(file_path)
        with open(safe_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def move_path(self, src: str, dst: str) -> None:
        safe_src = self._secure_path(src)
        safe_dst = self._secure_path(dst)
        # Ensure destination parent directory exists
        os.makedirs(os.path.dirname(safe_dst), exist_ok=True)
        shutil.move(safe_src, safe_dst)

    def delete_path(self, path: str) -> None:
        safe_path = self._secure_path(path)
        if os.path.isfile(safe_path):
            os.remove(safe_path)
        elif os.path.isdir(safe_path):
            shutil.rmtree(safe_path)
