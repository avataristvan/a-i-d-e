import os
from typing import Tuple, Optional
from aide.core.domain.ports import FileSystemPort, LanguageStrategy, LlmProvider
from aide.parsing.domain.ports import LanguageParserPort
from aide.core.infrastructure.strategy_provider import StrategyProvider
from aide.core.infrastructure.briefing_service import BriefingService

class ImplementLogicUseCase:
    def __init__(self, 
                 file_system: FileSystemPort, 
                 language_parser: LanguageParserPort,
                 strategy_provider: StrategyProvider,
                 llm_provider: LlmProvider,
                 briefing_service: BriefingService):
        self.file_system = file_system
        self.language_parser = language_parser
        self.strategy_provider = strategy_provider
        self.llm_provider = llm_provider
        self.briefing_service = briefing_service


    def execute(self, file_path: str, symbol_name: str, prompt: str, dry_run: bool = False) -> Tuple[bool, str]:
        """
        Extracts the method bounds, prompts the LLM to write the body,
        and splices the LLM's response back into the original file.
        Returns (success, message_or_error)
        """
        try:
            content = self.file_system.read_file(file_path)
        except Exception as e:
            return False, f"Failed to read file: {e}"

        strategy = self.strategy_provider.get_strategy(file_path)
        if not strategy:
            return False, f"Unsupported language for implementation targeting: {file_path}"
            
        lines = content.splitlines()
        
        # 1. Find the bounds of the function
        start_line, end_line = strategy.find_symbol_range(lines, symbol_name)
        if start_line is None or end_line is None:
            return False, f"Symbol '{symbol_name}' not found in {file_path}"

        # 2. Extract context
        # We grab the full block to provide to the LLM and to replace later.
        full_block = lines[start_line - 1:end_line]

        # 2.5 Load Persona Rules, Dependencies & Symbol Map
        persona_rules = self.briefing_service.get_persona_rules()
        dependency_context = self.briefing_service.get_dependency_context(file_path)
        symbol_map = self.briefing_service.get_symbol_map(file_path, content)

        # 3. Construct the prompt
        system_prompt = (
            "You are an AIDE Sub-Agent Logic Generator. You operate as a pure AST block replacement engine.\n\n"
            "PERSONA RULES:\n"
            f"{persona_rules}\n\n"
            "PROJECT CONTEXT (DEPENDENCIES):\n"
            f"{dependency_context}\n\n"
            "FILE ARCHITECTURE (SYMBOL MAP):\n"
            f"{symbol_map}\n\n"
            "CONTEXT RULES:\n"
            "1. You are given the ENTIRE source code block of a function or class (including signature and braces/indentation).\n"
            "2. You must implement the business logic described by the user's prompt.\n"
            "3. Your resulting code MUST be the EXACT, COMPLETE replacement block. Do not omit the function signature or trailing braces.\n"
            "4. Do NOT output markdown code blocks (e.g., ```python).\n"
            "5. Do NOT explain your code. Output ONLY raw executable code.\n"
            "6. Preserve the exact indentation of the original signature."
        )
        
        user_prompt = (
            f"Target Block Context:\n"
            f"{chr(10).join(full_block)}\n\n"
            f"Task: {prompt}\n\n"
            f"Provide the complete, raw replacement block:"
        )

        try:
            llm_response = self.llm_provider.generate(system_prompt, user_prompt)
        except Exception as e:
            return False, f"LLM Generation failed: {e}"

        # Clean the LLM response in case it hallucinated markdown anyway
        cleaned_response = llm_response
        
        # Remove empty newlines at start and end without destroying leading spaces
        while cleaned_response.startswith("\n") or cleaned_response.startswith("\r"):
            cleaned_response = cleaned_response[1:]
        while cleaned_response.endswith("\n") or cleaned_response.endswith("\r"):
            cleaned_response = cleaned_response[:-1]
            
        if cleaned_response.strip().startswith("```"):
            lines_resp = cleaned_response.strip().splitlines()
            if len(lines_resp) > 1 and lines_resp[0].startswith("```"):
                lines_resp = lines_resp[1:]
            if len(lines_resp) > 0 and lines_resp[-1].startswith("```"):
                lines_resp = lines_resp[:-1]
            cleaned_response = "\n".join(lines_resp)

        # 4. Splicing
        # Because we asked the LLM for the *entire block*, we simply replace the exact lines bounds.
        new_block_lines = cleaned_response.splitlines()
        
        # Ensure that if the LLM stripped the base indentation of the signature, we restore it.
        # This is a safety check: if the original block had 4 spaces indent, and the LLM returned it at 0 spaces,
        # we re-pad the entire block.
        if len(full_block) > 0 and len(new_block_lines) > 0:
            original_indent_count = len(full_block[0]) - len(full_block[0].lstrip())
            llm_indent_count = len(new_block_lines[0]) - len(new_block_lines[0].lstrip())
            
            # Only add padding if the LLM dropped the original base indent (it returned it flat)
            if original_indent_count > llm_indent_count:
                missing_spaces = original_indent_count - llm_indent_count
                padding = " " * missing_spaces
                new_block_lines = [padding + line if line.strip() else line for line in new_block_lines]

        new_lines = lines[:start_line-1] + new_block_lines + lines[end_line:]

        # 5. Result
        if not dry_run:
            self.file_system.write_file(file_path, "\n".join(new_lines))
        return True, "Logic implemented and injected successfully."

