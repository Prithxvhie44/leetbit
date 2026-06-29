from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote


def build_github_remote_url(repository: str | None, token: str | None = None) -> str | None:
    if not repository:
        return None
    repository = repository.strip()
    if repository.startswith(("http://", "https://", "git@")):
        return repository
    if "/" not in repository:
        raise ValueError("GITHUB_REPO must be a repository slug like owner/name or a full git URL")
    if token:
        return f"https://x-access-token:{quote(token, safe='')}@github.com/{repository}.git"
    return f"https://github.com/{repository}.git"


@dataclass(slots=True)
class GitRepositoryManager:
    repository_path: Path
    branch: str = "main"
    remote_url: str | None = None

    def ensure_repository(self) -> None:
        self.repository_path.mkdir(parents=True, exist_ok=True)

        try:
            from git import Repo
        except ImportError:
            return

        git_dir = self.repository_path / ".git"
        repo = Repo.init(self.repository_path) if not git_dir.exists() else Repo(self.repository_path)

        if self.remote_url:
            if "origin" in repo.remotes:
                repo.remote("origin").set_url(self.remote_url)
            else:
                repo.create_remote("origin", self.remote_url)

        with repo.config_writer() as config_writer:
            config_writer.set_value("user", "name", "Leetbit")
            config_writer.set_value("user", "email", "leetbit@users.noreply.github.com")

    def commit_and_push(self, message: str) -> str | None:
        try:
            from git import Repo
        except ImportError:
            return None

        self.ensure_repository()
        repo = Repo(self.repository_path)
        repo.git.add(A=True)
        commit = None
        if repo.is_dirty(untracked_files=True):
            commit = repo.index.commit(message)
        elif repo.head.is_valid():
            commit = repo.head.commit

        if self.remote_url and repo.remotes:
            try:
                repo.remotes.origin.push(refspec=f"HEAD:refs/heads/{self.branch}")
            except Exception:
                pass
        return getattr(commit, "hexsha", None)
