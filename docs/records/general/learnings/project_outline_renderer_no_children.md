type: learning
topic: general
created: 1782658616.975737
---

Der OutlineUseCase-Renderer (aide/features/code_inspection/application/outline.py:33) iteriert nur Top-Level-SymbolNodes ohne Children zu rekursieren. War unsichtbar solange Regex-Parser flache Listen lieferten. Mit clangd (hierarchisch: Namespace → Klasse → Methoden) werden Children verschluckt — nur der Namespace erscheint im Output.
Why: Renderer muss um rekursive Darstellung mit Einrückung erweitert werden.