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
        self._in_transaction = False
        self._backups = {} # path -> original content (str) or None if it didn't exist
        self._moved_dirs = [] # list of (src, dst)
        self._created_dirs = set() # directories created during transaction

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

    def path_exists(self, path: str) -> bool:
        try:
            safe_path = self._secure_path(path)
            return os.path.exists(safe_path)
        except SecurityError:
            return False

    def read_file(self, file_path: str) -> str:
        safe_path = self._secure_path(file_path)
        with open(safe_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    def write_file(self, file_path: str, content: str) -> None:
        safe_path = self._secure_path(file_path)
        
        if self._in_transaction and safe_path not in self._backups:
            if os.path.exists(safe_path):
                with open(safe_path, 'r', encoding='utf-8', errors='ignore') as f:
                    self._backups[safe_path] = f.read()
            else:
                self._backups[safe_path] = None
                # Track newly created directories to clean them up on rollback
                parent = os.path.dirname(safe_path)
                if not os.path.exists(parent):
                    self._track_created_dirs(parent)
                
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        with open(safe_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _track_created_dirs(self, dir_path: str):
        safe_dir = self._secure_path(dir_path)
        current = safe_dir
        while current != self.jailed_root and not os.path.exists(current):
            self._created_dirs.add(current)
            current = os.path.dirname(current)

    def move_path(self, src: str, dst: str) -> None:
        safe_src = self._secure_path(src)
        safe_dst = self._secure_path(dst)
        
        if self._in_transaction:
            if os.path.isdir(safe_src):
                self._moved_dirs.append((safe_src, safe_dst))
            else:
                if safe_dst not in self._backups:
                    self._backups[safe_dst] = None if not os.path.exists(safe_dst) else self.read_file(safe_dst)
                if safe_src not in self._backups:
                    self._backups[safe_src] = self.read_file(safe_src)
                    
        parent = os.path.dirname(safe_dst)
        if self._in_transaction and not os.path.exists(parent):
            self._track_created_dirs(parent)
            
        # Ensure destination parent directory exists
        os.makedirs(parent, exist_ok=True)
        
        # If destination exists and is a directory, and source is a directory,
        # shutil.move(src, dst) will move src INTO dst (nesting).
        # We want to RENAME/MOVE TO dst, not into it.
        if os.path.isdir(safe_src) and os.path.exists(safe_dst) and os.path.isdir(safe_dst):
             # If destination exists, we merge contents
             for item in os.listdir(safe_src):
                 self.move_path(os.path.join(safe_src, item), os.path.join(safe_dst, item))
             os.rmdir(safe_src)
        else:
             shutil.move(safe_src, safe_dst)

    def delete_path(self, path: str) -> None:
        safe_path = self._secure_path(path)
        
        if self._in_transaction:
            if os.path.isdir(safe_path):
                # For directories, tracking every file is too expensive, 
                # but AIDE mostly deletes individual files.
                # If needed, we could copytree to a temp dir.
                raise NotImplementedError("Directory deletion rollback not yet supported.")
            else:
                if safe_path not in self._backups and os.path.exists(safe_path):
                    self._backups[safe_path] = self.read_file(safe_path)
                    
        if os.path.isfile(safe_path):
            os.remove(safe_path)
        elif os.path.isdir(safe_path):
            shutil.rmtree(safe_path)

    def delete_empty_parents(self, path: str, root_limit: str) -> None:
        safe_path = self._secure_path(path)
        safe_limit = self._secure_path(root_limit)
        
        current = os.path.dirname(safe_path)
        while current.startswith(safe_limit) and current != safe_limit:
            if os.path.exists(current) and os.path.isdir(current) and not os.listdir(current):
                os.rmdir(current)
                current = os.path.dirname(current)
            else:
                break

    def start_transaction(self) -> None:
        self._in_transaction = True
        self._backups.clear()
        self._moved_dirs.clear()
        self._created_dirs.clear()

    def commit(self) -> None:
        self._in_transaction = False
        self._backups.clear()
        self._moved_dirs.clear()
        self._created_dirs.clear()

    def rollback(self) -> None:
        if not self._in_transaction:
            return

        # 1. Reverse directory moves
        for src, dst in reversed(self._moved_dirs):
            if os.path.exists(dst):
                shutil.move(dst, src)

        # 2. Restore files (or delete if they were newly created)
        for path, content in self._backups.items():
            if content is None:
                if os.path.exists(path):
                    os.remove(path)
            else:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)

        # 3. Cleanup created empty directories
        # Sort descending by length to delete deepest first
        for dir_path in sorted(list(self._created_dirs), key=len, reverse=True):
            if os.path.exists(dir_path) and not os.listdir(dir_path):
                try:
                    os.rmdir(dir_path)
                except OSError:
                    pass

        self.commit()
