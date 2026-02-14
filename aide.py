#!/usr/bin/env python3
import argparse
import sys
import os

# Add current directory to path so we can import 'aide' package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from aide.core.context import Context
from aide.core.infrastructure.os_file_system import OsFileSystem
from aide.parsing.infrastructure.parsers import RegexLanguageParser
from aide.plugin_system.infrastructure.plugin_loader import PluginLoader

def main():
    parser = argparse.ArgumentParser(description="a-i-d-e: The AI's IDE (Plugin Architecture)")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # 1. Initialize Core Infrastructure
    file_system = OsFileSystem()
    language_parser = RegexLanguageParser()
    context = Context(file_system=file_system, language_parser=language_parser)

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
    main()
