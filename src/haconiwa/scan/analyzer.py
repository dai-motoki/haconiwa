"""
Model Analyzer Implementation

Analyzes AI model directory structures, categorization,
and provides insights about model organization.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from collections import defaultdict
import json
import yaml
from datetime import datetime

class ModelAnalyzer:
    """Analyzes AI model directory structures and metadata"""
    
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        
        # Common model configuration files
        self.config_files = [
            'config.json', 'model_config.json', 'configuration.json',
            'config.yaml', 'config.yml', 'metadata.json',
            'model_card.md', 'README.md'
        ]
        
        # Model file extensions
        self.model_extensions = {
            '.pt': 'PyTorch',
            '.pth': 'PyTorch',
            '.onnx': 'ONNX',
            '.pb': 'TensorFlow',
            '.h5': 'Keras/TensorFlow',
            '.tflite': 'TensorFlow Lite',
            '.mlmodel': 'Core ML',
            '.bin': 'Binary',
            '.safetensors': 'SafeTensors',
            '.gguf': 'GGUF (llama.cpp)',
            '.ggml': 'GGML'
        }
    
    def analyze_all(self) -> Dict[str, Any]:
        """Analyze entire directory structure"""
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'base_path': str(self.base_path),
            'categories': defaultdict(list),
            'providers': defaultdict(list),
            'model_formats': defaultdict(int),
            'total_models': 0,
            'total_size': 0,
            'insights': []
        }
        
        # Scan directory structure
        for root, dirs, files in self.base_path.walk():
            root_path = Path(root)
            
            # Check if this is a model directory
            if self._is_model_directory(root_path, files):
                model_info = self._analyze_model_directory(root_path, files)
                
                if model_info:
                    category = model_info['category']
                    provider = model_info['provider']
                    
                    analysis['categories'][category].append(model_info)
                    analysis['providers'][provider].append(model_info['name'])
                    analysis['total_models'] += 1
                    analysis['total_size'] += model_info.get('size', 0)
                    
                    # Track model formats
                    for fmt in model_info.get('formats', []):
                        analysis['model_formats'][fmt] += 1
        
        # Generate insights
        analysis['insights'] = self._generate_insights(analysis)
        
        # Convert defaultdicts to regular dicts
        analysis['categories'] = dict(analysis['categories'])
        analysis['providers'] = dict(analysis['providers'])
        analysis['model_formats'] = dict(analysis['model_formats'])
        
        return analysis
    
    def analyze_category(self, category: str) -> Dict[str, Any]:
        """Analyze models in a specific category"""
        analysis = {
            'category': category,
            'models': [],
            'total_count': 0,
            'total_size': 0,
            'common_formats': defaultdict(int),
            'providers': defaultdict(int)
        }
        
        all_analysis = self.analyze_all()
        
        if category in all_analysis['categories']:
            models = all_analysis['categories'][category]
            analysis['models'] = models
            analysis['total_count'] = len(models)
            
            for model in models:
                analysis['total_size'] += model.get('size', 0)
                analysis['providers'][model.get('provider', 'unknown')] += 1
                
                for fmt in model.get('formats', []):
                    analysis['common_formats'][fmt] += 1
        
        # Convert defaultdicts
        analysis['common_formats'] = dict(analysis['common_formats'])
        analysis['providers'] = dict(analysis['providers'])
        
        return analysis
    
    def get_directory_structure(self) -> Dict[str, Any]:
        """Get hierarchical directory structure"""
        structure = {}
        
        def build_tree(path: Path, tree: Dict[str, Any]):
            """Recursively build directory tree"""
            try:
                for item in sorted(path.iterdir()):
                    if item.is_dir() and not item.name.startswith('.'):
                        tree[item.name] = {}
                        build_tree(item, tree[item.name])
                    elif item.is_file() and self._is_model_file(item):
                        if '__files__' not in tree:
                            tree['__files__'] = []
                        tree['__files__'].append({
                            'name': item.name,
                            'size': item.stat().st_size,
                            'type': self.model_extensions.get(item.suffix, 'other')
                        })
            except PermissionError:
                pass
        
        build_tree(self.base_path, structure)
        return structure
    
    def _is_model_directory(self, path: Path, files: List[str]) -> bool:
        """Check if directory contains model files"""
        # Check for config files
        has_config = any(f in files for f in self.config_files)
        
        # Check for model files
        has_model = any(
            any(f.endswith(ext) for ext in self.model_extensions.keys())
            for f in files
        )
        
        # Check directory name patterns
        model_patterns = ['model', 'checkpoint', 'weights', 'ckpt']
        has_pattern = any(pattern in path.name.lower() for pattern in model_patterns)
        
        return has_config or has_model or has_pattern
    
    def _analyze_model_directory(self, path: Path, files: List[str]) -> Optional[Dict[str, Any]]:
        """Analyze a single model directory"""
        model_info = {
            'path': str(path.relative_to(self.base_path)),
            'name': self._extract_model_name(path),
            'provider': self._extract_provider(path),
            'category': self._determine_category(path),
            'formats': [],
            'size': 0,
            'files': [],
            'config': None
        }
        
        # Analyze files
        for file in files:
            file_path = path / file
            
            try:
                file_stat = file_path.stat()
                file_size = file_stat.st_size
                model_info['size'] += file_size
                
                # Check for model files
                for ext, format_name in self.model_extensions.items():
                    if file.endswith(ext):
                        model_info['formats'].append(format_name)
                        model_info['files'].append({
                            'name': file,
                            'format': format_name,
                            'size': file_size
                        })
                        break
                
                # Load config if available
                if file in self.config_files and file.endswith(('.json', '.yaml', '.yml')):
                    try:
                        if file.endswith('.json'):
                            with open(file_path, 'r') as f:
                                model_info['config'] = json.load(f)
                        elif file.endswith(('.yaml', '.yml')):
                            with open(file_path, 'r') as f:
                                model_info['config'] = yaml.safe_load(f)
                    except:
                        pass
            
            except (PermissionError, OSError):
                continue
        
        # Remove duplicates from formats
        model_info['formats'] = list(set(model_info['formats']))
        
        return model_info if model_info['formats'] or model_info['config'] else None
    
    def _extract_model_name(self, path: Path) -> str:
        """Extract model name from path"""
        # Try to get from config files first
        for config_file in self.config_files:
            config_path = path / config_file
            if config_path.exists():
                try:
                    if config_file.endswith('.json'):
                        with open(config_path, 'r') as f:
                            config = json.load(f)
                            if 'model_name' in config:
                                return config['model_name']
                            if 'name' in config:
                                return config['name']
                except:
                    pass
        
        # Fallback to directory name
        return path.name
    
    def _extract_provider(self, path: Path) -> str:
        """Extract provider from path or config"""
        providers = {
            'openai': ['openai', 'gpt'],
            'anthropic': ['anthropic', 'claude'],
            'meta': ['meta', 'llama'],
            'google': ['google', 'gemini', 'palm'],
            'mistral': ['mistral'],
            'huggingface': ['huggingface', 'hf']
        }
        
        path_str = str(path).lower()
        
        for provider, keywords in providers.items():
            if any(keyword in path_str for keyword in keywords):
                return provider
        
        return 'unknown'
    
    def _determine_category(self, path: Path) -> str:
        """Determine model category"""
        path_str = str(path).lower()
        
        categories = {
            'llm': ['llm', 'language', 'text', 'chat'],
            'vision': ['vision', 'image', 'visual', 'cv'],
            'audio': ['audio', 'speech', 'voice', 'sound'],
            'multimodal': ['multimodal', 'multi-modal'],
            'embedding': ['embedding', 'embed', 'vector']
        }
        
        for category, keywords in categories.items():
            if any(keyword in path_str for keyword in keywords):
                return category
        
        return 'general'
    
    def _is_model_file(self, path: Path) -> bool:
        """Check if file is a model file"""
        return path.suffix in self.model_extensions or path.name in self.config_files
    
    def _generate_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate insights from analysis"""
        insights = []
        
        # Model count insight
        if analysis['total_models'] > 0:
            insights.append(f"Found {analysis['total_models']} models across {len(analysis['categories'])} categories")
        
        # Size insight
        if analysis['total_size'] > 0:
            size_gb = analysis['total_size'] / (1024 ** 3)
            insights.append(f"Total model storage: {size_gb:.2f} GB")
        
        # Format insights
        if analysis['model_formats']:
            most_common = max(analysis['model_formats'].items(), key=lambda x: x[1])
            insights.append(f"Most common format: {most_common[0]} ({most_common[1]} models)")
        
        # Provider insights
        if analysis['providers']:
            provider_count = len(analysis['providers'])
            insights.append(f"Models from {provider_count} different providers")
        
        # Category distribution
        if analysis['categories']:
            largest_category = max(analysis['categories'].items(), key=lambda x: len(x[1]))
            insights.append(f"Largest category: {largest_category[0]} with {len(largest_category[1])} models")
        
        return insights