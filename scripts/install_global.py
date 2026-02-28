#!/usr/bin/env python3
import os
import shutil
import sys
import stat

def install():
    home = os.path.expanduser("~")
    repo_root = os.path.dirname(os.path.abspath(__file__))
    if repo_root.endswith("/scripts"):
        repo_root = os.path.dirname(repo_root)
        
    install_dir = os.path.join(home, ".local/share/aide")
    bin_dir = os.path.join(home, ".local/bin")
    shim_path = os.path.join(bin_dir, "aide")

    print(f"🚀 Installing AIDE from {repo_root}...")

    # 1. Create Directories
    os.makedirs(install_dir, exist_ok=True)
    os.makedirs(bin_dir, exist_ok=True)

    # 2. Copy AIDE Core
    print(f"📦 Copying core files to {install_dir}...")
    
    # Items to copy (base items and specific skill)
    items = ["aide.py", "aide"]
    for item in items:
        src = os.path.join(repo_root, item)
        dst = os.path.join(install_dir, item)
        if os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
            
    # Copy Global Skill
    src_skill = os.path.join(repo_root, "setup-files/global-aide/SKILL.md")
    dst_skill = os.path.join(install_dir, "SKILL.md")
    shutil.copy2(src_skill, dst_skill)

    # Copy Native Extension Metadata
    src_ext = os.path.join(repo_root, "setup-files/global-aide/gemini-extension.json")
    dst_ext = os.path.join(install_dir, "gemini-extension.json")
    shutil.copy2(src_ext, dst_ext)

    # 3. Create Shim
    print(f"🔗 Creating global shim at {shim_path}...")
    shim_content = f"""#!/usr/bin/env python3
import os
import sys

# Global AIDE Entrypoint
AIDE_ENTRY = "{os.path.join(install_dir, 'aide.py')}"

if __name__ == "__main__":
    if not os.path.exists(AIDE_ENTRY):
        print(f"Error: AIDE entrypoint not found at {{AIDE_ENTRY}}", file=sys.stderr)
        sys.exit(1)
    
    # Execute AIDE with passed arguments
    os.execv(sys.executable, [sys.executable, AIDE_ENTRY] + sys.argv[1:])
"""
    with open(shim_path, "w") as f:
        f.write(shim_content)

    # 4. Set Permissions
    print("🔐 Setting permissions...")
    # Executable for aide.py in share
    os.chmod(os.path.join(install_dir, "aide.py"), 0o755)
    # Executable for shim in bin
    os.chmod(shim_path, 0o755)

    # 5. Verify Path
    path_env = os.environ.get("PATH", "")
    if bin_dir not in path_env:
        print(f"\n⚠️  Warning: {bin_dir} is not in your PATH.")
        print("Add this to your shell config (e.g., .bashrc or .zshrc):")
        print(f'export PATH="$HOME/.local/bin:$PATH"')
    # 5. Success Message
    print("\n" + "="*50)
    print("✅ AIDE INSTALLED SUCCESSFULLY")
    print("="*50)
    print("\n🚀 NATIVE GEMINI EXTENSION (Recommended)")
    print("   Register AIDE natively in Gemini by running:")
    print(f"   mkdir -p ~/.gemini/extensions/aide-extension")
    print(f"   cp {dst_ext} ~/.gemini/extensions/aide-extension/")
    
    print("\n💡 NOTE: Manual 'memory rules' (SKILL.md) are NOT needed")
    print("   when using the native extension.")
    print("="*50 + "\n")

if __name__ == "__main__":
    install()
