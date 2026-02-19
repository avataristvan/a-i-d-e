import re
from typing import Dict, Any, List
import os

class AuditFixturesUseCase:
    """Scans test directory for unused or redundant pytest fixtures."""
    
    def __init__(self, file_system):
        self.file_system = file_system
        
    def execute(self, tests_dir: str, format: str = "json") -> Dict[str, Any]:
        # Very simple greedy grep for fixture definitions and usage
        
        # 1. Gather all files in tests_dir
        # Since we don't have a perfect walk file_system command here without os listdir
        # We'll just assume a flat or one-level deep structure for the fake implementation
        # Actually os.walk is fine for this standalone script.
        
        fixtures = {}
        usages = {}
        
        try:
            files = list(self.file_system.walk_files(tests_dir))
        except Exception as e:
            print(f"❌ Failed to traverse path: {e}")
            return {}

        for path in files:
            if path.endswith(".py"):
                content = self.file_system.read_file(path)
                
                # Regex for fixture def: @pytest.fixture\ndef my_fixture(
                defs = re.finditer(r'@pytest\.fixture(?:\(.*?\))?\s*def\s+([a-zA-Z0-9_]+)', content)
                for d in defs:
                    name = d.group(1)
                    if name not in fixtures:
                        fixtures[name] = []
                    fixtures[name].append(path)
                    
                # Find all test function signatures to see what they request
                # def test_something(my_fixture, other_fixture):
                tests = re.finditer(r'def\s+test_[a-zA-Z0-9_]+\s*\((.*?)\)', content)
                for t in tests:
                    args_str = t.group(1)
                    args = [a.strip() for a in args_str.split(',') if a.strip()]
                    for arg in args:
                        arg_name = arg.split(':')[0].strip() # remove type hints if any
                        if arg_name not in usages:
                            usages[arg_name] = 0
                        usages[arg_name] += 1
                            
        # Now correlate unused
        unused = []
        for fix_name, locs in fixtures.items():
            if usages.get(fix_name, 0) == 0:
                unused.append({"name": fix_name, "locations": locs})
                
        payload = {
            "total_fixtures": len(fixtures),
            "unused_fixtures": unused
        }
        
        import json
        if format == "json":
            print(json.dumps(payload, indent=2))
        else:
            print(f"📊 Audited {len(fixtures)} fixtures.")
            for fix in unused:
                print(f"⚠️ Unused fixture '{fix['name']}' in {fix['locations']}")
                
        return payload
