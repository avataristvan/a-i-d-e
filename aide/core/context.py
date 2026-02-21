from typing import Type, TypeVar, Dict, Any, Optional
from aide.core.domain.ports import FileSystemPort, LlmProvider
from aide.parsing.domain.ports import LanguageParserPort
from aide.core.infrastructure.strategy_provider import StrategyProvider
from aide.core.infrastructure.briefing_service import BriefingService

T = TypeVar('T')

class Context:
    """Dependency Injection Container for AIDE plugins."""
    
    def __init__(self, 
                 file_system: Optional[FileSystemPort] = None, 
                 language_parser: Optional[LanguageParserPort] = None,
                 strategy_provider: Optional[StrategyProvider] = None,
                 llm_provider: Optional[LlmProvider] = None,
                 briefing_service: Optional[BriefingService] = None):
        
        self._services: Dict[Type, Any] = {}
        
        # Backward compatibility registration for existing systems
        if file_system:
            self.register(FileSystemPort, file_system)
        if language_parser:
            self.register(LanguageParserPort, language_parser)
        if strategy_provider:
             self.register(StrategyProvider, strategy_provider)
        else:
             self.register(StrategyProvider, StrategyProvider())
        if llm_provider:
             self.register(LlmProvider, llm_provider)
        if briefing_service:
             self.register(BriefingService, briefing_service)
             
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

    @property
    def llm_provider(self) -> LlmProvider:
        return self.resolve(LlmProvider)

    @property
    def briefing_service(self) -> BriefingService:
        return self.resolve(BriefingService)
