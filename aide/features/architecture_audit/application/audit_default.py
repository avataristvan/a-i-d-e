from aide.core.domain.ports import FileSystemPort
from aide.parsing.domain.ports import LanguageParserPort
import os

class AuditDefaultUseCase:
    """Basic structural audit for unsupported stacks"""
    
    def __init__(self, file_system: FileSystemPort, language_parser: LanguageParserPort):
        self.file_system = file_system
        self.parser = language_parser

    def execute(self, src_root: str) -> dict:
        domain_found = False
        app_found = False
        infra_found = False
        
        for root, dirs, files in os.walk(src_root):
            if 'domain' in dirs: domain_found = True
            if 'application' in dirs: app_found = True
            if 'infrastructure' in dirs: infra_found = True
            
        success = domain_found or app_found or infra_found
        message = "Basic Clean Architecture structure detected." if success else "No Clean Architecture layers detected (domain/application/infrastructure)."
        
        return {
            "success": success,
            "message": message,
            "data": {
                "domain_layer_found": domain_found,
                "application_layer_found": app_found,
                "infrastructure_layer_found": infra_found,
                "notice": "Stack-specific boundary rules are limited for this language."
            }
        }
