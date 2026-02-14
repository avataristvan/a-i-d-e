from typing import Dict
from aide.core.domain.ports import LanguageStrategy
from aide.parsing.infrastructure.kotlin_strategy import KotlinLanguageStrategy
from aide.parsing.infrastructure.typescript_strategy import TypeScriptLanguageStrategy
from aide.parsing.infrastructure.python_strategy import PythonLanguageStrategy
from aide.parsing.infrastructure.csharp_strategy import CSharpLanguageStrategy
from aide.parsing.infrastructure.rust_strategy import RustLanguageStrategy
from aide.parsing.infrastructure.go_strategy import GoLanguageStrategy
from aide.parsing.infrastructure.cpp_strategy import CppLanguageStrategy
from aide.parsing.infrastructure.scala_strategy import ScalaLanguageStrategy
from aide.parsing.infrastructure.ruby_strategy import RubyLanguageStrategy

class StrategyProvider:
    def __init__(self):
        self._strategies: Dict[str, LanguageStrategy] = {}
        
        # Default Strategies
        kotlin = KotlinLanguageStrategy()
        typescript = TypeScriptLanguageStrategy()
        python = PythonLanguageStrategy()
        csharp = CSharpLanguageStrategy()
        rust = RustLanguageStrategy()
        go = GoLanguageStrategy()
        cpp = CppLanguageStrategy()
        scala = ScalaLanguageStrategy()
        ruby = RubyLanguageStrategy()
        
        self._strategies['.kt'] = kotlin
        self._strategies['.java'] = kotlin 
        self._strategies['.ts'] = typescript
        self._strategies['.tsx'] = typescript
        self._strategies['.js'] = typescript
        self._strategies['.jsx'] = typescript
        self._strategies['.py'] = python
        self._strategies['.cs'] = csharp
        self._strategies['.rs'] = rust
        self._strategies['.go'] = go
        self._strategies['.cpp'] = cpp
        self._strategies['.hpp'] = cpp
        self._strategies['.cc'] = cpp
        self._strategies['.h'] = cpp
        self._strategies['.scala'] = scala
        self._strategies['.rb'] = ruby

    def get_strategy(self, file_path: str) -> LanguageStrategy:
        import os
        ext = os.path.splitext(file_path)[1]
        strategy = self._strategies.get(ext)
        if not strategy:
            # Fallback to Kotlin (existing behavior) or a generic one?
            # For now, let's stick to Kotlin as fallback to avoid breaking current flow
            return self._strategies['.kt']
        return strategy
