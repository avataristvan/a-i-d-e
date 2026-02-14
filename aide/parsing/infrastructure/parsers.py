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
