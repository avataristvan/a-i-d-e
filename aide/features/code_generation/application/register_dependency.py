from aide.core.domain.ports import FileSystemPort, LlmProvider
from aide.core.infrastructure.strategy_provider import StrategyProvider
from aide.core.infrastructure.briefing_service import BriefingService

class RegisterDependencyUseCase:
    def __init__(self, 
                 file_system: FileSystemPort, 
                 strategy_provider: StrategyProvider,
                 llm_provider: LlmProvider,
                 briefing_service: BriefingService):
        self.file_system = file_system
        self.strategy_provider = strategy_provider
        self.llm_provider = llm_provider
        self.briefing_service = briefing_service

    def execute(self, file_path: str, import_path: str, binding: str) -> bool:
        try:
            content = self.file_system.read_file(file_path)
            
            persona_rules = self.briefing_service.get_persona_rules()
            dependency_context = self.briefing_service.get_dependency_context(file_path)

            system_prompt = (
                "You are an AIDE Sub-Agent Dependency Injector.\n\n"
                "PERSONA RULES:\n"
                f"{persona_rules}\n\n"
                "PROJECT CONTEXT:\n"
                f"{dependency_context}\n\n"
                "GOAL:\n"
                "1. Analyze the provided file content.\n"
                "2. Inject the necessary import and the binding code in the most idiomatic location.\n"
                "3. Ensure the result is syntactically correct and respects surrounding style.\n"
                "4. Output exactly the new ENTIRE file content.\n"
                "5. Do NOT output markdown code blocks. ONLY raw code."
            )

            user_prompt = (
                f"File: {file_path}\n"
                f"Content:\n{content}\n\n"
                f"Requested Import: {import_path}\n"
                f"Requested Binding Code: {binding}\n\n"
                "Generate the updated file content:"
            )

            new_content = self.llm_provider.generate(system_prompt, user_prompt)
            
            # Clean markdown if LLM disobeyed
            if new_content.startswith("```"):
                nc_lines = new_content.splitlines()
                if nc_lines[0].startswith("```"): nc_lines = nc_lines[1:]
                if nc_lines and nc_lines[-1].startswith("```"): nc_lines = nc_lines[:-1]
                new_content = "\n".join(nc_lines)

            self.file_system.write_file(file_path, new_content.strip() + "\n")
            return True
        except Exception:
            return False
