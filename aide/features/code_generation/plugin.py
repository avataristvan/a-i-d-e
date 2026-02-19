from argparse import _SubParsersAction
from aide.core.context import Context
from aide.features.code_generation.application.scaffold_feature import ScaffoldFeatureUseCase
from aide.features.code_generation.application.implement_interface import ImplementInterfaceUseCase
from aide.features.code_generation.application.register_dependency import RegisterDependencyUseCase
from aide.features.code_generation.application.project_dto import ProjectDtoUseCase

class CodeGenerationPlugin:
    def register(self, subparsers: _SubParsersAction, context: Context) -> None:
        parser = subparsers.add_parser("scaffold-feature", help="Scaffold Context-Aware Architecture for a new feature")
        parser.add_argument("--name", required=True, help="Name of the feature (e.g. UserProfile)")
        parser.add_argument("--stack", required=True, choices=["kotlin", "python"], help="Target tech stack")
        parser.add_argument("--output-dir", default="./src", help="Directory to scaffold into")
        parser.set_defaults(func=lambda args: self.run_scaffold(args, context))

        impl_parser = subparsers.add_parser("implement-interface", help="Deterministically inject missing interface methods into a concrete class")
        impl_parser.add_argument("--file", required=True, help="Path to the file containing the class and interface")
        impl_parser.add_argument("--class-name", required=True, help="Name of the concrete class (e.g. MyRepo)")
        impl_parser.add_argument("--implements", required=True, help="Name of the interface to implement (e.g. IRepository)")
        impl_parser.set_defaults(func=lambda args: self.run_implement(args, context))

        reg_parser = subparsers.add_parser("register-dependency", help="Deterministically inject a DI binding and import into a container")
        reg_parser.add_argument("--file", required=True, help="Path to the DI registry file")
        reg_parser.add_argument("--import-path", required=True, help="The full import path (e.g. com.example.UserEngine)")
        reg_parser.add_argument("--binding", required=True, help="The exact binding code to inject")
        reg_parser.set_defaults(func=lambda args: self.run_register(args, context))

        proj_parser = subparsers.add_parser("project-dto", help="Deterministically generate a DTO and mapping function from a Domain Entity")
        proj_parser.add_argument("--source-file", required=True, help="Path to the Domain Entity file")
        proj_parser.add_argument("--entity", required=True, help="Name of the source Entity class")
        proj_parser.add_argument("--target-file", required=True, help="Path to write the new DTO file")
        proj_parser.add_argument("--dto", required=True, help="Name of the output DTO class")
        proj_parser.add_argument("--stack", required=True, choices=["kotlin", "python"], help="Target tech stack")
        proj_parser.set_defaults(func=lambda args: self.run_project(args, context))

    def run_scaffold(self, args, context: Context):
        print(f"🏗️  Scaffolding {args.name} feature for {args.stack}...")
        
        use_case = ScaffoldFeatureUseCase(context.file_system)
        success = use_case.execute(args.name, args.stack, args.output_dir)
        
        if success:
            slug = args.name.lower().replace(" ", "_").replace("-", "_")
            print(f"✅ Generated Clean Architecture feature module at {args.output_dir}/{slug}")
        else:
            print(f"❌ Failed to scaffold feature.")
            
    def run_implement(self, args, context: Context):
        print(f"🏗️  Injecting '{args.implements}' methods into '{args.class_name}' in '{args.file}'...")
        
        use_case = ImplementInterfaceUseCase(
            context.file_system,
            context.language_parser,
            context.strategy_provider
        )
        
        success = use_case.execute(args.file, args.class_name, args.implements)
        if success:
            print(f"✅ Implementation complete.")
        else:
            print(f"❌ Failed to implement interface.")

    def run_register(self, args, context: Context):
        print(f"🏗️  Registering dependency in '{args.file}'...")
        
        use_case = RegisterDependencyUseCase(
            context.file_system,
            context.language_parser,
            context.strategy_provider
        )
        
        success = use_case.execute(args.file, args.import_path, args.binding)
        if success:
            print(f"✅ Registration complete.")
        else:
            print(f"❌ Failed to register dependency.")

    def run_project(self, args, context: Context):
        print(f"🏗️  Projecting '{args.entity}' into '{args.dto}'...")
        
        use_case = ProjectDtoUseCase(
            context.file_system,
            context.language_parser,
            context.strategy_provider
        )
        
        success = use_case.execute(args.source_file, args.entity, args.target_file, args.dto, args.stack)
        if success:
            print(f"✅ Projection complete.")
        else:
            print(f"❌ Failed to project DTO.")
