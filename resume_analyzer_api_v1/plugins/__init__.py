import os
import importlib

def load_all_plugins():
    for file in os.listdir(os.path.dirname(__file__)):
        if file.endswith(".py") and file != "__init__.py":
            module_name = f"plugins.{file[:-3]}"
            importlib.import_module(module_name)
