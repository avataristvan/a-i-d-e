# Example: Agentic Refactoring 

This example demonstrates how an AI agent uses `a-i-d-e` to seamlessly navigate a repository and refactor a core component deterministically.

## The Goal
The agent needs to extract a messy, inline string processing block from `app.py` into a reusable `format_currency` function in `utils.py`.

### Step 1: Discover context with `outline`
The agent uses `a-i-d-e` to look at the structure of `app.py`.

**Agent Terminal Command:**
```bash
$ aide outline app.py
```

**AIDE Output:**
```
Found 2 symbols in app.py:
  File: app.py
    Function: main (Lines 10-45)
    Class: OrderProcessor (Lines 48-120)
       Method: calculate_total (Lines 55-80)
```

### Step 2: Read specific line numbers
The agent reads `OrderProcessor.calculate_total` to find the target block.

**Agent Terminal Command:**
```bash
$ aide read app.py --selection 55:80
```

**AIDE Output:**
```python
55:     def calculate_total(self, items):
...
68:         # messy string formatting
69:         amount_str = str(total)
70:         if "." in amount_str:
71:             cents = amount_str.split(".")[1]
72:             if len(cents) == 1:
73:                 amount_str += "0"
74:         formatted = f"${amount_str}"
75:         return formatted
```

### Step 3: Deterministic Extraction
Instead of hallucinating python code with `sed` or trying to rewrite the whole file, the agent uses AIDE to safely extract the block to a new function in `utils.py`.

**Agent Terminal Command:**
```bash
$ aide extract --file app.py --selection 69:74 --name format_currency
```

**AIDE Output:**
```
✅ Extracted 'format_currency' from app.py.
```

### Step 4: Move the newly created symbol
The new `format_currency` function is at the top of `app.py`. The agent moves it to `utils.py` across the codebase.

**Agent Terminal Command:**
```bash
$ aide move-symbol format_currency --source app.py --dest utils.py
```

**AIDE Output:**
```
✅ Moved 'format_currency' from app.py to utils.py.
✅ Automatically added 'from utils import format_currency' to app.py.
```

### Result
The agent successfully mapped the project, read specific line bounds, cleanly extracted a local function, and migrated it into a generic utilities file while completely avoiding LLM hallucination or broken regex edits!
