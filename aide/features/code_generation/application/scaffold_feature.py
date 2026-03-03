import os
from aide.core.domain.ports import FileSystemPort

class ScaffoldFeatureUseCase:
    def __init__(self, file_system: FileSystemPort) -> None:
        self.file_system = file_system

    def execute(self, feature_name: str, stack: str, output_dir: str) -> bool:
        feature_slug = feature_name.lower().replace(" ", "_").replace("-", "_")
        feature_class = "".join(word.capitalize() for word in feature_slug.split("_"))
        
        base_path = os.path.join(output_dir, feature_slug)
        
        # We need to simulate directory creation or just ensure OsFileSystem handles paths
        # OsFileSystem's write_file should create parent dirs, but let's be explicit
        
        if stack.lower() == "kotlin" or stack.lower() == "java":
            self._scaffold_kotlin(base_path, feature_slug, feature_class)
        elif stack.lower() == "python":
            self._scaffold_python(base_path, feature_slug, feature_class)
        else:
            self._scaffold_generic(base_path, feature_slug, feature_class, stack.lower())
            
        return True

    def _scaffold_kotlin(self, base_path: str, slug: str, clazz: str):
        domain_entity = f"package {slug}.domain\n\ndata class {clazz}Entity(\n    val id: String\n)\n"
        self.file_system.write_file(os.path.join(base_path, "domain", f"{clazz}Entity.kt"), domain_entity)
        
        app_use_case = f"package {slug}.application\n\nimport {slug}.domain.{clazz}Entity\n\nclass Get{clazz}UseCase {{\n    fun execute(): {clazz}Entity? {{\n        return null\n    }}\n}}\n"
        self.file_system.write_file(os.path.join(base_path, "application", f"Get{clazz}UseCase.kt"), app_use_case)
        
        infra_repo = f"package {slug}.infrastructure\n\nimport {slug}.domain.{clazz}Entity\n\nclass {clazz}RepositoryImpl {{\n    fun save(entity: {clazz}Entity) {{}}\n}}\n"
        self.file_system.write_file(os.path.join(base_path, "infrastructure", f"{clazz}RepositoryImpl.kt"), infra_repo)

    def _scaffold_python(self, base_path: str, slug: str, clazz: str):
        # Python requires __init__.py files
        self.file_system.write_file(os.path.join(base_path, "domain", "__init__.py"), "")
        self.file_system.write_file(os.path.join(base_path, "application", "__init__.py"), "")
        self.file_system.write_file(os.path.join(base_path, "infrastructure", "__init__.py"), "")
        
        domain_entity = f"from dataclasses import dataclass\n\n@dataclass\nclass {clazz}Entity:\n    id: str\n"
        self.file_system.write_file(os.path.join(base_path, "domain", "entity.py"), domain_entity)
        
        app_use_case = f"from {slug}.domain.entity import {clazz}Entity\n\nclass Get{clazz}UseCase:\n    def execute(self) -> {clazz}Entity:\n        pass\n"
        self.file_system.write_file(os.path.join(base_path, "application", "use_cases.py"), app_use_case)
        
        infra_repo = f"from {slug}.domain.entity import {clazz}Entity\n\nclass {clazz}RepositoryImpl:\n    def save(self, entity: {clazz}Entity):\n        pass\n"
        self.file_system.write_file(os.path.join(base_path, "infrastructure", "repository.py"), infra_repo)

    def _scaffold_generic(self, base_path: str, slug: str, clazz: str, stack: str):
        # Generic fallback for unsupported stacks
        ext = ".ts" if stack in ["typescript", "javascript", "ts", "js"] else (".go" if stack == "go" else ".txt")
        if stack == "rust" or stack == "rs": ext = ".rs"
        elif stack == "csharp" or stack == "cs": ext = ".cs"
        elif stack == "cpp" or stack == "c++": ext = ".cpp"
        elif stack == "scala": ext = ".scala"
        elif stack == "ruby" or stack == "rb": ext = ".rb"
        
        domain_entity = f"// Entity: {clazz}\n// ID: string\n"
        self.file_system.write_file(os.path.join(base_path, "domain", f"{clazz}Entity{ext}"), domain_entity)
        
        app_use_case = f"// UseCase: Get{clazz}\n// Returns: {clazz}Entity\n"
        self.file_system.write_file(os.path.join(base_path, "application", f"Get{clazz}UseCase{ext}"), app_use_case)
        
        infra_repo = f"// Repository: {clazz}RepositoryImpl\n// Methods: save({clazz}Entity)\n"
        self.file_system.write_file(os.path.join(base_path, "infrastructure", f"{clazz}RepositoryImpl{ext}"), infra_repo)

