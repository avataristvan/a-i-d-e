import re
from typing import Any, Tuple, Callable, Generator
from aide.parsing.domain.ports import LanguageParserPort
from aide.parsing.domain.models import SymbolNode

class CompositeLanguageParser(LanguageParserPort):
    """Routes parsing requests to specialized AST parsers based on file extension, 
    falling back to RegexLanguageParser if no specific grammar engine exists yet."""
    
    def __init__(self, fallback_parser: LanguageParserPort):
        self._parsers = {}
        self._fallback = fallback_parser
        
    def register(self, extension: str, parser: LanguageParserPort):
        self._parsers[extension] = parser
        
    def parse(self, content: str, file_extension: str) -> list[SymbolNode]:
        parser = self._parsers.get(file_extension, self._fallback)
        return parser.parse(content, file_extension)

    def parse_imports(self, content: str, file_extension: str) -> list[str]:
        parser = self._parsers.get(file_extension, self._fallback)
        return parser.parse_imports(content, file_extension)

class RegexLanguageParser(LanguageParserPort):
    def parse(self, content: str, file_extension: str) -> list[SymbolNode]:
        lines = content.splitlines()
        nodes = []
        
        # Simple Regex Patterns
        # Note: This is an approximation. It won't handle nested structures perfectly or multiline signatures.
        # But it's "Good Enough" for a high-level outline.
        
        patterns = []
        
        match file_extension:
            case '.py':
                patterns = [
                    (r'^\s*class\s+(\w+)', 'class'),
                    (r'^\s*def\s+(\w+)', 'function'),
                ]
            case '.kt' | '.java':
                patterns = [
                    (r'^\s*.*class\s+(\w+)', 'class'),
                    (r'^\s*.*interface\s+(\w+)', 'interface'),
                    (r'^\s*.*object\s+(\w+)', 'object'),
                    (r'^\s*.*fun\s+(?:[\w<>.]+\.)?(\w+)', 'function'),
                ]
            case '.ts' | '.tsx' | '.js' | '.jsx':
                patterns = [
                    (r'^\s*(?:export\s+)?(?:abstract\s+)?class\s+(\w+)', 'class'),
                    (r'^\s*(?:export\s+)?interface\s+(\w+)', 'interface'),
                    (r'^\s*(?:export\s+)?type\s+(\w+)', 'type'),
                    (r'^\s*(?:export\s+)?enum\s+(\w+)', 'enum'),
                    (r'^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Z]\w+)', 'component'),
                    (r'^\s*(?:export\s+)?(?:async\s+)?function\s+(use\w+)', 'hook'),
                    (r'^\s*(?:export\s+)?(?:async\s+)?function\s+([a-z]\w+)', 'function'),
                    (r'^\s*(?:export\s+)?const\s+([A-Z]\w+)\s*=\s*(?:async\s+)?.*=>', 'component'),
                    (r'^\s*(?:export\s+)?const\s+(\w+)\s*=\s*React\.memo', 'component'), 
                    (r'^\s*(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?(?:<|\()', 'arrow_function'), 
                ]
            case '.cs':
                patterns = [
                    (r'^\s*(?:public\s+|private\s+|protected\s+|internal\s+|static\s+|sealed\s+|abstract\s+|partial\s+)*class\s+(\w+)', 'class'),
                    (r'^\s*(?:public\s+|private\s+|protected\s+|internal\s+|static\s+|sealed\s+|abstract\s+|partial\s+)*interface\s+(\w+)', 'interface'),
                    (r'^\s*(?:public\s+|private\s+|protected\s+|internal\s+|static\s+|sealed\s+|abstract\s+|partial\s+)*enum\s+(\w+)', 'enum'),
                    (r'^\s*(?:public\s+|private\s+|protected\s+|internal\s+|static\s+|virtual\s+|override\s+|sealed\s+|abstract\s+|async\s+)*[\w<>, \[\]]+\s+(\w+)\s*\(', 'function'),
                ]
            case '.rs':
                patterns = [
                    (r'^\s*(?:pub\s+(?:\([^)]+\)\s+)?)?struct\s+(\w+)', 'struct'),
                    (r'^\s*(?:pub\s+(?:\([^)]+\)\s+)?)?enum\s+(\w+)', 'enum'),
                    (r'^\s*(?:pub\s+(?:\([^)]+\)\s+)?)?trait\s+(\w+)', 'trait'),
                    (r'^\s*(?:pub\s+(?:\([^)]+\)\s+)?)?(?:async\s+|const\s+|unsafe\s+|extern\s+)*fn\s+(\w+)', 'function'),
                    (r'^\s*(?:pub\s+(?:\([^)]+\)\s+)?)?mod\s+(\w+)', 'module'),
                ]
            case '.go':
                patterns = [
                    (r'^\s*type\s+(\w+)\s+struct', 'struct'),
                    (r'^\s*type\s+(\w+)\s+interface', 'interface'),
                    (r'^\s*func\s+(?:\([^)]+\)\s+)?(\w+)', 'function'),
                ]
            case '.cpp' | '.hpp' | '.c' | '.cc' | '.h':
                 patterns = [
                    (r'^\s*(?:class|struct)\s+(\w+)', 'class'),
                    (r'^\s*(?:virtual\s+|inline\s+|constexpr\s+|static\s+)*[a-zA-Z0-9_<>:*\s]+\s+(\w+)\s*\(', 'function'),   
                 ]
            case '.scala':
                 patterns = [
                    (r'^\s*(?:private\s+|protected\s+|abstract\s+|sealed\s+|final\s+|implicit\s+|lazy\s+|override\s+)*class\s+(\w+)', 'class'),
                    (r'^\s*(?:private\s+|protected\s+|abstract\s+|sealed\s+|final\s+|implicit\s+|lazy\s+|override\s+)*trait\s+(\w+)', 'trait'),
                    (r'^\s*(?:private\s+|protected\s+|abstract\s+|sealed\s+|final\s+|implicit\s+|lazy\s+|override\s+)*object\s+(\w+)', 'object'),
                    (r'^\s*(?:private\s+|protected\s+|abstract\s+|sealed\s+|final\s+|implicit\s+|lazy\s+|override\s+)*def\s+(\w+)', 'function'),
                 ]
            case '.rb':
                 patterns = [
                    (r'^\s*module\s+(\w+)', 'module'),
                    (r'^\s*class\s+(\w+)', 'class'),
                    (r'^\s*def\s+(?:self\.)?(\w+)', 'function'),
                 ]
            case _:
                return []

        for i, line in enumerate(lines):
            line_num = i + 1
            for pattern, kind in patterns:
                match = re.search(pattern, line)
                if match:
                    name = match.group(1)
                    # We rely on indentation to guess hierarchy in a simple way? 
                    # For now, let's just return a flat list of important symbols. 
                    # Real parsing is hard without a grammar.
                    nodes.append(SymbolNode(name=name, kind=kind, line_number=line_num, children=[]))
                    break # Match only one pattern per line
                    
        return nodes

    def parse_imports(self, content: str, file_extension: str) -> list[str]:
        imports = []
        lines = content.splitlines()
        
        # Regex for imports
        pattern = None
        
        match file_extension:
            case '.kt' | '.java':
                pattern = r'^\s*import\s+([\w\.]+)'
            case '.py':
                pass # TODO: Python import parsing
            case '.ts' | '.tsx' | '.js' | '.jsx':
                pattern = r'^\s*import\s+(?:.*from\s+)?[\'"]([^\'"]+)[\'"]'
            case '.cs':
                pattern = r'^\s*using\s+([\w\.]+);'
            case '.rs':
                pattern = r'^\s*use\s+([^;]+);'
            case '.go':
                pattern = r'^\s*(?:import\s+)?[\'"]([^\'"]+)[\'"]'
            case '.cpp' | '.hpp' | '.c' | '.cc' | '.h':
                pattern = r'^\s*#include\s*[<"]([^>"]+)[>"]'
            case '.scala':
                pattern = r'^\s*import\s+([\w\.]+)'
            case '.rb':
                pattern = r'^\s*(?:require|require_relative|load)\s+[\'"]([^\'"]+)[\'"]'
            case _:
                return []

        for line in lines:
            if file_extension in {'.kt', '.java', '.ts', '.tsx', '.js', '.jsx', '.cs', '.rs', '.cpp', '.hpp', '.c', '.cc', '.h', '.scala', '.rb'}:
                match = re.search(pattern, line)
                if match:
                    imports.append(match.group(1))
            elif file_extension == '.py':
                 # Simple Python logic (fallback)
                 line = line.strip()
                 if line.startswith("import "):
                     parts = line.split(" ")
                     if len(parts) > 1: imports.append(parts[1])
                 elif line.startswith("from "):
                     parts = line.split(" ")
                     if len(parts) > 1: imports.append(parts[1])
            elif file_extension == '.go':
                 # Very naive go logic to handle multi-line imports
                 line = line.strip()
                 match = re.search(pattern, line)
                 if match:
                     imports.append(match.group(1))
                     
        return imports
