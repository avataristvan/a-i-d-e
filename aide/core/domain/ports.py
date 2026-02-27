from abc import ABC, abstractmethod
from typing import Any, Tuple, Callable, Generator

class FileSystemPort(ABC):
    @abstractmethod
    def walk_files(self, root_path: str) -> Generator[str, None, None]:
        """Yields absolute file paths recursively."""
        pass

    @abstractmethod
    def path_exists(self, path: str) -> bool:
        """Checks if a path exists and is within the jail."""
        pass

    @abstractmethod
    def read_file(self, file_path: str) -> str:
        """Reads file content."""
        pass

    @abstractmethod
    def write_file(self, file_path: str, content: str) -> None:
        """Writes content to file."""
        pass

    @abstractmethod
    def move_path(self, src: str, dst: str) -> None:
        """Moves a file or directory."""
        pass

    @abstractmethod
    def delete_path(self, path: str) -> None:
        """Deletes a file or directory."""
        pass

    @abstractmethod
    def delete_empty_parents(self, path: str, root_limit: str) -> None:
        """Recursively deletes empty parent directories up to a limit."""
        pass

    @abstractmethod
    def start_transaction(self) -> None:
        """Starts tracking file system changes for a potential rollback."""
        pass

    @abstractmethod
    def commit(self) -> None:
        """Commits the tracked file system changes, clearing the transaction history."""
        pass

    @abstractmethod
    def rollback(self) -> None:
        """Reverts all file system changes made since the transaction started."""
        pass

class LanguageStrategy(ABC):
    @abstractmethod
    def extract_imports_and_header(self, lines: list[str]) -> tuple[list[str], str | None]:
        """Returns list of imports and the package/header declaration (e.g. 'package ...')."""
        pass

    @abstractmethod
    def get_package_header(self, file_path: str) -> str | None:
        """Returns the package/header line for a new file based on its path."""
        pass

    @abstractmethod
    def get_module_path(self, file_path: str) -> str:
        """Returns the logical module path (for updates/imports) from a file path."""
        pass

    @abstractmethod
    def adjust_visibility(self, content: str) -> str:
        """Adjusts visibility of moved symbols (e.g. removing private)."""
        pass

    @abstractmethod
    def find_symbol_range(self, lines: list[str], symbol: str) -> tuple[int | None, int | None]:
        """Finds start and end line of a symbol (1-based)."""
        pass

    @abstractmethod
    def get_import_statement(self, package: str, symbol: str) -> str:
        """Returns the appropriate import statement for a symbol."""
        pass

    @abstractmethod
    def find_variables(self, text: str) -> set[str]:
        """Finds potential variable identifiers in text block."""
        pass

    @abstractmethod
    def is_defined_in_outer_scope(self, var_name: str, context_text: str) -> bool:
        """Checks if a variable is defined in the outer scope."""
        pass

    @abstractmethod
    def infer_types(self, parameters: list[str], context_text: str) -> list[tuple[str, str]]:
        """Infers types for a list of variables from context."""
        pass

    @abstractmethod
    def get_function_template(self, name: str, params_str: str, body: list[str], scope: str, indent: str) -> str:
        """Generates a function definition template."""
        pass

    @abstractmethod
    def get_function_call(self, name: str, args_str: str, indent: str) -> str:
        """Generates a function call statement."""
        pass

    @abstractmethod
    def is_definition(self, line: str, symbol: str) -> bool:
        """Checks if a line contains the definition of a symbol."""
        pass

    @abstractmethod
    def update_signature_string(self, line: str, symbol: str, is_definition: bool, insertion: str) -> str:
        """Updates a signature/call string by inserting a parameter/value."""
        pass
