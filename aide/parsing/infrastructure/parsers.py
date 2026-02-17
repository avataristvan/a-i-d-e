import re
from typing import List
from aide.parsing.domain.ports import LanguageParserPort
from aide.parsing.domain.models import SymbolNode

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

        if not pattern and file_extension not in {'.py'}:
             return []

        for line in lines:
            if file_extension in {'.kt', '.java', '.ts', '.tsx', '.js', '.jsx'}:
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
                     
        return imports
