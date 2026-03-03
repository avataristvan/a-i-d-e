#!/usr/bin/env python3
import os
import shutil
import sys

def prompt_target():
    print("\nSelect target AI to configure:")
    print("  1) Claude  (~/.claude/skills/aide)")
    print("  2) Gemini  (~/.gemini/extensions/aide-extension)")
    print("  3) All     [default]")
    choice = input("\nChoice [1/2/3]: ").strip()
    return {"1": "claude", "2": "gemini"}.get(choice, "all")

def install_core(repo_root, install_dir, bin_dir, shim_path):
    os.makedirs(install_dir, exist_ok=True)
    os.makedirs(bin_dir, exist_ok=True)

    print(f"📦 Copying core files to {install_dir}...")
    for item in ["aide.py", "aide"]:
        src = os.path.join(repo_root, item)
        dst = os.path.join(install_dir, item)
        if os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

    print(f"🔗 Creating global shim at {shim_path}...")
    shim_content = f"""#!/usr/bin/env python3
import os
import sys

AIDE_ENTRY = "{os.path.join(install_dir, 'aide.py')}"

if __name__ == "__main__":
    if not os.path.exists(AIDE_ENTRY):
        print(f"Error: AIDE entrypoint not found at {{AIDE_ENTRY}}", file=sys.stderr)
        sys.exit(1)
    os.execv(sys.executable, [sys.executable, AIDE_ENTRY] + sys.argv[1:])
"""
    with open(shim_path, "w") as f:
        f.write(shim_content)

    print("🔐 Setting permissions...")
    os.chmod(os.path.join(install_dir, "aide.py"), 0o755)
    os.chmod(shim_path, 0o755)

def install_claude(repo_root, install_dir, home):
    src = os.path.join(repo_root, "setup-files/claude-global-aide")
    dst = os.path.join(install_dir, "claude-skill")
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

    skills_dir = os.path.join(home, ".claude/skills")
    link = os.path.join(skills_dir, "aide")
    os.makedirs(skills_dir, exist_ok=True)
    if os.path.islink(link):
        os.unlink(link)
    elif os.path.isdir(link):
        shutil.rmtree(link)
    os.symlink(dst, link)
    print(f"🤖 Claude skill linked: {link}")
    return link

def install_gemini(repo_root, install_dir):
    shutil.copy2(
        os.path.join(repo_root, "setup-files/gemini-global-aide/SKILL.md"),
        os.path.join(install_dir, "SKILL.md"),
    )
    dst_ext = os.path.join(install_dir, "gemini-extension.json")
    shutil.copy2(
        os.path.join(repo_root, "setup-files/gemini-global-aide/gemini-extension.json"),
        dst_ext,
    )
    print(f"🚀 Gemini extension files copied to {install_dir}")
    return dst_ext

def install(target=None):
    home = os.path.expanduser("~")
    repo_root = os.path.dirname(os.path.abspath(__file__))
    if repo_root.endswith("/scripts"):
        repo_root = os.path.dirname(repo_root)

    install_dir = os.path.join(home, ".local/share/aide")
    bin_dir = os.path.join(home, ".local/bin")
    shim_path = os.path.join(bin_dir, "aide")

    if target is None:
        target = prompt_target()

    print(f"\n🚀 Installing AIDE ({target}) from {repo_root}...")

    install_core(repo_root, install_dir, bin_dir, shim_path)

    claude_link = None
    dst_ext = None

    if target in ("claude", "all"):
        claude_link = install_claude(repo_root, install_dir, home)

    if target in ("gemini", "all"):
        dst_ext = install_gemini(repo_root, install_dir)

    # Verify PATH
    if bin_dir not in os.environ.get("PATH", ""):
        print(f"\n⚠️  Warning: {bin_dir} is not in your PATH.")
        print(f'   Add to your shell config: export PATH="$HOME/.local/bin:$PATH"')

    # Summary
    print("\n" + "=" * 50)
    print("✅ AIDE INSTALLED SUCCESSFULLY")
    print("=" * 50)
    if claude_link:
        print(f"\n🤖 CLAUDE CODE  — /aide skill active")
        print(f"   {claude_link}")
    if dst_ext:
        print(f"\n🚀 GEMINI  — register the native extension:")
        print(f"   mkdir -p ~/.gemini/extensions/aide-extension")
        print(f"   cp {dst_ext} ~/.gemini/extensions/aide-extension/")
    print("=" * 50 + "\n")

if __name__ == "__main__":
    # Optional: pass target as CLI arg for non-interactive use
    # e.g.  python install_global.py claude
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    if arg and arg not in ("claude", "gemini", "all"):
        print(f"Usage: {sys.argv[0]} [claude|gemini|all]", file=sys.stderr)
        sys.exit(1)
    install(target=arg)
