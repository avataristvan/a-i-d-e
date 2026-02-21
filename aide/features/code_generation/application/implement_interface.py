from aide.core.domain.ports import FileSystemPort, LlmProvider
from aide.core.infrastructure.strategy_provider import StrategyProvider
from aide.core.infrastructure.briefing_service import BriefingService

class ImplementInterfaceUseCase:
    def __init__(self, 
                 file_system: FileSystemPort, 
                 strategy_provider: StrategyProvider,
                 llm_provider: LlmProvider,
                 briefing_service: BriefingService):
        self.file_system = file_system
        self.strategy_provider = strategy_provider
        self.llm_provider = llm_provider
        self.briefing_service = briefing_service

    def execute(self, file_path: str, class_name: str, interface_name: str) -> bool:
        try:
            content = self.file_system.read_file(file_path)
            lines = content.splitlines()
            
            strategy = self.strategy_provider.get_strategy(file_path)
            if not strategy: return False

            iface_start, iface_end = strategy.find_symbol_range(lines, interface_name)
            class_start, class_end = strategy.find_symbol_range(lines, class_name)
            
            if not iface_start or not class_start: return False

            iface_source = "\n".join(lines[iface_start-1:iface_end])
            class_source = "\n".join(lines[class_start-1:class_end])

            persona_rules = self.briefing_service.get_persona_rules()
            dependency_context = self.briefing_service.get_dependency_context(file_path)

            system_prompt = (
                "You are an AIDE Sub-Agent Interface Implementer.\n\n"
                "PERSONA RULES:\n"
                f"{persona_rules}\n\n"
                "PROJECT CONTEXT:\n"
                f"{dependency_context}\n\n"
                "GOAL:\n"
                "1. Analyze the provided interface and the concrete class.\n"
                "2. Identify missing methods in the concrete class that are required by the interface.\n"
                "3. Generate ONLY the missing methods to be appended to the class.\n"
                "4. Output ONLY raw code. Do NOT output markdown code blocks."
            )

            user_prompt = (
                f"Interface ({interface_name}):\n{iface_source}\n\n"
                f"Concrete Class ({class_name}):\n{class_source}\n\n"
                "Generate the missing method implementations:"
            )

            missing_code = self.llm_provider.generate(system_prompt, user_prompt)
            
            # Clean markdown
            if missing_code.startswith("```"):
                m_lines = missing_code.splitlines()
                if m_lines[0].startswith("```"): m_lines = m_lines[1:]
                if m_lines and m_lines[-1].startswith("```"): m_lines = m_lines[:-1]
                missing_code = "\n".join(m_lines)

            # Splice: Insert before the last closing brace if C-style, or just at end for Python
            if file_path.endswith((".kt", ".java", ".ts")):
                 for i in reversed(range(class_start-1, class_end)):
                     if "}" in lines[i]:
                         lines.insert(i, missing_code.strip())
                         break
            else:
                 lines.insert(class_end, missing_code.strip())

            self.file_system.write_file(file_path, "\n".join(lines) + "\n")
            return True
        except Exception:
            return False

