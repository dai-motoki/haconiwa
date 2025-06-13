"""
Model Comparator Implementation

Compares multiple AI models across various aspects including
capabilities, parameters, performance, and use cases.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import yaml
from collections import defaultdict

class ModelComparator:
    """Compares multiple AI models"""
    
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        
        # Comparison aspects
        self.aspects = {
            'capabilities': self._compare_capabilities,
            'parameters': self._compare_parameters,
            'performance': self._compare_performance,
            'use_cases': self._compare_use_cases,
            'formats': self._compare_formats,
            'size': self._compare_size,
            'metadata': self._compare_metadata
        }
    
    def compare(self, models: List[str], aspects: List[str]) -> Dict[str, Any]:
        """Compare multiple models across specified aspects"""
        comparison = {
            'models': models,
            'timestamp': self._get_timestamp(),
            'results': {}
        }
        
        # Load model information
        model_data = {}
        for model in models:
            model_info = self._load_model_info(model)
            if model_info:
                model_data[model] = model_info
        
        # Compare across requested aspects
        for aspect in aspects:
            if aspect in self.aspects:
                comparison['results'][aspect] = self.aspects[aspect](model_data)
        
        return comparison['results']
    
    def _load_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Load information about a specific model"""
        from .scanner import ModelScanner
        
        scanner = ModelScanner(self.base_path)
        search_results = scanner.search_by_model_name(model_name)
        
        if not search_results['matches']:
            return None
        
        model_info = {
            'name': model_name,
            'files': [],
            'config': None,
            'metadata': {},
            'size': 0
        }
        
        # Collect all files from matches
        for category, files in search_results['matches'].items():
            for file_info in files:
                model_info['files'].append(file_info)
                model_info['size'] += file_info.get('size', 0)
                
                # Try to load config
                file_path = self.base_path / file_info['path']
                if file_path.name in ['config.json', 'model_config.json']:
                    try:
                        with open(file_path, 'r') as f:
                            model_info['config'] = json.load(f)
                    except:
                        pass
        
        return model_info
    
    def _compare_capabilities(self, model_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Compare model capabilities"""
        capabilities = {}
        
        capability_keywords = {
            'text_generation': ['generate', 'completion', 'text', 'language'],
            'code_generation': ['code', 'programming', 'syntax'],
            'translation': ['translate', 'multilingual', 'language'],
            'summarization': ['summary', 'summarize', 'abstract'],
            'classification': ['classify', 'classification', 'categorize'],
            'embedding': ['embed', 'embedding', 'vector'],
            'chat': ['chat', 'conversation', 'dialogue'],
            'reasoning': ['reason', 'logic', 'analytical'],
            'multimodal': ['multimodal', 'image', 'vision', 'audio']
        }
        
        for model, data in model_data.items():
            model_capabilities = set()
            
            # Check config for capabilities
            if data.get('config'):
                config_str = json.dumps(data['config']).lower()
                for capability, keywords in capability_keywords.items():
                    if any(keyword in config_str for keyword in keywords):
                        model_capabilities.add(capability)
            
            # Check file names and paths
            for file_info in data.get('files', []):
                file_str = file_info['path'].lower()
                for capability, keywords in capability_keywords.items():
                    if any(keyword in file_str for keyword in keywords):
                        model_capabilities.add(capability)
            
            capabilities[model] = list(model_capabilities)
        
        return capabilities
    
    def _compare_parameters(self, model_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Compare model parameters"""
        parameters = {}
        
        for model, data in model_data.items():
            model_params = {
                'total_parameters': 'Unknown',
                'layers': 'Unknown',
                'hidden_size': 'Unknown',
                'vocabulary_size': 'Unknown'
            }
            
            # Extract from config
            if data.get('config'):
                config = data['config']
                
                # Common parameter names across different frameworks
                param_mappings = {
                    'total_parameters': ['n_params', 'num_parameters', 'total_params'],
                    'layers': ['n_layers', 'num_layers', 'num_hidden_layers'],
                    'hidden_size': ['hidden_size', 'd_model', 'n_embd'],
                    'vocabulary_size': ['vocab_size', 'vocabulary_size', 'n_vocab']
                }
                
                for param_key, possible_names in param_mappings.items():
                    for name in possible_names:
                        if name in config:
                            model_params[param_key] = config[name]
                            break
            
            parameters[model] = model_params
        
        return parameters
    
    def _compare_performance(self, model_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Compare model performance metrics"""
        performance = {}
        
        for model, data in model_data.items():
            model_perf = {
                'inference_speed': 'Unknown',
                'memory_usage': 'Unknown',
                'accuracy': 'Unknown',
                'benchmark_scores': {}
            }
            
            # Try to find performance data in config or metadata
            if data.get('config'):
                config = data['config']
                
                # Look for benchmark scores
                benchmark_keys = ['benchmark', 'evaluation', 'scores', 'metrics']
                for key in benchmark_keys:
                    if key in config:
                        model_perf['benchmark_scores'] = config[key]
                        break
            
            # Estimate based on model size
            if data.get('size', 0) > 0:
                size_gb = data['size'] / (1024 ** 3)
                if size_gb < 1:
                    model_perf['inference_speed'] = 'Fast'
                elif size_gb < 10:
                    model_perf['inference_speed'] = 'Medium'
                else:
                    model_perf['inference_speed'] = 'Slow'
            
            performance[model] = model_perf
        
        return performance
    
    def _compare_use_cases(self, model_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Compare model use cases"""
        use_cases = {}
        
        use_case_patterns = {
            'chatbot': ['chat', 'conversation', 'dialogue'],
            'content_generation': ['generate', 'create', 'write'],
            'code_assistance': ['code', 'programming', 'development'],
            'translation': ['translate', 'multilingual'],
            'analysis': ['analyze', 'analysis', 'insight'],
            'summarization': ['summary', 'summarize'],
            'question_answering': ['qa', 'question', 'answer'],
            'research': ['research', 'academic', 'scientific']
        }
        
        for model, data in model_data.items():
            model_use_cases = set()
            
            # Check all text content for use case patterns
            all_text = []
            if data.get('config'):
                all_text.append(json.dumps(data['config']))
            
            for file_info in data.get('files', []):
                all_text.append(file_info['path'])
            
            combined_text = ' '.join(all_text).lower()
            
            for use_case, patterns in use_case_patterns.items():
                if any(pattern in combined_text for pattern in patterns):
                    model_use_cases.add(use_case)
            
            use_cases[model] = list(model_use_cases)
        
        return use_cases
    
    def _compare_formats(self, model_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Compare available model formats"""
        formats = {}
        
        format_extensions = {
            '.pt': 'PyTorch',
            '.pth': 'PyTorch',
            '.onnx': 'ONNX',
            '.pb': 'TensorFlow',
            '.h5': 'Keras',
            '.tflite': 'TensorFlow Lite',
            '.safetensors': 'SafeTensors',
            '.gguf': 'GGUF',
            '.bin': 'Binary'
        }
        
        for model, data in model_data.items():
            model_formats = set()
            
            for file_info in data.get('files', []):
                file_path = Path(file_info['path'])
                if file_path.suffix in format_extensions:
                    model_formats.add(format_extensions[file_path.suffix])
            
            formats[model] = list(model_formats)
        
        return formats
    
    def _compare_size(self, model_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Compare model sizes"""
        sizes = {}
        
        for model, data in model_data.items():
            size_bytes = data.get('size', 0)
            size_gb = size_bytes / (1024 ** 3)
            
            sizes[model] = {
                'bytes': size_bytes,
                'gb': round(size_gb, 2),
                'category': self._categorize_size(size_gb)
            }
        
        return sizes
    
    def _compare_metadata(self, model_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Compare model metadata"""
        metadata = {}
        
        for model, data in model_data.items():
            model_meta = {
                'has_config': data.get('config') is not None,
                'file_count': len(data.get('files', [])),
                'config_keys': list(data['config'].keys()) if data.get('config') else []
            }
            
            # Extract specific metadata if available
            if data.get('config'):
                config = data['config']
                important_keys = [
                    'model_type', 'architecture', 'license', 
                    'training_data', 'created_by', 'version'
                ]
                
                for key in important_keys:
                    if key in config:
                        model_meta[key] = config[key]
            
            metadata[model] = model_meta
        
        return metadata
    
    def _categorize_size(self, size_gb: float) -> str:
        """Categorize model size"""
        if size_gb < 0.1:
            return 'Tiny'
        elif size_gb < 1:
            return 'Small'
        elif size_gb < 10:
            return 'Medium'
        elif size_gb < 50:
            return 'Large'
        else:
            return 'Very Large'
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()