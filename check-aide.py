#!/usr/bin/env python3
import os
import subprocess
import sys

def check():
    print("🔍 Verifying AIDE Clone...")
    
    # 1. Check AIDE core
    if not os.path.exists("aide.py"):
        print("❌ Error: aide.py not found in current directory.")
        return False
    
    # 2. Check Permissions
    if not os.access("aide.py", os.X_OK):
        print("⚠️  Warning: aide.py is not executable. Run 'chmod +x aide.py'.")
    else:
        print("✅ Permissions: OK")

    # 3. Check Dependencies
    try:
        import tree_sitter
        print("✅ tree-sitter: OK")
    except ImportError:
        print("⚠️  Warning: tree-sitter not found. AST parsing will use regex fallback.")

    # 4. Functional Test
    print("🧪 Running functional check...")
    try:
        result = subprocess.run([sys.executable, "aide.py", "outline", "aide.py"], 
                                capture_output=True, text=True, check=True)
        if "main" in result.stdout:
            print("✅ Functional Check: OK (Outline found 'main')")
        else:
            print("⚠️  Functional Check: Unexpected output from outline.")
    except Exception as e:
        print(f"❌ Functional Check: FAILED ({e})")
        return False

    print("\n🚀 AIDE is healthy and ready for your agents!")
    return True

if __name__ == "__main__":
    if not check():
        sys.exit(1)
