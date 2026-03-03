import os
from aide.core.domain.ports import FileSystemPort


class ReadFileUseCase:
    def __init__(self, file_system: FileSystemPort):
        self.file_system = file_system

    def execute(self, file_path: str, selection: str | None = None) -> dict:
        abs_path = os.path.abspath(file_path)
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        content = self.file_system.read_file(abs_path)
        lines = content.splitlines()

        start_line = 1
        end_line = len(lines)

        if selection:
            parts = selection.split(":")
            try:
                start_line = int(parts[0])
                if len(parts) > 1:
                    end_line = int(parts[1])
            except ValueError:
                raise ValueError(
                    f"Invalid selection format: '{selection}'. Use start:end (e.g. 10:20)"
                )

        read_lines = [
            f"{i + 1}: {lines[i]}"
            for i in range(start_line - 1, end_line)
            if i < len(lines)
        ]

        return {
            "file_path": abs_path,
            "total_lines": len(lines),
            "total_bytes": len(content),
            "start_line": start_line,
            "end_line": end_line,
            "content": "\n".join(read_lines),
        }
