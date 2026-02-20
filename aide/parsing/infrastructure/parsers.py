import re
from typing import List
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
        
    def parse(self, content: str, file_extension: str) -> List[SymbolNode]:
        parser = self._parsers.get(file_extension, self._fallback)
        return parser.parse(content, file_extension)

    def parse_imports(self, content: str, file_extension: str) -> List[str]:
        parser = self._parsers.get(file_extension, self._fallback)
        return parser.parse_imports(content, file_extension)

class RegexLanguageParser(LanguageParserPort):
    def parse(self, content: str, file_extension: str) -> List[SymbolNode]:
        lines = content.splitlines()
        nodes = []
        
        # Simple Regex Patterns
        # Note: This is an approximation. It won't handle nested structures perfectly or multiline signatures.
        # But it's "Good Enough" for a high-level outline.
        
        patterns = []
        
        if file_extension in {'.py'}:
            patterns = [
                (r'^\s*class\s+(\w+)', 'class'),
                (r'^\s*def\s+(\w+)', 'function'),
            ]
        elif file_extension in {'.kt', '.java'}:
            patterns = [
                (r'^\s*.*class\s+(\w+)', 'class'),
                (r'^\s*.*interface\s+(\w+)', 'interface'),
                (r'^\s*.*object\s+(\w+)', 'object'),
                (r'^\s*.*fun\s+(?:[\w<>.]+\.)?(\w+)', 'function'),
                # (r'^\s*.*val\s+(\w+)', 'variable'), # Might be too noisy
            ]
        elif file_extension in {'.ts', '.tsx', '.js', '.jsx'}:
            patterns = [
                (r'^\s*(?:export\s+)?(?:abstract\s+)?class\s+(\w+)', 'class'),
                (r'^\s*(?:export\s+)?interface\s+(\w+)', 'interface'),
                (r'^\s*(?:export\s+)?type\s+(\w+)', 'type'),
                (r'^\s*(?:export\s+)?enum\s+(\w+)', 'enum'),
                # React Component (Functional, uppercase start)
                (r'^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Z]\w+)', 'component'),
                # React Hook (use...)
                (r'^\s*(?:export\s+)?(?:async\s+)?function\s+(use\w+)', 'hook'),
                # Standard Function (other)
                (r'^\s*(?:export\s+)?(?:async\s+)?function\s+([a-z]\w+)', 'function'),
                # Arrow Component (const X = ... =>)
                (r'^\s*(?:export\s+)?const\s+([A-Z]\w+)\s*=\s*(?:async\s+)?.*=>', 'component'),
                (r'^\s*(?:export\s+)?const\s+(\w+)\s*=\s*React\.memo', 'component'), 
                (r'^\s*(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?(?:<|\()', 'arrow_function'), 
            ]
            
        elif file_extension in {'.cs'}:
            patterns = [
                (r'^\s*(?:public\s+|private\s+|protected\s+|internal\s+|static\s+|sealed\s+|abstract\s+|partial\s+)*class\s+(\w+)', 'class'),
                (r'^\s*(?:public\s+|private\s+|protected\s+|internal\s+|static\s+|sealed\s+|abstract\s+|partial\s+)*interface\s+(\w+)', 'interface'),
                (r'^\s*(?:public\s+|private\s+|protected\s+|internal\s+|static\s+|sealed\s+|abstract\s+|partial\s+)*enum\s+(\w+)', 'enum'),
                (r'^\s*(?:public\s+|private\s+|protected\s+|internal\s+|static\s+|virtual\s+|override\s+|sealed\s+|abstract\s+|async\s+)*[\w<>, \[\]]+\s+(\w+)\s*\(', 'function'),
            ]
        elif file_extension in {'.rs'}:
            patterns = [
                (r'^\s*(?:pub\s+(?:\([^)]+\)\s+)?)?struct\s+(\w+)', 'struct'),
                (r'^\s*(?:pub\s+(?:\([^)]+\)\s+)?)?enum\s+(\w+)', 'enum'),
                (r'^\s*(?:pub\s+(?:\([^)]+\)\s+)?)?trait\s+(\w+)', 'trait'),
                (r'^\s*(?:pub\s+(?:\([^)]+\)\s+)?)?(?:async\s+|const\s+|unsafe\s+|extern\s+)*fn\s+(\w+)', 'function'),
                (r'^\s*(?:pub\s+(?:\([^)]+\)\s+)?)?mod\s+(\w+)', 'module'),
            ]
        elif file_extension in {'.go'}:
            patterns = [
                (r'^\s*type\s+(\w+)\s+struct', 'struct'),
                (r'^\s*type\s+(\w+)\s+interface', 'interface'),
                (r'^\s*func\s+(?:\([^)]+\)\s+)?(\w+)', 'function'),
            ]
        elif file_extension in {'.cpp', '.hpp', '.c', '.cc', '.h'}:
             patterns = [
                (r'^\s*(?:class|struct)\s+(\w+)', 'class'),
                (r'^\s*(?:virtual\s+|inline\s+|constexpr\s+|static\s+)*[a-zA-Z0-9_<>:*\s]+\s+(\w+)\s*\(', 'function'),   
             ]
        elif file_extension in {'.scala'}:
             patterns = [
                (r'^\s*(?:private\s+|protected\s+|abstract\s+|sealed\s+|final\s+|implicit\s+|lazy\s+|override\s+)*class\s+(\w+)', 'class'),
                (r'^\s*(?:private\s+|protected\s+|abstract\s+|sealed\s+|final\s+|implicit\s+|lazy\s+|override\s+)*trait\s+(\w+)', 'trait'),
                (r'^\s*(?:private\s+|protected\s+|abstract\s+|sealed\s+|final\s+|implicit\s+|lazy\s+|override\s+)*object\s+(\w+)', 'object'),
                (r'^\s*(?:private\s+|protected\s+|abstract\s+|sealed\s+|final\s+|implicit\s+|lazy\s+|override\s+)*def\s+(\w+)', 'function'),
             ]
        elif file_extension in {'.rb'}:
             patterns = [
                (r'^\s*module\s+(\w+)', 'module'),
                (r'^\s*class\s+(\w+)', 'class'),
                (r'^\s*def\s+(?:self\.)?(\w+)', 'function'),
             ]
            
        if not patterns:
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

    def parse_imports(self, content: str, file_extension: str) -> List[str]:
        imports = []
        lines = content.splitlines()
        
        # Regex for imports
        pattern = None
        
        if file_extension in {'.kt', '.java'}:
            # import com.example.Foo
            pattern = r'^\s*import\s+([\w\.]+)'
        elif file_extension in {'.py'}:
            # import foo
            # from foo import bar
            # We want 'foo' from 'import foo' or 'foo' from 'from foo import bar'
            # This is tricky with regex. Let's just grab the whole line for audit purposes or simple extraction.
            # But the contract returns List[str]. 
            # For Python audit, we might need the full import line to check "from ... import ...". 
            # But let's stick to extraction of the *module* name if possible.
            pass # TODO: Python import parsing
        elif file_extension in {'.ts', '.tsx', '.js', '.jsx'}:
            # import ... from '...'
            # import '...'
            pattern = r'^\s*import\s+(?:.*from\s+)?[\'"]([^\'"]+)[\'"]'
        elif file_extension in {'.cs'}:
            pattern = r'^\s*using\s+([\w\.]+);'
        elif file_extension in {'.rs'}:
            pattern = r'^\s*use\s+([^;]+);'
        elif file_extension in {'.go'}:
            pattern = r'^\s*(?:import\s+)?[\'"]([^\'"]+)[\'"]' # very naive go import
        elif file_extension in {'.cpp', '.hpp', '.c', '.cc', '.h'}:
            pattern = r'^\s*#include\s*[<"]([^>"]+)[>"]'
        elif file_extension in {'.scala'}:
            pattern = r'^\s*import\s+([\w\.]+)'
        elif file_extension in {'.rb'}:
            pattern = r'^\s*(?:require|require_relative|load)\s+[\'"]([^\'"]+)[\'"]'

        if not pattern and file_extension not in {'.py', '.go'}:
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
