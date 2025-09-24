# plugin_registry.py

PLUGIN_REGISTRY = {}

def register_plugin(name):
    def decorator(func):
        PLUGIN_REGISTRY[name] = func
        return func
    return decorator
