import json
from argparse import _SubParsersAction
from aide.core.context import Context
from aide.core.domain.ports import FileSystemPort
from aide.parsing.domain.ports import LanguageParserPort
from aide.features.architecture_audit.application.audit_kotlin import AuditKotlinUseCase
from aide.features.architecture_audit.application.audit_nextjs import AuditNextjsUseCase
from aide.features.architecture_audit.application.audit_default import AuditDefaultUseCase

class ArchitectureAuditPlugin:
    """Plugin to audit projects for context-aware architecture violations."""
    
    def register(self, subparsers: _SubParsersAction, context: Context) -> None:
        parser = subparsers.add_parser("audit", help="Audit codebase for architecture violations")
        parser.add_argument("--stack", required=True, help="Technology stack to audit (e.g. kotlin, nextjs, python, rust, go)")
        parser.add_argument("--src", default=".", help="Source root directory")
        parser.set_defaults(func=lambda args: self.run_audit(args, context))

    def run_audit(self, args, context: Context):
        # Resolve dependencies from the DI Context
        file_system = context.resolve(FileSystemPort)
        language_parser = context.resolve(LanguageParserPort)
        
        if args.stack == 'kotlin':
            use_case = AuditKotlinUseCase(file_system, language_parser)
            result = use_case.execute(args.src)
        elif args.stack == 'nextjs':
            use_case = AuditNextjsUseCase(file_system, language_parser)
            result = use_case.execute(args.src)
        else:
            use_case = AuditDefaultUseCase(file_system, language_parser)
            result = use_case.execute(args.src)
            
        print(json.dumps(result, indent=2))
