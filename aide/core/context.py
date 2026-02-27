from typing import Type, TypeVar, Dict, Any, Optional
from aide.core.domain.ports import FileSystemPort
from aide.parsing.domain.ports import LanguageParserPort
from aide.core.infrastructure.strategy_provider import StrategyProvider
T = TypeVar('T')

class Context:
    """Dependency Injection Container for AIDE plugins."""
    
    def __init__(self, 
                 file_system: FileSystemPort | None = None, 
                 language_parser: LanguageParserPort | None = None,
                 strategy_provider: StrategyProvider | None = None):
        
        self._services: dict[Type, Any] = {}
        
        # Backward compatibility registration for existing systems
        if file_system:
            self.register(FileSystemPort, file_system)
        if language_parser:
            self.register(LanguageParserPort, language_parser)
        if strategy_provider:
             self.register(StrategyProvider, strategy_provider)
        else:
             self.register(StrategyProvider, StrategyProvider())
             
    def register(self, interface: Type[T], implementation: T) -> None:
        """Register a dependency with the DI Container."""
        self._services[interface] = implementation
        
    def resolve(self, interface: Type[T]) -> T:
        """Resolve a dependency from the DI Container."""
        if interface not in self._services:
            raise KeyError(f"Service '{interface.__name__}' is not registered in the Context.")
        return self._services[interface]

    # --- Backward Compatibility Properties ---
    # These remain so existing plugins don't break, but future plugins
    # should use `context.resolve(MyInterface)`.
    
    @property
    def file_system(self) -> FileSystemPort:
        return self.resolve(FileSystemPort)

    @property
    def language_parser(self) -> LanguageParserPort:
        return self.resolve(LanguageParserPort)

    @property
    def strategy_provider(self) -> StrategyProvider:
        return self.resolve(StrategyProvider)
