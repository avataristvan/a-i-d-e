type: pattern
topic: general
created: 1782658610.652735
---

Rule: LSP SymbolKind für C++ struct ist Class (5), nicht Struct (23)
When: Bei clangd-Integration oder anderen C++ LSP-Servern, die DocumentSymbol zurückgeben
Why: In C++ unterscheiden sich struct und class nur in Default-Visibility — clangd 22 normalisiert beide auf Class. Tests und Kind-Mappings müssen `kind in ("struct", "class")` prüfen, nicht exklusiv auf "struct".