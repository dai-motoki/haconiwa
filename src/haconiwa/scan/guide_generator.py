"""
Guide Generator Implementation

Generates development guides, usage documentation, and integration
guides for specific AI models based on discovered information.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import json
from datetime import datetime

class GuideGenerator:
    """Generates guides for AI models"""
    
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        
        # Guide templates
        self.templates = {
            'development': self._generate_development_guide,
            'usage': self._generate_usage_guide,
            'integration': self._generate_integration_guide,
            'quickstart': self._generate_quickstart_guide
        }
    
    def generate(self, model_name: str, guide_type: str = 'development') -> str:
        """Generate a guide for the specified model"""
        # Load model information
        model_info = self._load_model_info(model_name)
        
        if not model_info:
            return f"# Error: Model '{model_name}' not found\n\nPlease check the model name and try again."
        
        # Generate guide using appropriate template
        generator = self.templates.get(guide_type, self._generate_development_guide)
        return generator(model_info)
    
    def _load_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Load comprehensive information about a model"""
        from .scanner import ModelScanner
        from .analyzer import ModelAnalyzer
        
        scanner = ModelScanner(self.base_path)
        analyzer = ModelAnalyzer(self.base_path)
        
        # Search for model
        search_results = scanner.search_by_model_name(model_name, include_content=True)
        
        if not search_results['matches']:
            return None
        
        # Compile model information
        model_info = {
            'name': model_name,
            'normalized_name': search_results['normalized_name'],
            'files': [],
            'config': None,
            'readme': None,
            'examples': [],
            'requirements': [],
            'api_info': None,
            'categories': search_results.get('categories', []),
            'total_files': search_results.get('total_files', 0)
        }
        
        # Process files
        for category, files in search_results['matches'].items():
            for file_info in files:
                file_path = Path(file_info['path'])
                
                # Extract config
                if file_path.name in ['config.json', 'model_config.json']:
                    try:
                        model_info['config'] = json.loads(file_info.get('content', '{}'))
                    except (json.JSONDecodeError, TypeError):
                        pass
                
                # Extract README
                elif file_path.name.lower() in ['readme.md', 'readme.txt']:
                    model_info['readme'] = file_info.get('content', '')
                
                # Collect examples
                elif 'example' in file_path.name.lower():
                    model_info['examples'].append(file_info)
                
                # Extract requirements
                elif file_path.name in ['requirements.txt', 'requirements.yml']:
                    model_info['requirements'].append(file_info)
                
                # API information
                elif 'api' in file_path.name.lower() or 'client' in file_path.name.lower():
                    model_info['api_info'] = file_info
                
                model_info['files'].append(file_info)
        
        return model_info
    
    def _generate_development_guide(self, model_info: Dict[str, Any]) -> str:
        """Generate a development guide"""
        lines = [
            f"# Development Guide: {model_info['name']}",
            f"\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "\n## Overview",
            f"\nThis guide provides development information for working with {model_info['name']}."
        ]
        
        # Model information
        if model_info['config']:
            lines.extend([
                "\n## Model Configuration",
                "\n```json",
                json.dumps(model_info['config'], indent=2),
                "```"
            ])
        
        # Categories
        if model_info['categories']:
            lines.extend([
                "\n## Categories",
                f"\nThis model is categorized as: {', '.join(model_info['categories'])}"
            ])
        
        # File structure
        lines.extend([
            "\n## File Structure",
            f"\nTotal files: {model_info['total_files']}",
            "\n### Key Files:"
        ])
        
        for file_info in model_info['files'][:10]:  # First 10 files
            lines.append(f"- `{file_info['path']}` ({file_info['type']})")
        
        # Requirements
        if model_info['requirements']:
            lines.extend([
                "\n## Requirements",
                "\n### Dependencies:"
            ])
            
            for req_file in model_info['requirements']:
                if req_file.get('content'):
                    lines.append(f"\nFrom `{req_file['name']}`:")
                    lines.append("```")
                    lines.append(req_file['content'][:500])  # First 500 chars
                    if len(req_file['content']) > 500:
                        lines.append("...")
                    lines.append("```")
        
        # API Usage
        if model_info['api_info']:
            lines.extend([
                "\n## API Integration",
                f"\nAPI file found: `{model_info['api_info']['path']}`",
                "\nRefer to this file for API integration details."
            ])
        
        # Examples
        if model_info['examples']:
            lines.extend([
                "\n## Examples",
                "\n### Available Examples:"
            ])
            
            for example in model_info['examples'][:5]:
                lines.append(f"- `{example['path']}`")
        
        # Getting Started
        lines.extend([
            "\n## Getting Started",
            "\n### 1. Setup Environment",
            "```bash",
            "# Create virtual environment",
            "python -m venv venv",
            "source venv/bin/activate  # On Windows: venv\\Scripts\\activate",
            "",
            "# Install dependencies",
            "pip install -r requirements.txt",
            "```",
            "\n### 2. Load Model",
            "```python",
            f"# Example code to load {model_info['name']}",
            "import json",
            "",
            "# Load configuration",
            "with open('config.json', 'r') as f:",
            "    config = json.load(f)",
            "",
            "# Initialize model (framework-specific)",
            "# Add your model initialization code here",
            "```"
        ])
        
        # Best Practices
        lines.extend([
            "\n## Best Practices",
            "\n1. **Version Control**: Track model versions and configurations",
            "2. **Testing**: Implement comprehensive tests for model inference",
            "3. **Documentation**: Keep documentation up-to-date with model changes",
            "4. **Performance**: Monitor and optimize inference performance",
            "5. **Security**: Validate inputs and handle errors gracefully"
        ])
        
        # Additional Resources
        lines.extend([
            "\n## Additional Resources",
            "\n- Model documentation: Check README files in the model directory",
            "- Examples: Review example files for usage patterns",
            "- Configuration: Refer to config files for model parameters"
        ])
        
        return "\n".join(lines)
    
    def _generate_usage_guide(self, model_info: Dict[str, Any]) -> str:
        """Generate a usage guide"""
        lines = [
            f"# Usage Guide: {model_info['name']}",
            f"\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "\n## Quick Start"
        ]
        
        # Basic usage
        lines.extend([
            "\n### Basic Usage",
            "\n```python",
            f"# Using {model_info['name']}",
            "",
            "# 1. Import necessary libraries",
            "import json",
            "from pathlib import Path",
            "",
            "# 2. Load model configuration",
            "config_path = Path('config.json')",
            "with open(config_path, 'r') as f:",
            "    config = json.load(f)",
            "",
            "# 3. Initialize and use model",
            "# Add framework-specific code here",
            "```"
        ])
        
        # Common use cases
        lines.extend([
            "\n## Common Use Cases",
            f"\nBased on the model structure, {model_info['name']} can be used for:"
        ])
        
        if 'llm' in str(model_info['categories']).lower():
            lines.extend([
                "\n### Text Generation",
                "- Content creation",
                "- Code generation",
                "- Language translation",
                "- Text summarization"
            ])
        
        if 'vision' in str(model_info['categories']).lower():
            lines.extend([
                "\n### Computer Vision",
                "- Image classification",
                "- Object detection",
                "- Image generation",
                "- Visual analysis"
            ])
        
        # Parameters
        if model_info['config']:
            lines.extend([
                "\n## Model Parameters",
                "\nKey configuration options:"
            ])
            
            for key, value in list(model_info['config'].items())[:10]:
                lines.append(f"- `{key}`: {value}")
        
        # Examples from files
        if model_info['examples']:
            lines.extend([
                "\n## Code Examples",
                "\nExample files available:"
            ])
            
            for example in model_info['examples'][:3]:
                lines.append(f"\n### {example['name']}")
                if example.get('content'):
                    lines.append("```python")
                    lines.append(example['content'][:300])
                    if len(example['content']) > 300:
                        lines.append("# ... (truncated)")
                    lines.append("```")
        
        # Tips
        lines.extend([
            "\n## Tips and Tricks",
            "\n1. **Performance Optimization**:",
            "   - Use appropriate batch sizes",
            "   - Enable GPU acceleration if available",
            "   - Consider model quantization for deployment",
            "",
            "2. **Error Handling**:",
            "   - Validate input data formats",
            "   - Handle out-of-memory errors gracefully",
            "   - Implement timeout mechanisms",
            "",
            "3. **Best Results**:",
            "   - Preprocess input data appropriately",
            "   - Use recommended hyperparameters",
            "   - Fine-tune for specific use cases"
        ])
        
        return "\n".join(lines)
    
    def _generate_integration_guide(self, model_info: Dict[str, Any]) -> str:
        """Generate an integration guide"""
        lines = [
            f"# Integration Guide: {model_info['name']}",
            f"\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "\n## Overview",
            f"\nThis guide helps you integrate {model_info['name']} into your application."
        ]
        
        # Integration approaches
        lines.extend([
            "\n## Integration Approaches",
            "\n### 1. Direct Integration",
            "```python",
            "# Direct model loading and inference",
            "from your_framework import load_model",
            "",
            "model = load_model('path/to/model')",
            "result = model.predict(input_data)",
            "```",
            "\n### 2. API Integration",
            "```python",
            "# REST API integration",
            "import requests",
            "",
            "response = requests.post(",
            "    'http://your-api-endpoint/predict',",
            "    json={'input': input_data}",
            ")",
            "result = response.json()",
            "```",
            "\n### 3. Microservice Architecture",
            "```yaml",
            "# Docker Compose example",
            "version: '3.8'",
            "services:",
            "  model-service:",
            "    image: your-model-image",
            "    ports:",
            "      - '8080:8080'",
            "    environment:",
            "      - MODEL_PATH=/models/your-model",
            "```"
        ])
        
        # Requirements for integration
        lines.extend([
            "\n## System Requirements",
            "\n### Hardware Requirements",
            "- CPU: Multi-core processor recommended",
            "- RAM: Depends on model size",
            "- GPU: Optional but recommended for large models",
            "\n### Software Requirements"
        ])
        
        if model_info['requirements']:
            for req_file in model_info['requirements']:
                if req_file.get('content'):
                    lines.append(f"\nFrom `{req_file['name']}`:")
                    lines.append("```")
                    lines.append(req_file['content'][:200])
                    lines.append("```")
        
        # Configuration
        lines.extend([
            "\n## Configuration",
            "\n### Environment Variables",
            "```bash",
            "export MODEL_PATH=/path/to/model",
            "export MODEL_CONFIG=/path/to/config.json",
            "export DEVICE=cuda  # or cpu",
            "```"
        ])
        
        # Deployment options
        lines.extend([
            "\n## Deployment Options",
            "\n### 1. Cloud Deployment",
            "- AWS SageMaker",
            "- Google Cloud AI Platform",
            "- Azure Machine Learning",
            "\n### 2. Edge Deployment",
            "- Mobile devices (TensorFlow Lite, Core ML)",
            "- IoT devices",
            "- Browser (WebAssembly, TensorFlow.js)",
            "\n### 3. On-Premise",
            "- Kubernetes cluster",
            "- Docker containers",
            "- Bare metal servers"
        ])
        
        # Monitoring
        lines.extend([
            "\n## Monitoring and Maintenance",
            "\n### Key Metrics to Monitor",
            "- Inference latency",
            "- Throughput (requests/second)",
            "- Resource utilization (CPU, GPU, Memory)",
            "- Error rates",
            "\n### Logging",
            "```python",
            "import logging",
            "",
            "logging.basicConfig(level=logging.INFO)",
            "logger = logging.getLogger(__name__)",
            "",
            "# Log model predictions",
            "logger.info(f'Prediction: {result}, Latency: {latency}ms')",
            "```"
        ])
        
        return "\n".join(lines)
    
    def _generate_quickstart_guide(self, model_info: Dict[str, Any]) -> str:
        """Generate a quickstart guide"""
        lines = [
            f"# Quick Start: {model_info['name']}",
            f"\nGet started with {model_info['name']} in 5 minutes!",
            "\n## 1. Installation",
            "```bash",
            "# Clone the repository or download model files",
            "git clone <repository-url>",
            "cd " + model_info['name'].lower().replace(' ', '-'),
            "",
            "# Install dependencies",
            "pip install -r requirements.txt",
            "```",
            "\n## 2. Basic Example",
            "```python",
            f"# Quick example using {model_info['name']}",
            "import json",
            "",
            "# Load configuration",
            "with open('config.json', 'r') as f:",
            "    config = json.load(f)",
            "",
            "# Your code here",
            "# model = load_model(config)",
            "# result = model.predict('Hello, world!')",
            "# print(result)",
            "```",
            "\n## 3. Next Steps",
            "- Read the full development guide",
            "- Explore example scripts",
            "- Check model configuration options",
            "- Join the community for support"
        ]
        
        return "\n".join(lines)