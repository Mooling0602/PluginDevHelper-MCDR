from dataclasses import dataclass
from pathlib import Path

from mcdreforged.api.all import Serializable


# Load from repos.yml
class GitRepoInfo(Serializable):
    plugin_id: str  # used to check in MCDR plugin system
    local_dir: str  # optional, stores the plugin code, used to cwd
    remote_url: str  # if .git not in local_dir, necessary
    branch: str  # if .git not in local_dir, necessary
    is_linked: bool  # necessary, see https://docs.mcdreforged.com/en/latest/plugin_dev/plugin_format.html#linked-directory-plugin
    do_packaging: bool  # default is False, if True, will package the plugin use `mcdreforged pack`


# Used to run git options
@dataclass
class PureGitRepo(Serializable):
    plugin_id: str  # necessary
    local_dir: Path  # necessary


# Used to load and cache git repos data
class GitRepoList(Serializable):
    git_repos: list[GitRepoInfo]
