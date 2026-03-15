from mcdreforged.api.all import PluginServerInterface


def on_load(s: PluginServerInterface, _):
    s.logger.info("PluginDevHelper loaded.")


def on_unload(s: PluginServerInterface, _):
    s.logger.info("PluginDevHelper unloaded.")