"""
Output Formatter Implementation

Handles formatting of scan results into various output formats
including text, JSON, YAML, and summary formats.
"""

import json
import yaml
from typing import Any, Dict, List, Union
from datetime import datetime
from pathlib import Path

class OutputFormatter:
    """Formats scan results for different output types"""
    
    def __init__(self):
        self.format_handlers = {
            'text': self._format_text,
            'json': self._format_json,
            'yaml': self._format_yaml,
            'summary': self._format_summary,
            'table': self._format_table,
            'tree': self._format_tree
        }
    
    def format(self, data: Any, output_format: str) -> str:
        """Format data according to specified output format"""
        handler = self.format_handlers.get(output_format, self._format_text)
        return handler(data)
    
    def _format_text(self, data: Any) -> str:
        """Format as human-readable text"""
        if isinstance(data, dict):
            return self._dict_to_text(data)
        elif isinstance(data, list):
            return self._list_to_text(data)
        else:
            return str(data)
    
    def _dict_to_text(self, data: Dict[str, Any], indent: int = 0) -> str:
        """Convert dictionary to formatted text"""
        lines = []
        indent_str = "  " * indent
        
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{indent_str}{key}:")
                lines.append(self._dict_to_text(value, indent + 1))
            elif isinstance(value, list):
                lines.append(f"{indent_str}{key}:")
                for item in value:
                    if isinstance(item, dict):
                        lines.append(self._dict_to_text(item, indent + 1))
                    else:
                        lines.append(f"{indent_str}  - {item}")
            else:
                lines.append(f"{indent_str}{key}: {value}")
        
        return "\n".join(lines)
    
    def _list_to_text(self, data: List[Any]) -> str:
        """Convert list to formatted text"""
        lines = []
        for item in data:
            if isinstance(item, dict):
                lines.append(self._dict_to_text(item))
                lines.append("")  # Empty line between items
            else:
                lines.append(f"- {item}")
        
        return "\n".join(lines)
    
    def _format_json(self, data: Any) -> str:
        """Format as JSON"""
        return json.dumps(data, indent=2, default=str)
    
    def _format_yaml(self, data: Any) -> str:
        """Format as YAML"""
        return yaml.dump(data, default_flow_style=False, allow_unicode=True)
    
    def _format_summary(self, data: Any) -> str:
        """Format as a concise summary"""
        if not isinstance(data, dict):
            return str(data)
        
        lines = ["=" * 50]
        
        # Handle model search results
        if 'model_name' in data:
            lines.append(f"Model Search: {data['model_name']}")
            lines.append("=" * 50)
            lines.append(f"Total files found: {data.get('total_files', 0)}")
            
            if 'matches' in data:
                lines.append("\nMatches by category:")
                for category, files in data['matches'].items():
                    lines.append(f"  {category}: {len(files)} files")
        
        # Handle content search results
        elif 'pattern' in data and 'matches' in data:
            lines.append(f"Content Search: {data['pattern']}")
            lines.append("=" * 50)
            lines.append(f"Total matches: {data.get('total_matches', 0)}")
            lines.append(f"Files searched: {data.get('files_searched', 0)}")
            
            if data['matches']:
                lines.append("\nTop matches:")
                for match in data['matches'][:5]:
                    lines.append(f"  {match['file']}:{match['line_number']}")
        
        # Handle analysis results
        elif 'categories' in data and 'providers' in data:
            lines.append("Model Analysis Summary")
            lines.append("=" * 50)
            lines.append(f"Base path: {data.get('base_path', 'Unknown')}")
            lines.append(f"Total models: {data.get('total_models', 0)}")
            
            if data.get('total_size', 0) > 0:
                size_gb = data['total_size'] / (1024 ** 3)
                lines.append(f"Total size: {size_gb:.2f} GB")
            
            if 'insights' in data:
                lines.append("\nInsights:")
                for insight in data['insights']:
                    lines.append(f"  • {insight}")
        
        # Handle list results
        elif isinstance(data, list) and data:
            lines.append(f"Results: {len(data)} items")
            lines.append("=" * 50)
            for i, item in enumerate(data[:10], 1):
                if isinstance(item, dict):
                    name = item.get('name', item.get('path', 'Unknown'))
                    lines.append(f"{i}. {name}")
                else:
                    lines.append(f"{i}. {item}")
            
            if len(data) > 10:
                lines.append(f"... and {len(data) - 10} more")
        
        lines.append("=" * 50)
        return "\n".join(lines)
    
    def _format_table(self, data: Any) -> str:
        """Format as ASCII table"""
        if not isinstance(data, (list, dict)):
            return str(data)
        
        # Convert dict to list of items
        if isinstance(data, dict) and 'matches' not in data:
            data = [{'key': k, 'value': v} for k, v in data.items()]
        
        # Handle different data structures
        if isinstance(data, dict) and 'matches' in data:
            # Model search results
            rows = []
            for category, files in data['matches'].items():
                for file in files:
                    rows.append({
                        'Category': category,
                        'File': file['name'],
                        'Path': file['path'],
                        'Type': file['type']
                    })
            return self._create_table(rows)
        
        elif isinstance(data, list) and data:
            # List of models or other items
            if isinstance(data[0], dict):
                return self._create_table(data)
            else:
                # Simple list
                return "\n".join(f"• {item}" for item in data)
        
        return str(data)
    
    def _create_table(self, rows: List[Dict[str, Any]]) -> str:
        """Create ASCII table from rows"""
        if not rows:
            return "No data"
        
        # Get column names
        columns = list(rows[0].keys())
        
        # Calculate column widths
        widths = {}
        for col in columns:
            widths[col] = max(
                len(str(col)),
                max(len(str(row.get(col, ''))) for row in rows)
            )
        
        # Create header
        header = "| " + " | ".join(col.ljust(widths[col]) for col in columns) + " |"
        separator = "+" + "+".join("-" * (widths[col] + 2) for col in columns) + "+"
        
        # Create rows
        lines = [separator, header, separator]
        
        for row in rows:
            line = "| " + " | ".join(
                str(row.get(col, '')).ljust(widths[col]) for col in columns
            ) + " |"
            lines.append(line)
        
        lines.append(separator)
        return "\n".join(lines)
    
    def _format_tree(self, data: Any) -> str:
        """Format as tree structure"""
        if not isinstance(data, dict):
            return str(data)
        
        lines = []
        
        def build_tree(node: Dict[str, Any], prefix: str = "", is_last: bool = True):
            """Recursively build tree representation"""
            items = [(k, v) for k, v in node.items() if k != '__files__']
            files = node.get('__files__', [])
            
            # Add directories
            for i, (key, value) in enumerate(items):
                is_last_item = i == len(items) - 1 and not files
                
                connector = "└── " if is_last_item else "├── "
                lines.append(f"{prefix}{connector}{key}/")
                
                if isinstance(value, dict):
                    extension = "    " if is_last_item else "│   "
                    build_tree(value, prefix + extension, is_last_item)
            
            # Add files
            for i, file_info in enumerate(files):
                is_last_file = i == len(files) - 1
                connector = "└── " if is_last_file else "├── "
                
                if isinstance(file_info, dict):
                    name = file_info.get('name', 'Unknown')
                    size = file_info.get('size', 0)
                    size_str = self._format_size(size)
                    lines.append(f"{prefix}{connector}{name} ({size_str})")
                else:
                    lines.append(f"{prefix}{connector}{file_info}")
        
        build_tree(data)
        return "\n".join(lines)
    
    def _format_size(self, size: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"