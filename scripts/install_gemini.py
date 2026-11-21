#!/usr/bin/env python3
"""Registers AIDE as a Gemini CLI extension (~/.gemini/extensions/aide-extension).

Claude Code gets AIDE from the aide@aide plugin instead (.claude-plugin/, enabled per project).
Nothing is copied: the extension's context file points Gemini at this checkout's bin/aide, so
code changes take effect without re-installing.
"""
import os
import shutil

AIDE_BIN_PLACEHOLDER = "{{AIDE_BIN}}"


def check_optional_deps():
    missing = []
    if not shutil.which("clangd"):
        missing.append(("clangd", "C/C++ LSP parsing (outline, usages)", "sudo pacman -S clang"))
    return missing


def install():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(repo_root, "setup-files", "gemini-global-aide")
    ext_dir = os.path.join(os.path.expanduser("~"), ".gemini", "extensions", "aide-extension")
    os.makedirs(ext_dir, exist_ok=True)

    shutil.copy2(os.path.join(src, "gemini-extension.json"), os.path.join(ext_dir, "gemini-extension.json"))
    with open(os.path.join(src, "SKILL.md"), encoding="utf-8") as f:
        context = f.read().replace(AIDE_BIN_PLACEHOLDER, os.path.join(repo_root, "bin", "aide"))
    with open(os.path.join(ext_dir, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write(context)

    print(f"✅ Gemini extension written to {ext_dir}")
    if not shutil.which("gemini"):
        print("   Note: the gemini CLI is not on PATH.")
    for name, feature, cmd in check_optional_deps():
        print(f"⚙️  Optional: {name} ({feature}) — install with: {cmd}")


if __name__ == "__main__":
    install()
