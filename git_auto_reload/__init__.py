from mcdreforged.api.all import PluginServerInterface
from git_auto_reload.command import register


def on_load(s: PluginServerInterface, _):
    register(s)
    s.logger.info("PluginDevHelper loaded.")


def on_unload(s: PluginServerInterface):
    s.logger.info("PluginDevHelper unloaded.")
