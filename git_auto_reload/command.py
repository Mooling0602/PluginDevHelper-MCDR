from mcdreforged.api.all import (
    PluginServerInterface,
    # CommandSource,
    # CommandContext,
    Literal,
)


main_command = Literal(["!!gar", "!!git_auto_reload"]).runs(
    lambda src: src.reply("Main command.")
)


def register(s: PluginServerInterface):
    s.register_command(main_command)

