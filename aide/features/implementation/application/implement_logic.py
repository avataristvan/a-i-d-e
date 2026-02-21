import os
from typing import Tuple, Optional
from aide.core.domain.ports import FileSystemPort, LanguageStrategy, LlmProvider
from aide.parsing.domain.ports import LanguageParserPort
from aide.core.infrastructure.strategy_provider import StrategyProvider

class ImplementLogicUseCase:
    def __init__(self, 
                 file_system: FileSystemPort, 
                 language_parser: LanguageParserPort,
                 strategy_provider: StrategyProvider,
                 llm_provider: LlmProvider):
        self.file_system = file_system
        self.language_parser = language_parser
        self.strategy_provider = strategy_provider
        self.llm_provider = llm_provider

    def _get_indentation(self, line: str) -> str:
        """Returns the leading whitespace of a line."""
        return line[:len(line) - len(line.lstrip())]

    def _determine_body_indentation(self, lines: list[str], start_line: int, end_line: int) -> str:
        """Determines the correct body indentation by looking at the first non-empty line after the signature."""
        for i in range(start_line, end_line):
            line_content = lines[i]
            if line_content.strip() and not line_content.strip().startswith("{"):
                return self._get_indentation(line_content)
                
        # Fallback: Signature indentation + 4 spaces
        sig_indent = self._get_indentation(lines[start_line - 1])
        return sig_indent + "    "

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
        signature_lines = lines[start_line - 1:start_line] # Very naive, but ASTs might span multiple lines. We'll grab full block.
        full_block = lines[start_line - 1:end_line]
        
        body_indentation = self._determine_body_indentation(lines, start_line, end_line)

        # 3. Construct the prompt
        system_prompt = (
            "You are an AIDE Sub-Agent Logic Generator. You operate as a pure function body compiler.\n\n"
            "CONTEXT RULES:\n"
            "1. You are given the signature of a function/method and its surrounding context.\n"
            "2. You must implement the business logic described by the user's prompt.\n"
            f"3. Your resulting code MUST use exactly '{body_indentation}' at the base indentation level for the body.\n"
            "4. Do NOT output markdown code blocks (e.g., ```python).\n"
            "5. Do NOT repeat the function signature or the closing brace. ONLY output the inner body execution lines.\n"
            "6. Do NOT explain your code. Output ONLY raw executable code.\n"
            "7. Assume any required imports are already present at the top of the file."
        )
        
        user_prompt = (
            f"Target Method Context:\n"
            f"{chr(10).join(full_block)}\n\n"
            f"Task: {prompt}\n\n"
            f"Provide only the replacement body:"
        )

        try:
            llm_response = self.llm_provider.generate(system_prompt, user_prompt)
        except Exception as e:
            return False, f"LLM Generation failed: {e}"

        # Clean the LLM response in case it hallucinated markdown anyway
        cleaned_response = llm_response.strip()
        if cleaned_response.startswith("```"):
            lines_resp = cleaned_response.splitlines()
            if len(lines_resp) > 1 and lines_resp[0].startswith("```"):
                lines_resp = lines_resp[1:]
            if len(lines_resp) > 0 and lines_resp[-1].startswith("```"):
                lines_resp = lines_resp[:-1]
            cleaned_response = "\n".join(lines_resp).strip()

        # 4. Splicing
        # We need to replace everything *between* the signature and the end of the original block.
        # This is language specific, but generically, for Python, replacing everything after the `def ...:`
        # For C-like languages, replacing everything between `{` and `}`.
        
        # Generic heuristic:
        # Keep the first line of the block (signature), and the last line (if it's just a closure brace)
        # We'll rely on the LLM to provide properly indented contents, and append it after the signature.
        
        # A safer AST-agnostic replacement logic:
        new_block = [full_block[0]] # Keep definition line
        
        # Add LLM output, ensuring proper base indentation if the LLM didn't indent properly
        for resp_line in cleaned_response.splitlines():
             if resp_line.strip() == "":
                 new_block.append("")
             else:
                 # If the line already starts with the correct indentation, keep it, otherwise force it
                 if not resp_line.startswith(body_indentation) and not resp_line.startswith(" ") and not resp_line.startswith("\t"):
                     new_block.append(body_indentation + resp_line)
                 else:
                     new_block.append(resp_line)
        
        # Keep closing brace if it was a distinct line (common in C/Java/Kotlin/TS)
        if full_block[-1].strip() == "}":
            new_block.append(full_block[-1])
            
        new_lines = lines[:start_line-1] + new_block + lines[end_line:]
        
        new_content = "\n".join(new_lines) + "\n"

        if not dry_run:
            self.file_system.write_file(file_path, new_content)

        return True, "Logic implemented and injected successfully."
