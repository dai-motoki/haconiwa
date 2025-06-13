"""
Scan command CLI implementation
"""

import typer
from pathlib import Path
from typing import Optional, List
import json
import yaml

from .scanner import ModelScanner
from .analyzer import ModelAnalyzer
from .formatter import OutputFormatter
from .comparator import ModelComparator
from .guide_generator import GuideGenerator
from .generate_parallel import ParallelYAMLGenerator

scan_app = typer.Typer(help="Universal AI model search and analysis")

@scan_app.command()
def model(
    model_name: str = typer.Argument(..., help="Model name to search for"),
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Base path to search in"),
    no_strip_prefix: bool = typer.Option(False, "--no-strip-prefix", help="Don't strip common prefixes"),
    format: str = typer.Option("text", "--format", "-f", help="Output format (text/json/yaml/tree)"),
    include_content: bool = typer.Option(False, "--include-content", help="Include file contents in results"),
    ignore: Optional[List[str]] = typer.Option(None, "--ignore", "-i", help="Patterns to ignore"),
    whitelist: Optional[List[str]] = typer.Option(None, "--whitelist", "-w", help="Patterns to whitelist")
):
    """Search for AI model by name with prefix stripping support"""
    scanner = ModelScanner(
        base_path=path or Path.cwd(),
        strip_prefix=not no_strip_prefix,
        ignore_patterns=ignore,
        whitelist=whitelist
    )
    
    results = scanner.search_by_model_name(model_name, include_content=include_content)
    
    formatter = OutputFormatter()
    output = formatter.format_search_results(results, format)
    typer.echo(output)

@scan_app.command()
def content(
    pattern: str = typer.Argument(..., help="Regex pattern to search for"),
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Base path to search in"),
    type: Optional[List[str]] = typer.Option(None, "--type", "-t", help="File types to search (e.g., .py)"),
    context: int = typer.Option(2, "--context", "-c", help="Number of context lines"),
    ignore: Optional[List[str]] = typer.Option(None, "--ignore", "-i", help="Patterns to ignore")
):
    """Search for patterns in file contents"""
    scanner = ModelScanner(
        base_path=path or Path.cwd(),
        ignore_patterns=ignore
    )
    
    results = scanner.search_content(pattern, file_types=type, context_lines=context)
    
    # Format output
    typer.echo(f"pattern: {results['pattern']}")
    typer.echo("matches:")
    for match in results['matches']:
        typer.echo(f"  file: {match['file']}")
        typer.echo(f"  line_number: {match['line_number']}")
        typer.echo(f"  line: {match['line']}")
        if match.get('context'):
            typer.echo("  context:")
            for line in match['context']:
                typer.echo(f"    - {line}")
        typer.echo()

@scan_app.command()
def analyze(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Path to analyze"),
    category: Optional[str] = typer.Option(None, "--category", help="Filter by category"),
    show_structure: bool = typer.Option(False, "--show-structure", help="Show directory structure"),
    output_format: str = typer.Option("text", "--format", "-f", help="Output format")
):
    """Analyze AI model directory structure and categorization"""
    analyzer = ModelAnalyzer(base_path=path or Path.cwd())
    
    results = analyzer.analyze_directory(
        show_structure=show_structure,
        category_filter=category
    )
    
    formatter = OutputFormatter()
    output = formatter.format_analysis_results(results, output_format)
    typer.echo(output)

@scan_app.command()
def compare(
    models: List[str] = typer.Argument(..., help="Model names to compare (2 or more)"),
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Base path to search in"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    format: str = typer.Option("table", "--format", "-f", help="Output format")
):
    """Compare multiple AI models"""
    if len(models) < 2:
        typer.echo("Error: At least 2 models required for comparison", err=True)
        raise typer.Exit(1)
    
    comparator = ModelComparator(base_path=path or Path.cwd())
    
    results = comparator.compare_models(models)
    
    formatter = OutputFormatter()
    output_text = formatter.format_comparison_results(results, format)
    
    if output:
        output.write_text(output_text)
        typer.echo(f"Results saved to: {output}")
    else:
        typer.echo(output_text)

@scan_app.command()
def guide(
    model_name: str = typer.Argument(..., help="Model name to generate guide for"),
    type: str = typer.Option("development", "--type", "-t", 
                            help="Guide type (development/usage/integration/quickstart)"),
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Base path to search in"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path")
):
    """Generate development guide for specific AI model"""
    generator = GuideGenerator(base_path=path or Path.cwd())
    
    guide_text = generator.generate(model_name, guide_type=type)
    
    if output:
        output.write_text(guide_text)
        typer.echo(f"Guide saved to: {output}")
    else:
        typer.echo(guide_text)

@scan_app.command("list")
def list_models(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Base path to search in"),
    category: Optional[str] = typer.Option(None, "--category", help="Filter by category"),
    provider: Optional[str] = typer.Option(None, "--provider", help="Filter by provider"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format")
):
    """List all available AI models"""
    scanner = ModelScanner(base_path=path or Path.cwd())
    
    models = scanner.list_all_models(
        category=category,
        provider=provider
    )
    
    formatter = OutputFormatter()
    output = formatter.format_model_list(models, output_format)
    typer.echo(output)

@scan_app.command("generate-parallel-config")
def generate_parallel_config(
    source: Optional[str] = typer.Option(None, "--source", "-s", 
                                        help="Source: 'last-search', 'model:name', or file path"),
    action: str = typer.Option("refactor", "--action", "-a",
                              help="Action type: refactor, add_type_hints, add_tests, etc."),
    max_files: int = typer.Option(10, "--max-files", "-m", help="Maximum number of files"),
    output: Path = typer.Option("parallel-dev.yaml", "--output", "-o", help="Output YAML file"),
    example: bool = typer.Option(False, "--example", help="Generate example YAML"),
    migration: Optional[List[str]] = typer.Option(None, "--migration",
                                                  help="Generate migration YAML (old:new)"),
    pattern_fix: Optional[List[str]] = typer.Option(None, "--pattern-fix",
                                                    help="Fix pattern (pattern:description)"),
    project_wide: Optional[str] = typer.Option(None, "--project-wide",
                                              help="Generate project-wide changes for file pattern"),
    exclude: Optional[List[str]] = typer.Option(None, "--exclude", "-e",
                                               help="Exclude patterns for project-wide"),
    prompt_file: Optional[Path] = typer.Option(None, "--prompt-file",
                                              help="File with custom prompts (file:prompt per line)")
):
    """Generate parallel development configuration YAML from scan results"""
    
    generator = ParallelYAMLGenerator(base_path=Path.cwd())
    
    # Handle different generation modes
    if example:
        # Generate example YAML
        config = generator.create_example_yaml()
        typer.echo("📝 Generated example parallel-dev.yaml")
    
    elif migration and len(migration) == 1 and ':' in migration[0]:
        # Migration mode
        old_model, new_model = migration[0].split(':', 1)
        scanner = ModelScanner(base_path=Path.cwd())
        
        # Find files containing old model
        results = scanner.search_by_model_name(old_model)
        files = []
        for category, file_list in results['matches'].items():
            for file_info in file_list:
                files.append(file_info['path'])
                if len(files) >= max_files:
                    break
        
        config = generator.generate_for_model_migration(old_model, new_model, files)
        typer.echo(f"🔄 Generated migration YAML: {old_model} → {new_model}")
    
    elif pattern_fix and len(pattern_fix) == 1 and ':' in pattern_fix[0]:
        # Pattern fix mode
        pattern, description = pattern_fix[0].split(':', 1)
        scanner = ModelScanner(base_path=Path.cwd())
        
        # Find files containing pattern
        results = scanner.search_content(pattern)
        files = [match['file'] for match in results['matches'][:max_files]]
        
        config = generator.generate_for_pattern_fix(pattern, description, files)
        typer.echo(f"🔧 Generated pattern fix YAML for: {pattern}")
    
    elif project_wide:
        # Project-wide mode
        config = generator.generate_project_wide(
            action=action,
            file_pattern=project_wide,
            exclude_patterns=exclude
        )
        typer.echo(f"🌍 Generated project-wide YAML for: {project_wide}")
    
    else:
        # Standard mode - from search results or model name
        custom_prompts = {}
        if prompt_file and prompt_file.exists():
            # Load custom prompts
            for line in prompt_file.read_text().splitlines():
                if ':' in line:
                    file_path, prompt = line.split(':', 1)
                    custom_prompts[file_path.strip()] = prompt.strip()
        
        if source and source.startswith('model:'):
            # Search for specific model
            model_name = source[6:]
            scanner = ModelScanner(base_path=Path.cwd())
            scan_results = scanner.search_by_model_name(model_name)
        elif source and Path(source).exists():
            # Load from file
            source_path = Path(source)
            if source_path.suffix in ['.json', '.yaml', '.yml']:
                with open(source_path, 'r') as f:
                    if source_path.suffix == '.json':
                        scan_results = json.load(f)
                    else:
                        scan_results = yaml.safe_load(f)
            else:
                typer.echo("Error: Source file must be JSON or YAML", err=True)
                raise typer.Exit(1)
        else:
            # Try to use last search results (would need to implement caching)
            typer.echo("📍 Using current directory analysis...")
            analyzer = ModelAnalyzer(base_path=Path.cwd())
            scan_results = analyzer.analyze_directory()
        
        config = generator.generate_from_scan_results(
            scan_results,
            action=action,
            max_files=max_files,
            custom_prompts=custom_prompts
        )
        typer.echo(f"✨ Generated parallel-dev YAML with {len(config['tasks'])} tasks")
    
    # Save YAML file
    saved_path = generator.save_yaml(config, output)
    typer.echo(f"💾 Saved to: {saved_path}")
    
    # Show preview
    typer.echo("\n📋 Preview:")
    typer.echo(f"Provider: {config['provider']}")
    typer.echo(f"Total tasks: {len(config['tasks'])}")
    if config['tasks']:
        typer.echo("\nFirst 3 tasks:")
        for i, task in enumerate(config['tasks'][:3], 1):
            typer.echo(f"{i}. {task['file']}")
            typer.echo(f"   → {task['prompt'][:80]}{'...' if len(task['prompt']) > 80 else ''}")
    
    typer.echo(f"\n✅ Generated YAML file is ready: {output}")

@scan_app.command()
def help():
    """Show detailed help for scan command"""
    help_text = """
🔍 Haconiwa Scan Command - AI Model Search & Analysis

The scan command provides comprehensive search and analysis capabilities for AI model
directories, supporting model name searching, file content searching, and various 
output formats.

COMMANDS:
  model         Search by model name (with automatic prefix stripping)
  content       Search file contents with regex
  list          List all available AI models
  analyze       Analyze directory structure and categorization
  compare       Compare multiple AI models
  guide         Generate development guide for specific model
  generate-parallel-config  Generate parallel development configuration YAML

EXAMPLES:
  # Search for a model
  haconiwa scan model gpt-4
  
  # Search with prefix
  haconiwa scan model claude-3-opus --no-strip-prefix
  
  # Search content
  haconiwa scan content "model.forward" --type .py --context 5
  
  # List models by provider
  haconiwa scan list --provider openai --format json
  
  # Analyze directory
  haconiwa scan analyze --show-structure
  
  # Compare models
  haconiwa scan compare gpt-4 claude-3-opus
  
  # Generate guide
  haconiwa scan guide gpt-4 --type quickstart --output guide.md
  
  # Generate parallel development configuration YAML
  haconiwa scan generate-parallel-config --source model:gpt-4 --action add_tests
  haconiwa scan generate-parallel-config --example
  haconiwa scan generate-parallel-config --migration gpt-3.5:gpt-4 --max-files 20
  haconiwa scan generate-parallel-config --project-wide "*.py" --action add_type_hints

For more information on a specific command, use:
  haconiwa scan <command> --help
    """
    typer.echo(help_text)