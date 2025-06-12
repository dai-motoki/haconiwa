import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from git import Repo, GitCommandError

from haconiwa.core.config import Config


class WorktreeManager:
    def __init__(self, config: Config):
        self.config = config
        self.repo_path = Path(config.get("git.repo_path"))
        self.worktree_base = Path(config.get("git.worktree_base"))
        self.repo = Repo(self.repo_path)
        self.default_branch = config.get("git.default_branch", "main")
        self._init_worktree_base()

    def _init_worktree_base(self):
        self.worktree_base.mkdir(parents=True, exist_ok=True)

    def create_worktree(self, task_id: str, branch_name: str) -> Path:
        worktree_path = self.worktree_base / task_id
        if worktree_path.exists():
            raise ValueError(f"Worktree already exists: {task_id}")

        self.repo.git.worktree("add", str(worktree_path), "-b", branch_name)
        return worktree_path

    def remove_worktree(self, task_id: str, force: bool = False) -> None:
        worktree_path = self.worktree_base / task_id
        if not worktree_path.exists():
            return

        try:
            self.repo.git.worktree("remove", str(worktree_path), "--force" if force else "")
            if worktree_path.exists():
                shutil.rmtree(worktree_path)
        except GitCommandError as e:
            if not force:
                raise
            shutil.rmtree(worktree_path)

    def list_worktrees(self) -> List[Dict[str, str]]:
        result = []
        for line in self.repo.git.worktree("list", "--porcelain").split("\n\n"):
            if not line.strip():
                continue
            info = {}
            for item in line.split("\n"):
                if " " in item:
                    key, value = item.split(" ", 1)
                    info[key] = value
            result.append(info)
        return result

    def commit_changes(self, task_id: str, message: str, author: Optional[str] = None) -> str:
        worktree_path = self.worktree_base / task_id
        worktree_repo = Repo(worktree_path)
        
        if not worktree_repo.is_dirty(untracked_files=True):
            return None

        worktree_repo.git.add(".")
        commit = worktree_repo.index.commit(
            message,
            author=author or self.config.get("git.default_author")
        )
        return str(commit)

    def push_changes(self, task_id: str, remote: str = "origin") -> None:
        worktree_path = self.worktree_base / task_id
        worktree_repo = Repo(worktree_path)
        current_branch = worktree_repo.active_branch.name
        worktree_repo.git.push(remote, current_branch)

    def merge_branch(self, source_task: str, target_branch: Optional[str] = None) -> Tuple[bool, str]:
        if target_branch is None:
            target_branch = self.default_branch
            
        source_path = self.worktree_base / source_task
        source_repo = Repo(source_path)
        source_branch = source_repo.active_branch.name

        try:
            self.repo.git.checkout(target_branch)
            self.repo.git.merge(source_branch)
            return True, "Merge successful"
        except GitCommandError as e:
            return False, str(e)

    def resolve_conflicts(self, task_id: str, strategy: str = "ours") -> bool:
        worktree_path = self.worktree_base / task_id
        worktree_repo = Repo(worktree_path)

        try:
            if strategy == "ours":
                worktree_repo.git.checkout("--ours", ".")
            elif strategy == "theirs":
                worktree_repo.git.checkout("--theirs", ".")
            else:
                return False

            worktree_repo.git.add(".")
            worktree_repo.git.commit("--no-edit")
            return True
        except GitCommandError:
            return False

    def backup_worktree(self, task_id: str) -> Path:
        source_path = self.worktree_base / task_id
        backup_path = self.worktree_base / f"{task_id}_backup"
        
        if not source_path.exists():
            raise ValueError(f"Worktree not found: {task_id}")

        shutil.copytree(source_path, backup_path)
        return backup_path

    def restore_worktree(self, task_id: str, backup_path: Optional[Path] = None) -> None:
        if backup_path is None:
            backup_path = self.worktree_base / f"{task_id}_backup"

        target_path = self.worktree_base / task_id
        if not backup_path.exists():
            raise ValueError(f"Backup not found: {backup_path}")

        if target_path.exists():
            shutil.rmtree(target_path)
        shutil.copytree(backup_path, target_path)

    def sync_worktree(self, task_id: str) -> None:
        worktree_path = self.worktree_base / task_id
        worktree_repo = Repo(worktree_path)
        current_branch = worktree_repo.active_branch.name

        worktree_repo.git.fetch("origin")
        worktree_repo.git.rebase(f"origin/{current_branch}")

    def get_worktree_status(self, task_id: str) -> Dict[str, any]:
        worktree_path = self.worktree_base / task_id
        worktree_repo = Repo(worktree_path)
        
        return {
            "branch": worktree_repo.active_branch.name,
            "is_dirty": worktree_repo.is_dirty(untracked_files=True),
            "untracked_files": worktree_repo.untracked_files,
            "active_branch": worktree_repo.active_branch.name,
            "current_commit": str(worktree_repo.head.commit),
            "modified_files": [item.a_path for item in worktree_repo.index.diff(None)]
        }

    def cleanup_stale_worktrees(self) -> List[str]:
        cleaned = []
        for worktree in self.list_worktrees():
            path = Path(worktree.get("worktree", ""))
            if not path.exists() or not any(path.iterdir()):
                self.remove_worktree(path.name, force=True)
                cleaned.append(path.name)
        return cleaned