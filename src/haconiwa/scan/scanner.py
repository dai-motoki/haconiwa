"""
Model Scanner Core Implementation

Handles the core scanning functionality for AI models,
including model name searching, file content searching,
and directory traversal with filtering.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import fnmatch
from collections import defaultdict

class ModelScanner:
    """Core scanner for AI model directories"""
    
    def __init__(self, 
                 base_path: Path,
                 strip_prefix: bool = True,
                 ignore_patterns: Optional[List[str]] = None,
                 whitelist: Optional[List[str]] = None):
        self.base_path = Path(base_path)
        self.strip_prefix = strip_prefix
        self.ignore_patterns = ignore_patterns or [
            "*.pyc", "__pycache__", ".git", ".venv", 
            "node_modules", "*.egg-info", ".pytest_cache"
        ]
        self.whitelist = whitelist or []
        
        # Common model name prefixes to strip
        self.model_prefixes = [
            "gpt-", "claude-", "llama-", "mistral-", "gemini-",
            "palm-", "anthropic-", "openai-", "meta-", "google-"
        ]
        
        # File type mappings
        self.file_type_mappings = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.md': 'markdown',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.txt': 'text',
            '.sh': 'shell',
            '.dockerfile': 'docker',
            '.toml': 'toml',
            '.ini': 'config',
            '.conf': 'config'
        }
    
    def _should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored"""
        path_str = str(path)
        
        # Check whitelist first
        if self.whitelist:
            whitelisted = any(
                fnmatch.fnmatch(path_str, pattern) or 
                pattern in path_str 
                for pattern in self.whitelist
            )
            if not whitelisted:
                return True
        
        # Check ignore patterns
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(path.name, pattern):
                return True
            if pattern in path_str:
                return True
        
        return False
    
    def _normalize_model_name(self, model_name: str) -> str:
        """Normalize model name by stripping common prefixes if enabled"""
        if not self.strip_prefix:
            return model_name.lower()
        
        normalized = model_name.lower()
        for prefix in self.model_prefixes:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
                break
        
        return normalized
    
    def search_by_model_name(self, 
                           model_name: str, 
                           include_content: bool = False) -> Dict[str, Any]:
        """Search for files and directories related to a model name"""
        normalized_name = self._normalize_model_name(model_name)
        results = {
            'model_name': model_name,
            'normalized_name': normalized_name,
            'matches': defaultdict(list),
            'total_files': 0,
            'categories': set()
        }
        
        # Search patterns
        patterns = [
            normalized_name,
            model_name.lower(),
            model_name.replace('-', '_'),
            normalized_name.replace('-', '_')
        ]
        
        for root, dirs, files in os.walk(self.base_path):
            root_path = Path(root)
            
            # Filter directories
            dirs[:] = [d for d in dirs if not self._should_ignore(root_path / d)]
            
            # Check directory names
            for pattern in patterns:
                if pattern in root_path.name.lower():
                    category = self._determine_category(root_path)
                    results['categories'].add(category)
                    
                    # Process files in matching directory
                    for file in files:
                        file_path = root_path / file
                        if not self._should_ignore(file_path):
                            file_info = self._get_file_info(file_path, include_content)
                            results['matches'][category].append(file_info)
                            results['total_files'] += 1
            
            # Check file names
            for file in files:
                file_path = root_path / file
                if self._should_ignore(file_path):
                    continue
                
                for pattern in patterns:
                    if pattern in file.lower():
                        category = self._determine_category(root_path)
                        results['categories'].add(category)
                        file_info = self._get_file_info(file_path, include_content)
                        results['matches'][category].append(file_info)
                        results['total_files'] += 1
                        break
        
        results['categories'] = list(results['categories'])
        results['matches'] = dict(results['matches'])
        return results
    
    def search_content(self, 
                      pattern: str, 
                      file_types: Optional[List[str]] = None,
                      context_lines: int = 2) -> Dict[str, Any]:
        """Search for pattern in file contents"""
        results = {
            'pattern': pattern,
            'matches': [],
            'total_matches': 0,
            'files_searched': 0
        }
        
        regex = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
        
        for file_path in self._iter_files(file_types):
            if self._should_ignore(file_path):
                continue
            
            results['files_searched'] += 1
            
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                lines = content.splitlines()
                
                for i, line in enumerate(lines):
                    if regex.search(line):
                        match_info = {
                            'file': str(file_path.relative_to(self.base_path)),
                            'line_number': i + 1,
                            'line': line.strip(),
                            'context': self._get_context(lines, i, context_lines)
                        }
                        results['matches'].append(match_info)
                        results['total_matches'] += 1
            
            except Exception:
                # Skip files that can't be read
                continue
        
        return results
    
    def list_all_models(self, 
                       category: Optional[str] = None,
                       provider: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all available models in the directory structure"""
        models = []
        model_dirs = defaultdict(lambda: {'files': [], 'categories': set()})
        
        for root, dirs, files in os.walk(self.base_path):
            root_path = Path(root)
            
            # Filter directories
            dirs[:] = [d for d in dirs if not self._should_ignore(root_path / d)]
            
            # Look for model-related directories
            if self._is_model_directory(root_path):
                model_name = self._extract_model_name(root_path)
                model_provider = self._extract_provider(root_path)
                model_category = self._determine_category(root_path)
                
                if category and model_category != category:
                    continue
                if provider and model_provider != provider:
                    continue
                
                for file in files:
                    file_path = root_path / file
                    if not self._should_ignore(file_path):
                        model_dirs[model_name]['files'].append(str(file_path))
                        model_dirs[model_name]['categories'].add(model_category)
                        model_dirs[model_name]['provider'] = model_provider
        
        # Convert to list format
        for model_name, info in model_dirs.items():
            models.append({
                'name': model_name,
                'provider': info.get('provider', 'Unknown'),
                'category': ', '.join(info['categories']),
                'file_count': len(info['files']),
                'files': info['files'][:5]  # First 5 files as sample
            })
        
        return sorted(models, key=lambda x: (x['provider'], x['name']))
    
    def _iter_files(self, file_types: Optional[List[str]] = None):
        """Iterate through files with optional type filtering"""
        for root, dirs, files in os.walk(self.base_path):
            root_path = Path(root)
            
            # Filter directories
            dirs[:] = [d for d in dirs if not self._should_ignore(root_path / d)]
            
            for file in files:
                file_path = root_path / file
                
                if file_types:
                    if not any(file_path.suffix == ft for ft in file_types):
                        continue
                
                yield file_path
    
    def _get_file_info(self, file_path: Path, include_content: bool = False) -> Dict[str, Any]:
        """Get information about a file"""
        info = {
            'path': str(file_path.relative_to(self.base_path)),
            'name': file_path.name,
            'type': self.file_type_mappings.get(file_path.suffix, 'other'),
            'size': file_path.stat().st_size
        }
        
        if include_content and info['size'] < 1024 * 1024:  # Max 1MB
            try:
                info['content'] = file_path.read_text(encoding='utf-8', errors='ignore')
            except (OSError, UnicodeDecodeError):
                info['content'] = None
        
        return info
    
    def _get_context(self, lines: List[str], index: int, context_lines: int) -> List[str]:
        """Get context lines around a match"""
        start = max(0, index - context_lines)
        end = min(len(lines), index + context_lines + 1)
        return lines[start:end]
    
    def _determine_category(self, path: Path) -> str:
        """Determine the category of a model based on its path"""
        path_str = str(path).lower()
        
        categories = {
            'llm': ['llm', 'language', 'gpt', 'claude', 'llama'],
            'vision': ['vision', 'image', 'cv', 'visual'],
            'audio': ['audio', 'speech', 'voice', 'sound'],
            'multimodal': ['multimodal', 'multi-modal'],
            'embedding': ['embedding', 'embed', 'vector'],
            'classification': ['classification', 'classifier'],
            'generation': ['generation', 'generative'],
            'translation': ['translation', 'translate'],
            'summarization': ['summarization', 'summary']
        }
        
        for category, keywords in categories.items():
            if any(keyword in path_str for keyword in keywords):
                return category
        
        return 'general'
    
    def _is_model_directory(self, path: Path) -> bool:
        """Check if a directory likely contains model-related files"""
        model_indicators = [
            'model', 'models', 'checkpoint', 'weights',
            'config.json', 'model.json', 'tokenizer',
            '.pt', '.pth', '.onnx', '.pb', '.h5'
        ]
        
        path_str = str(path).lower()
        return any(indicator in path_str for indicator in model_indicators)
    
    def _extract_model_name(self, path: Path) -> str:
        """Extract model name from path"""
        # Try to extract from common patterns
        path_parts = path.parts
        
        for part in reversed(path_parts):
            if any(prefix in part.lower() for prefix in self.model_prefixes):
                return part
            if 'model' in part.lower() and len(part) > 5:
                return part
        
        return path.name
    
    def _extract_provider(self, path: Path) -> str:
        """Extract provider name from path"""
        providers = {
            'openai': ['openai', 'gpt'],
            'anthropic': ['anthropic', 'claude'],
            'meta': ['meta', 'llama', 'facebook'],
            'google': ['google', 'gemini', 'palm', 'bard'],
            'mistral': ['mistral'],
            'huggingface': ['huggingface', 'hf'],
            'microsoft': ['microsoft', 'azure'],
            'amazon': ['amazon', 'aws', 'bedrock']
        }
        
        path_str = str(path).lower()
        
        for provider, keywords in providers.items():
            if any(keyword in path_str for keyword in keywords):
                return provider
        
        return 'unknown'