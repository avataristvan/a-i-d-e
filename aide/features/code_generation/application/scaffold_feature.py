import json
import os
from aide.core.domain.ports import FileSystemPort, LlmProvider
from aide.core.infrastructure.briefing_service import BriefingService

class ScaffoldFeatureUseCase:
    def __init__(self, 
                 file_system: FileSystemPort, 
                 llm_provider: LlmProvider,
                 briefing_service: BriefingService):
        self.file_system = file_system
        self.llm_provider = llm_provider
        self.briefing_service = briefing_service

    def execute(self, feature_name: str, stack: str, output_dir: str) -> bool:
        try:
            feature_slug = feature_name.lower().replace(" ", "_").replace("-", "_")
            persona_rules = self.briefing_service.get_persona_rules()
            dependency_context = self.briefing_service.get_dependency_context(output_dir)

            system_prompt = (
                "You are an AIDE Sub-Agent Feature Scaffolder.\n\n"
                "PERSONA RULES:\n"
                f"{persona_rules}\n\n"
                "PROJECT CONTEXT:\n"
                f"{dependency_context}\n\n"
                "GOAL:\n"
                "Generate a standard Clean Architecture boilerplate for a new feature.\n"
                "Requirement: Output exactly a JSON object mapping relative file paths to their content.\n\n"
                "JSON FORMAT:\n"
                "{\n"
                "  \"domain/Entity.kt\": \"package ...\",\n"
                "  \"application/UseCase.kt\": \"package ...\",\n"
                "  \"infrastructure/Repository.kt\": \"package ...\"\n"
                "}\n"
                "Do NOT include markdown blocks. ONLY raw JSON."
            )

            user_prompt = (
                f"Feature Name: {feature_name}\n"
                f"Feature Slug: {feature_slug}\n"
                f"Target Stack: {stack}\n\n"
                "Generate the boilerplate structure:"
            )

            response = self.llm_provider.generate(system_prompt, user_prompt)
            
            # Simple JSON extraction
            start = response.find("{")
            end = response.rfind("}") + 1
            if start == -1 or end == 0:
                return False
                
            files_to_create = json.loads(response[start:end])
            
            base_path = os.path.join(output_dir, feature_slug)
            
            for rel_path, content in files_to_create.items():
                full_path = os.path.join(base_path, rel_path)
                self.file_system.write_file(full_path, content.strip() + "\n")
                
            return True
        except Exception as e:
            return False
