from typing import Dict
from aide.core.domain.ports import LanguageStrategy
from aide.parsing.infrastructure.kotlin_strategy import KotlinLanguageStrategy
from aide.parsing.infrastructure.typescript_strategy import TypeScriptLanguageStrategy
from aide.parsing.infrastructure.python_strategy import PythonLanguageStrategy

class StrategyProvider:
    def __init__(self):
        self._strategies: Dict[str, LanguageStrategy] = {}
        
        # Default Strategies
        kotlin = KotlinLanguageStrategy()
        typescript = TypeScriptLanguageStrategy()
        python = PythonLanguageStrategy()
        
        self._strategies['.kt'] = kotlin
        self._strategies['.java'] = kotlin 
        self._strategies['.ts'] = typescript
        self._strategies['.tsx'] = typescript
        self._strategies['.js'] = typescript
        self._strategies['.jsx'] = typescript
        self._strategies['.py'] = python

    def get_strategy(self, file_path: str) -> LanguageStrategy:
        import os
        ext = os.path.splitext(file_path)[1]
        strategy = self._strategies.get(ext)
        if not strategy:
            # Fallback to Kotlin (existing behavior) or a generic one?
            # For now, let's stick to Kotlin as fallback to avoid breaking current flow
            return self._strategies['.kt']
        return strategy
