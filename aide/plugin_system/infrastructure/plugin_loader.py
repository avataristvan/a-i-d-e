import os
import importlib.util
from argparse import _SubParsersAction
from aide.plugin_system.domain.plugin import Plugin
from aide.core.context import Context

class PluginLoader:
    def __init__(self, plugin_dir: str):
        self.plugin_dir = plugin_dir

    def load_plugins(self, subparsers: _SubParsersAction, context: Context) -> None:
        if not os.path.exists(self.plugin_dir):
            return

        # Walk through all subdirectories in the features/ folder
        # We expect a structure like aide/features/feature_name/plugin.py
        
        # Also support legacy flat plugins folder if we keep it, but we are moving to capability centric.
        # Let's assume self.plugin_dir is now 'aide/features'
        
        # Valid strategy:
        # 1. Walk directories.
        # 2. Look for 'plugin.py' or '*_plugin.py'.
        
        for root, dirs, files in os.walk(self.plugin_dir):
             for filename in files:
                if filename.endswith("_plugin.py") or filename == "plugin.py":
                    plugin_path = os.path.join(root, filename)
                    
                    # Calculate module name from path relative to 'aide' root?
                    # or just load by path
                    
                    # Assuming we run from root, and plugin_path is absolute or relative
                    # Module name needs to be unique.
                    
                    rel_path = os.path.relpath(plugin_path, os.getcwd()) 
                    # e.g. a-i-d-e/aide/features/code_cleanup/plugin.py
                    
                    # Convert path to module dotted name
                    # Remove .py
                    module_name = rel_path.replace(os.path.sep, ".")[:-3]
                    # Fix starting dot if any
                    if module_name.startswith("."): module_name = module_name[1:]
                    
                    try:
                        spec = importlib.util.spec_from_file_location(module_name, plugin_path)
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                            
                            # Find and instantiate the Plugin class
                            for attribute_name in dir(module):
                                attribute = getattr(module, attribute_name)
                                if isinstance(attribute, type) and attribute_name.endswith("Plugin"):
                                    import inspect
                                    try:
                                        plugin_instance = attribute()
                                        if hasattr(plugin_instance, 'register') and inspect.ismethod(plugin_instance.register):
                                            plugin_instance.register(subparsers, context)
                                    except Exception as e:
                                        print(f"Failed to register plugin {module_name}: {e}")
                    except Exception as e:
                        print(f"Failed to load plugin {filename}: {e}")
