#!/usr/bin/env python3
import argparse
import sys
import os

# Add current directory to path so we can import 'aide' package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from aide.core.context import Context
from aide.core.infrastructure.os_file_system import OsFileSystem
from aide.parsing.infrastructure.parsers import RegexLanguageParser, CompositeLanguageParser
from aide.parsing.infrastructure.ast_parsers import AstPythonParser
from aide.plugin_system.infrastructure.plugin_loader import PluginLoader

def main():
    parser = argparse.ArgumentParser(description="a-i-d-e: The AI's IDE (Plugin Architecture)")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # 1. Initialize Core Infrastructure
    file_system = OsFileSystem()
    
    # Setup Language Parsers
    fallback_parser = RegexLanguageParser()
    composite_parser = CompositeLanguageParser(fallback_parser)
    composite_parser.register(".py", AstPythonParser())
    
    context = Context(file_system=file_system, language_parser=composite_parser)

    # 2. Load Plugins (from features directory)
    # We now point to the new 'features' directory for capabilities
    plugin_dir = os.path.join(os.path.dirname(__file__), "aide", "features")
    loader = PluginLoader(plugin_dir)
    loader.load_plugins(subparsers, context)

    args = parser.parse_args()

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        # Print a friendly error message to stderr
        print(f"\033[91mError: {str(e)}\033[0m", file=sys.stderr)
        
        # Log full traceback to a file (or print if verbose, but let's stick to file/simple for now)
        # We can also print the traceback if it's a critical error
        # For now, let's print the traceback to stderr as well, but maybe less obtrusively?
        # Actually, let's just print it. The user is a dev.
        traceback.print_exc()
        sys.exit(1)
