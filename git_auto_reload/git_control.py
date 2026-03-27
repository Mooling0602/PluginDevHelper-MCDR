## git command impl, use subprocess
# - check updates: `git fetch`
# - download updates: `git pull`
# - apply changes(ignore here): reload in MCDR
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from returns.result import Result, ResultE, Success, safe


@dataclass(frozen=True)
class UpdateInfo:
    """Carries update availability info after a successful fetch."""

    local_commit: str
    remote_commit: str
    behind_count: int

    @property
    def has_updates(self) -> bool:
        return self.local_commit != self.remote_commit and self.behind_count > 0


@safe(
    exceptions=(
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
        OSError,
    )
)
def _run_git(
    args: list[str], cwd: Path, timeout: int = 30
) -> subprocess.CompletedProcess[str]:
    """
    Run a git command in the given directory.

    Uses check=True so non-zero exit codes raise CalledProcessError,
    which @safe wraps into Failure.

    :param args: git subcommand and arguments, e.g. ["fetch", "origin"]
    :param cwd: working directory (local repo path)
    :param timeout: command timeout in seconds
    :return: ResultE[CompletedProcess[str]]
    """
    return subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=True,
    )


@safe(exceptions=(ValueError,))
def _parse_int(s: str) -> int:
    """Safely parse an integer string, wrapping ValueError into Failure."""
    return int(s)


def _get_commit_hash(cwd: Path, ref: str = "HEAD") -> ResultE[str]:
    """
    Get the commit hash for a given ref.

    :param cwd: working directory (local repo path)
    :param ref: git ref, e.g. "HEAD" or "origin/main"
    :return: ResultE[str] commit hash
    """
    return _run_git(["rev-parse", ref], cwd=cwd).map(lambda p: p.stdout.strip())


def _get_behind_count(cwd: Path, branch: str, remote: str = "origin") -> ResultE[int]:
    """
    Get the number of commits the local branch is behind its remote counterpart.

    :param cwd: working directory
    :param branch: local branch name
    :param remote: remote name
    :return: ResultE[int] number of commits behind
    """
    remote_ref = f"{remote}/{branch}"
    return _run_git(["rev-list", "--count", f"HEAD..{remote_ref}"], cwd=cwd).bind(
        lambda p: _parse_int(p.stdout.strip())
    )


def _get_effective_branch(cwd: Path, branch: Optional[str]) -> ResultE[str]:
    """
    Resolve the effective branch name.

    Returns the provided branch directly, or auto-detects from HEAD if None.
    """
    if branch is not None:
        return Success(branch)
    return _run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd).map(
        lambda p: p.stdout.strip()
    )


def _build_update_info(cwd: Path, remote: str, branch: str) -> ResultE[UpdateInfo]:
    """
    Collect local commit, remote commit and behind-count, then assemble UpdateInfo.

    Uses Result.do() so the first Failure short-circuits the whole expression.
    """
    return Result.do(
        UpdateInfo(
            local_commit=local,
            remote_commit=remote_c,
            behind_count=count,
        )
        for local in _get_commit_hash(cwd, "HEAD")
        for remote_c in _get_commit_hash(cwd, f"{remote}/{branch}")
        for count in _get_behind_count(cwd, branch, remote)
    )


def fetch(
    local_dir: Path,
    remote: str = "origin",
    branch: Optional[str] = None,
    timeout: int = 30,
) -> ResultE[UpdateInfo]:
    """
    Fetch updates from remote and check whether there are new commits.

    Runs `git fetch <remote> [<branch>]`, then compares local HEAD with
    the remote tracking ref to determine if updates are available.

    :param local_dir: path to the local git repository
    :param remote: remote name, default "origin"
    :param branch: branch to fetch; if None the current branch is auto-detected
    :param timeout: git command timeout in seconds
    :return: ResultE[UpdateInfo] — Success(UpdateInfo) or Failure(Exception)
    """
    fetch_args = ["fetch", remote]
    if branch:
        fetch_args.append(branch)

    return (
        _run_git(fetch_args, cwd=local_dir, timeout=timeout)
        .bind(lambda _: _get_effective_branch(local_dir, branch))
        .bind(
            lambda effective_branch: _build_update_info(
                local_dir, remote, effective_branch
            )
        )
    )


def pull(
    local_dir: Path,
    remote: str = "origin",
    branch: Optional[str] = None,
    timeout: int = 60,
) -> ResultE[str]:
    """
    Pull (download and merge) updates from remote.

    Runs `git pull <remote> [<branch>]`.

    :param local_dir: path to the local git repository
    :param remote: remote name, default "origin"
    :param branch: branch to pull; if None git uses the tracking config
    :param timeout: git command timeout in seconds
    :return: ResultE[str] — Success(stdout) or Failure(Exception)
    """
    pull_args = ["pull", remote]
    if branch:
        pull_args.append(branch)

    return _run_git(pull_args, cwd=local_dir, timeout=timeout).map(
        lambda p: p.stdout.strip()
    )
