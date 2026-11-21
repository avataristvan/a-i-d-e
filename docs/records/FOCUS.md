Goal: AIDE plus Claude Code's LSP tool fully replace an IDE MCP server (IntelliJ) for agent work: symbol search, references, live diagnostics, refactoring, with no running IDE.

Now:
- Gap analysis: which IntelliJ-MCP capabilities (search_symbol, get_symbol_info, get_file_problems, rename, find usages, project structure) are not yet covered by LSP + AIDE, and which of them AIDE should provide.

Next:
- Clean up pyright errors in aide/ (mostly Optional handling).
- README.md: add clone-symbol, semantic rename-symbol, the Kotlin/clangd parsers and the LSP client (all committed now).

Backlog: BACKLOG.md.
