from plugin_registry import register_plugin

@register_plugin("cloudmatcher")
def run():
    print("📱 cloudmatcher plugin executed")
