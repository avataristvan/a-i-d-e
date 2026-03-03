import os
import re

class ProjectDtoUseCase:
    def __init__(self, file_system, language_parser, strategy_provider):
        self.file_system = file_system
        self.language_parser = language_parser
        self.strategy_provider = strategy_provider

    def execute(self, source_file: str, entity_name: str, target_file: str, dto_name: str, stack: str) -> bool:
        content = self.file_system.read_file(source_file)
        lines = content.splitlines()
        
        strategy = self.strategy_provider.get_strategy(source_file)
        
        # Find the entity class bounds
        start, end = strategy.find_symbol_range(lines, entity_name)
        if not start:
            return False

        entity_body = "\n".join(lines[start-1:end])
        
        # Extract fields
        fields = self._extract_fields(entity_body, stack)
        if not fields:
            return False
            
        # Generate DTO content
        dto_content = self._generate_dto(dto_name, fields, stack, entity_name)
        
        self.file_system.write_file(target_file, dto_content)
        return True


    def _extract_fields(self, body: str, stack: str):
        fields = []
        if stack == "python":
            # Matches: id: str,   name: str | None = None
            matches = re.finditer(r'^\s*([a-zA-Z0-9_]+)\s*:\s*([^=&#\n]+)', body, re.MULTILINE)
            for m in matches:
                name = m.group(1).strip()
                typ = m.group(2).strip()
                fields.append((name, typ))
        elif stack == "kotlin" or stack == "java":
            # Matches: val id: String, var name: String? = null
            matches = re.finditer(r'(?:val|var|private|public|protected)?\s*([a-zA-Z0-9_]+)\s*:\s*([^=,\n\)]+)', body)
            for m in matches:
                name = m.group(1).strip()
                typ = m.group(2).strip()
                if name not in ("class", "fun"):
                    fields.append((name, typ))
        else:
            # Generic fallback: tries to find Word: Type or Word Type
            matches = re.finditer(r'\b([a-zA-Z0-9_]+)\s*[:\s]\s*([A-Z][a-zA-Z0-9_<>\[\]]+)\b', body)
            for m in matches:
                name = m.group(1).strip()
                typ = m.group(2).strip()
                if name.lower() not in ("class", "struct", "interface", "fun", "function", "def", "public", "private"):
                    fields.append((name, typ))
            
        return fields

    def _generate_dto(self, dto_name: str, fields: list, stack: str, entity_name: str) -> str:
        if stack == "python":
            lines = [
                "from dataclasses import dataclass",
                "",
                "@dataclass",
                f"class {dto_name}:"
            ]
            for name, typ in fields:
                lines.append(f"    {name}: {typ}")
                
            lines.append("")
            lines.append("    @classmethod")
            lines.append(f"    def from_entity(cls, entity):")
            lines.append(f"        return cls(")
            for i, (name, _) in enumerate(fields):
                comma = "," if i < len(fields) - 1 else ""
                lines.append(f"            {name}=entity.{name}{comma}")
            lines.append(f"        )")
            
            return "\n".join(lines) + "\n"
            
        elif stack == "kotlin" or stack == "java":
            lines = [
                f"data class {dto_name}("
            ]
            for i, (name, typ) in enumerate(fields):
                comma = "," if i < len(fields) - 1 else ""
                lines.append(f"    val {name}: {typ}{comma}")
            lines.append(")")
            lines.append("")
            
            lines.append(f"fun {entity_name}.to{dto_name}() = {dto_name}(")
            for i, (name, _) in enumerate(fields):
                comma = "," if i < len(fields) - 1 else ""
                lines.append(f"    {name} = this.{name}{comma}")
            lines.append(")")
            
            return "\n".join(lines) + "\n"
            
        else:
            # Generic fallback
            lines = [
                f"// DTO: {dto_name}"
            ]
            for name, typ in fields:
                lines.append(f"// {name}: {typ}")
            lines.append("")
            lines.append(f"// TODO: Implement {dto_name} mapping for {entity_name}")
            return "\n".join(lines) + "\n"
        
        return ""
