"""Simplified Claude Code SDK parallel development functionality."""

import asyncio
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

# Try to load dotenv if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Create typer app for parallel-dev subcommands
parallel_dev_app = typer.Typer(
    name="parallel-dev",
    help="AI-powered parallel development tools"
)

console = Console()


class SimpleParallelDevManager:
    """Simplified manager for parallel development operations using CLI directly."""
    
    def __init__(self):
        self.results_dir = Path("./parallel-dev-results")
        self.results_dir.mkdir(exist_ok=True)
        self.task_history = []
        self.active_tasks = {}
        
    async def process_file_cli(
        self,
        file_path: str,
        prompt: str,
        task_id: str,
        max_turns: int = 5,
        timeout: int = 60
    ) -> Dict[str, any]:
        """Process a single file using Claude CLI directly."""
        start_time = datetime.now()
        
        # Construct command - use full path to claude
        claude_path = "/Users/motokidaisuke/.claude/local/claude"
        
        # Get absolute path
        import os
        abs_file_path = os.path.abspath(file_path)
        
        cmd = [
            claude_path, "-p",
            f"Please edit the file {abs_file_path} with the following instructions: {prompt}",
            "--max-turns", str(max_turns)
        ]
        
        try:
            # Track active task
            self.active_tasks[task_id] = {
                "file": file_path,
                "prompt": prompt,
                "status": "running",
                "start_time": start_time
            }
            
            # Run command
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", "")}
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                raise TimeoutError(f"Task timed out after {timeout} seconds")
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Mark as completed
            self.active_tasks[task_id]["status"] = "completed"
            
            if proc.returncode == 0:
                return {
                    "task_id": task_id,
                    "file": file_path,
                    "prompt": prompt,
                    "status": "success",
                    "output": stdout.decode('utf-8'),
                    "duration": duration,
                    "timestamp": start_time.isoformat()
                }
            else:
                return {
                    "task_id": task_id,
                    "file": file_path,
                    "prompt": prompt,
                    "status": "error",
                    "error": stderr.decode('utf-8') or stdout.decode('utf-8'),
                    "duration": duration,
                    "timestamp": start_time.isoformat()
                }
                
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Mark as failed
            if task_id in self.active_tasks:
                self.active_tasks[task_id]["status"] = "failed"
            
            return {
                "task_id": task_id,
                "file": file_path,
                "prompt": prompt,
                "status": "error",
                "error": str(e),
                "duration": duration,
                "timestamp": start_time.isoformat()
            }
    
    async def parallel_execute_simple(
        self,
        files_and_prompts: List[Tuple[str, str]],
        max_concurrent: int = 3,
        timeout: int = 60,
        max_turns: int = 5
    ) -> List[Dict[str, any]]:
        """Execute multiple file edits in parallel using CLI."""
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(file_path: str, prompt: str, idx: int):
            async with semaphore:
                task_id = f"task-{idx:03d}"
                return await self.process_file_cli(
                    file_path, prompt, task_id, max_turns, timeout
                )
        
        # Create tasks
        tasks = [
            asyncio.create_task(
                process_with_semaphore(file_path, prompt, idx)
            )
            for idx, (file_path, prompt) in enumerate(files_and_prompts)
        ]
        
        # Execute all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error results
        final_results = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append({
                    "task_id": f"task-{idx:03d}",
                    "file": files_and_prompts[idx][0],
                    "prompt": files_and_prompts[idx][1],
                    "status": "error",
                    "error": str(result),
                    "duration": 0
                })
            else:
                final_results.append(result)
        
        # Clear active tasks
        self.active_tasks.clear()
        
        # Store in history
        self.task_history.extend(final_results)
        
        return final_results
    
    def save_results(self, results: List[Dict[str, any]], session_id: str):
        """Save results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save summary
        summary_file = self.results_dir / f"summary_{timestamp}.json"
        summary = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "total_tasks": len(results),
            "successful": sum(1 for r in results if r.get("status") == "success"),
            "failed": sum(1 for r in results if r.get("status") == "error"),
            "results": results
        }
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Save individual logs
        logs_dir = self.results_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        for result in results:
            file_name = Path(result["file"]).name.replace("/", "_")
            log_file = logs_dir / f"{file_name}_{timestamp}.log"
            
            with open(log_file, 'w') as f:
                f.write(f"File: {result['file']}\n")
                f.write(f"Prompt: {result['prompt']}\n")
                f.write(f"Status: {result['status']}\n")
                f.write(f"Duration: {result.get('duration', 'N/A')}s\n")
                f.write("\n" + "="*50 + "\n\n")
                
                if result["status"] == "success":
                    f.write("Output:\n")
                    f.write(result.get("output", ""))
                else:
                    f.write(f"Error: {result.get('error', 'Unknown error')}\n")
        
        return summary_file


# Import os module
import os

# Replace the original manager with the simple one
manager = SimpleParallelDevManager()


@parallel_dev_app.command("claude")
def claude_parallel(
    files: Optional[str] = typer.Option(None, "-f", "--files", help="Comma-separated file paths"),
    prompts: Optional[str] = typer.Option(None, "-p", "--prompts", help="Comma-separated prompts"),
    file_list: Optional[Path] = typer.Option(None, "--file-list", help="File containing paths (one per line)"),
    prompt_file: Optional[Path] = typer.Option(None, "--prompt-file", help="File containing prompts (one per line)"),
    from_yaml: Optional[Path] = typer.Option(None, "--from-yaml", help="YAML configuration file"),
    max_concurrent: int = typer.Option(3, "-m", "--max-concurrent", help="Maximum concurrent executions"),
    timeout: int = typer.Option(60, "-t", "--timeout", help="Timeout per task in seconds"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be executed"),
    output_dir: Optional[Path] = typer.Option(None, "-o", "--output-dir", help="Output directory"),
    max_turns: int = typer.Option(5, "--max-turns", help="Maximum turns for Claude")
):
    """Execute parallel file edits using Claude Code SDK (simplified version)."""
    
    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        console.print("[red]❌ ANTHROPIC_API_KEY environment variable not set[/red]")
        raise typer.Exit(1)
    
    # Parse inputs
    files_and_prompts = []
    
    if from_yaml:
        # Load from YAML
        if not from_yaml.exists():
            console.print(f"[red]❌ YAML file not found: {from_yaml}[/red]")
            raise typer.Exit(1)
        
        import yaml
        with open(from_yaml, 'r') as f:
            config = yaml.safe_load(f)
        
        if config.get("provider") != "claude":
            console.print(f"[red]❌ Unsupported provider: {config.get('provider')}[/red]")
            raise typer.Exit(1)
        
        for task in config.get("tasks", []):
            files_and_prompts.append((task["file"], task["prompt"]))
        
        # Override options from YAML if present
        options = config.get("options", {})
        max_concurrent = options.get("max_concurrent", max_concurrent)
        timeout = options.get("timeout", timeout)
    
    elif files and prompts:
        # Parse comma-separated lists
        file_list = [f.strip() for f in files.split(",")]
        prompt_list = [p.strip() for p in prompts.split(",")]
        
        if len(file_list) != len(prompt_list):
            console.print("[red]❌ Number of files and prompts must match[/red]")
            raise typer.Exit(1)
        
        files_and_prompts = list(zip(file_list, prompt_list))
    
    elif file_list and prompt_file:
        # Read from files
        if not file_list.exists() or not prompt_file.exists():
            console.print("[red]❌ File list or prompt file not found[/red]")
            raise typer.Exit(1)
        
        with open(file_list, 'r') as f:
            file_paths = [line.strip() for line in f if line.strip()]
        
        with open(prompt_file, 'r') as f:
            prompt_list = [line.strip() for line in f if line.strip()]
        
        if len(file_paths) != len(prompt_list):
            console.print("[red]❌ Number of files and prompts must match[/red]")
            raise typer.Exit(1)
        
        files_and_prompts = list(zip(file_paths, prompt_list))
    
    else:
        console.print("[red]❌ Must specify either --files/-f and --prompts/-p, --file-list and --prompt-file, or --from-yaml[/red]")
        raise typer.Exit(1)
    
    # Validate inputs
    if not files_and_prompts:
        console.print("[red]❌ No files to process[/red]")
        raise typer.Exit(1)
    
    if len(files_and_prompts) > 10:
        console.print(f"[yellow]⚠️ Processing {len(files_and_prompts)} files (max recommended: 10)[/yellow]")
    
    # Display summary
    console.print(f"\n[bold]📋 Task Summary:[/bold]")
    console.print(f"- Total files: {len(files_and_prompts)}")
    console.print(f"- Max concurrent: {max_concurrent}")
    console.print(f"- Timeout per task: {timeout}s")
    console.print(f"- Max turns: {max_turns}")
    
    if dry_run:
        console.print("\n[yellow]🔍 Dry run - Tasks that would be executed:[/yellow]")
        for i, (file, prompt) in enumerate(files_and_prompts[:5]):
            console.print(f"  {i+1}. {file}: {prompt}")
        if len(files_and_prompts) > 5:
            console.print(f"  ... and {len(files_and_prompts) - 5} more tasks")
        return
    
    # Confirm execution
    if not typer.confirm(f"\nExecute {len(files_and_prompts)} parallel edits?"):
        console.print("[red]❌ Operation cancelled[/red]")
        raise typer.Exit(0)
    
    # Execute parallel tasks
    console.print(f"\n[bold green]🚀 Starting parallel Claude execution (simplified)...[/bold green]")
    
    # Run async execution
    results = asyncio.run(
        manager.parallel_execute_simple(
            files_and_prompts,
            max_concurrent=max_concurrent,
            timeout=timeout,
            max_turns=max_turns
        )
    )
    
    # Display results
    success_count = sum(1 for r in results if r["status"] == "success")
    error_count = sum(1 for r in results if r["status"] == "error")
    
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"✅ Success: {success_count}/{len(results)}")
    if error_count > 0:
        console.print(f"❌ Failed: {error_count}/{len(results)}")
    
    # Save results
    if output_dir:
        manager.results_dir = output_dir
    
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_file = manager.save_results(results, session_id)
    console.print(f"\n📁 Results saved to: {summary_file}")
    
    # Exit with error if any failures
    if error_count > 0:
        raise typer.Exit(1)


@parallel_dev_app.command("status")
def status():
    """Show status of active parallel development tasks."""
    if not manager.active_tasks:
        console.print("No active tasks")
        return
    
    table = Table(title="Active Tasks")
    table.add_column("Task ID", style="cyan")
    table.add_column("File", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Duration", style="magenta")
    
    for task_id, task_info in manager.active_tasks.items():
        duration = (datetime.now() - task_info["start_time"]).total_seconds()
        table.add_row(
            task_id,
            task_info["file"],
            task_info["status"],
            f"{duration:.1f}s"
        )
    
    console.print(table)


@parallel_dev_app.command("history")
def history(
    limit: int = typer.Option(10, "--limit", help="Number of entries to show")
):
    """Show execution history."""
    if not manager.task_history:
        console.print("No execution history")
        return
    
    # Get recent entries
    recent = manager.task_history[-limit:]
    
    table = Table(title=f"Recent Executions (showing {len(recent)} of {len(manager.task_history)})")
    table.add_column("Timestamp", style="cyan")
    table.add_column("File", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Duration", style="magenta")
    
    for entry in reversed(recent):
        timestamp = entry.get("timestamp", "N/A")
        if timestamp != "N/A":
            # Format timestamp
            dt = datetime.fromisoformat(timestamp)
            timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
        
        status_style = "green" if entry["status"] == "success" else "red"
        table.add_row(
            timestamp,
            entry["file"],
            f"[{status_style}]{entry['status']}[/{status_style}]",
            f"{entry.get('duration', 0):.1f}s"
        )
    
    console.print(table)


@parallel_dev_app.command("cancel")
def cancel(
    task_id: str = typer.Argument(..., help="Task ID to cancel")
):
    """Cancel a running task (placeholder for future implementation)."""
    console.print(f"[yellow]⚠️ Task cancellation not yet implemented[/yellow]")
    console.print(f"Task ID: {task_id}")