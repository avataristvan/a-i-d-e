import os
import json
from typing import List
from aide.core.domain.ports import FileSystemPort
from aide.parsing.domain.ports import LanguageParserPort

class BriefingService:
    def __init__(self, file_system: FileSystemPort, language_parser: LanguageParserPort):
        self.file_system = file_system
        self.language_parser = language_parser

    def get_persona_rules(self) -> str:
        """Loads persona rules hierarchical: AIDE_RULES_PATH -> workflows/use-aide-tool.md -> Default."""
        rules_path = os.getenv("AIDE_RULES_PATH")
        if not rules_path:
            local_path = "workflows/use-aide-tool.md"
            if self.file_system.path_exists(local_path):
                rules_path = local_path
        
        if rules_path:
            try:
                return self.file_system.read_file(rules_path).strip()
            except:
                pass
                
        return "Follow the provided context and instructions strictly to generate functional code."

    def _find_closest_file(self, target_file_path: str, filename: str) -> str:
        if not target_file_path:
            return filename if self.file_system.path_exists(filename) else None
            
        current_dir = os.path.dirname(target_file_path) if not self.file_system.path_exists(target_file_path) or not os.path.isdir(target_file_path) else target_file_path
        
        while True:
            check_path = os.path.join(current_dir, filename) if current_dir else filename
            if check_path.startswith("./"):
                check_path = check_path[2:]
                
            if self.file_system.path_exists(check_path):
                return check_path
                
            if not current_dir or current_dir == "." or current_dir == "/":
                # Final check at bare root
                if current_dir != "":
                    if self.file_system.path_exists(filename):
                        return filename
                break
                
            new_dir = os.path.dirname(current_dir)
            if new_dir == current_dir:
                break
            current_dir = new_dir
            
        return None

    def get_dependency_context(self, target_file_path: str = None) -> str:
        """Collects dependency information from closest common files like package.json."""
        context = []
        
        # 1. NPM
        npm_file = self._find_closest_file(target_file_path, "package.json")
        if npm_file:
            try:
                content = json.loads(self.file_system.read_file(npm_file))
                deps = content.get("dependencies", {})
                if deps:
                    context.append(f"NPM Dependencies ({npm_file}): {json.dumps(deps)}")
            except:
                pass
                
        # 2. Python
        req_file = self._find_closest_file(target_file_path, "requirements.txt")
        if req_file:
            try:
                context.append(f"Python Requirements ({req_file}):\n{self.file_system.read_file(req_file)}")
            except:
                pass
        
        pyext_file = self._find_closest_file(target_file_path, "pyproject.toml")
        if pyext_file:
            try:
                context.append(f"Python Project Config ({pyext_file}):\n{self.file_system.read_file(pyext_file)}")
            except:
                pass
                
        # 3. Gradle
        gradle_files = ["build.gradle", "build.gradle.kts", "app/build.gradle", "app/build.gradle.kts"]
        for gf in gradle_files:
            g_file = self._find_closest_file(target_file_path, gf)
            if g_file:
                try:
                    content = self.file_system.read_file(g_file)
                    context.append(f"Gradle File ({g_file}):\n{content[:2000]}")
                except:
                    pass

        # 4. Version Catalog
        toml_path = self._find_closest_file(target_file_path, "gradle/libs.versions.toml")
        if toml_path:
            try:
                context.append(f"Gradle Version Catalog ({toml_path}):\n{self.file_system.read_file(toml_path)}")
            except:
                pass
                
        return "\n".join(context) if context else "No specific dependency information found nearby."

    def get_symbol_map(self, file_path: str, content: str) -> str:
        """Generates an outline of the target file."""
        try:
            _, ext = os.path.splitext(file_path)
            symbols = self.language_parser.parse(content, ext)
            if not symbols:
                return "File structure could not be parsed."
                
            outline = []
            for symbol in symbols:
                outline.append(f"- {symbol.kind}: {symbol.name}")
                if symbol.children:
                    for child in symbol.children:
                        outline.append(f"  - {child.kind}: {child.name}")
                
            return "\n".join(outline)
        except Exception as e:
            return f"Error extracting symbol map: {e}"
