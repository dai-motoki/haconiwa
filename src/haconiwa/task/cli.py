import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

from ..task.worktree import WorktreeManager
from ..core.config import Config
from ..core.logging import get_logger

task_app = typer.Typer(help="タスク管理コマンド (開発中)")
console = Console()
logger = get_logger(__name__)

@task_app.command()
def new(
    name: str = typer.Argument(..., help="Task name"),
    description: str = typer.Option(None, "--desc", "-d", help="Task description"),
    priority: int = typer.Option(1, "--priority", "-p", help="Task priority (1-5)"),
):
    """Create a new task with git worktree"""
    try:
        config = Config("config.yaml")
        worktree = WorktreeManager(config)
        worktree_path = worktree.create_worktree(name, f"task-{name}")
        console.print(f"✨ Created task: [bold green]{name}[/]")
        console.print(f"📁 Worktree path: {worktree_path}")
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise typer.Exit(1)

@task_app.command()
def assign(
    task_id: str = typer.Argument(..., help="Task ID to assign"),
    agent_id: str = typer.Argument(..., help="Agent ID to assign to"),
):
    """Assign task to an AI agent"""
    try:
        console.print(f"🔗 Assigned task [bold]{task_id}[/] to agent [bold]{agent_id}[/]")
        # Implementation would store assignment in database/config
    except Exception as e:
        logger.error(f"Failed to assign task: {e}")
        raise typer.Exit(1)

@task_app.command()
def show(
    task_id: Optional[str] = typer.Argument(None, help="Task ID to show details"),
    all: bool = typer.Option(False, "--all", "-a", help="Show all tasks"),
):
    """Show task details and progress"""
    try:
        config = Config("config.yaml")
        worktree = WorktreeManager(config)
        
        if task_id:
            status = worktree.get_worktree_status(task_id)
            table = Table(title=f"Task Details: {task_id}")
            table.add_column("Property", style="cyan")
            table.add_column("Value")
            
            for key, value in status.items():
                table.add_row(key, str(value))
            console.print(table)
        else:
            worktrees = worktree.list_worktrees()
            table = Table(title="Tasks Overview")
            table.add_column("ID", style="cyan")
            table.add_column("Worktree")
            table.add_column("Branch")
            
            for wt in worktrees:
                table.add_row(
                    wt.get("worktree", "").split("/")[-1],
                    wt.get("worktree", ""),
                    wt.get("branch", "")
                )
            console.print(table)
    except Exception as e:
        logger.error(f"Failed to show task(s): {e}")
        raise typer.Exit(1)

@task_app.command()
def done(
    task_id: str = typer.Argument(..., help="Task ID to mark as completed"),
    merge: bool = typer.Option(True, "--no-merge", help="Merge worktree changes"),
):
    """Mark task as completed and cleanup worktree"""
    try:
        config = Config("config.yaml")
        worktree = WorktreeManager(config)
        
        with Progress() as progress:
            task = progress.add_task("Completing task...", total=100)
            worktree.remove_worktree(task_id)
            progress.update(task, completed=100)
        console.print(f"✅ Completed task: [bold green]{task_id}[/]")
    except Exception as e:
        logger.error(f"Failed to complete task: {e}")
        raise typer.Exit(1)

@task_app.command()
def prune(
    force: bool = typer.Option(False, "--force", "-f", help="Force delete orphaned worktrees"),
):
    """Cleanup orphaned worktrees"""
    try:
        config = Config("config.yaml")
        worktree = WorktreeManager(config)
        cleaned = worktree.cleanup_stale_worktrees()
        
        if not cleaned:
            console.print("✨ No orphaned worktrees found")
            return

        console.print(f"🧹 Cleaned up {len(cleaned)} orphaned worktrees: {', '.join(cleaned)}")
    except Exception as e:
        logger.error(f"Failed to prune worktrees: {e}")
        raise typer.Exit(1)

if __name__ == "__main__":
    task_app()