from aide.core.domain.ports import FileSystemPort, LlmProvider
from aide.core.infrastructure.strategy_provider import StrategyProvider
from aide.core.infrastructure.briefing_service import BriefingService

class ProjectDtoUseCase:
    def __init__(self, 
                 file_system: FileSystemPort, 
                 strategy_provider: StrategyProvider,
                 llm_provider: LlmProvider,
                 briefing_service: BriefingService):
        self.file_system = file_system
        self.strategy_provider = strategy_provider
        self.llm_provider = llm_provider
        self.briefing_service = briefing_service

    def execute(self, source_file: str, entity_name: str, target_file: str, dto_name: str, stack: str) -> bool:
        try:
            content = self.file_system.read_file(source_file)
            lines = content.splitlines()
            
            strategy = self.strategy_provider.get_strategy(source_file)
            if not strategy:
                return False
                
            # 1. Find the entity class bounds
            start, end = strategy.find_symbol_range(lines, entity_name)
            if not start:
                return False

            entity_source = "\n".join(lines[start-1:end])
            
            # 2. Get Context Briefing
            persona_rules = self.briefing_service.get_persona_rules()
            dependency_context = self.briefing_service.get_dependency_context(source_file)
            
            # 3. LLM Generation
            system_prompt = (
                "You are an AIDE Sub-Agent DTO Generator.\n\n"
                "PERSONA RULES:\n"
                f"{persona_rules}\n\n"
                "PROJECT CONTEXT:\n"
                f"{dependency_context}\n\n"
                "GOAL:\n"
                "1. Generate a DTO (Data Transfer Object) class based on the provided source entity.\n"
                "2. Include mapping logic (e.g., from_entity or to_dto).\n"
                "3. Follow the idiomatic style for the requested stack/language.\n"
                "4. Output ONLY raw code. Do NOT output markdown code blocks."
            )
            
            user_prompt = (
                f"Source Entity ({source_file}):\n"
                f"{entity_source}\n\n"
                f"Requested DTO Name: {dto_name}\n"
                f"Target Stack: {stack}\n\n"
                "Generate the DTO content:"
            )

            dto_content = self.llm_provider.generate(system_prompt, user_prompt)
            
            # Clean possible markdown
            if dto_content.startswith("```"):
                dto_lines = dto_content.splitlines()
                if dto_lines[0].startswith("```"): dto_lines = dto_lines[1:]
                if dto_lines and dto_lines[-1].startswith("```"): dto_lines = dto_lines[:-1]
                dto_content = "\n".join(dto_lines)
            
            self.file_system.write_file(target_file, dto_content.strip() + "\n")
            return True

        except Exception as e:
            return False

