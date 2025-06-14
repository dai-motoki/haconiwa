# Haconiwa Scan Command Design Document

## Overview

The `haconiwa scan` command provides universal AI model search and analysis capabilities, integrating seamlessly with haconiwa's existing architecture. It enables developers to discover, analyze, compare, and generate guides for AI models across their codebase.

## Architecture

### Module Structure

```
src/haconiwa/scan/
├── __init__.py          # Module exports
├── cli.py               # CLI command interface
├── scanner.py           # Core scanning functionality
├── analyzer.py          # Model analysis and insights
├── formatter.py         # Output formatting (json, yaml, text, table)
├── comparator.py        # Model comparison features
└── guide_generator.py   # Development guide generation
```

### Key Components

#### 1. ModelScanner (`scanner.py`)
- **Purpose**: Core scanning engine for finding AI models
- **Features**:
  - Model name search with prefix stripping
  - File content search with regex support
  - Directory traversal with ignore/whitelist patterns
  - Model file type detection
  - Provider and category extraction

#### 2. ModelAnalyzer (`analyzer.py`)
- **Purpose**: Analyze model directory structures and metadata
- **Features**:
  - Directory structure analysis
  - Model categorization (LLM, vision, audio, etc.)
  - Configuration file parsing
  - Storage size calculations
  - Insight generation

#### 3. OutputFormatter (`formatter.py`)
- **Purpose**: Format scan results for different output types
- **Supported Formats**:
  - Text (human-readable)
  - JSON (machine-readable)
  - YAML (configuration-friendly)
  - Summary (concise overview)
  - Table (ASCII tables)
  - Tree (directory structure)

#### 4. ModelComparator (`comparator.py`)
- **Purpose**: Compare multiple AI models
- **Comparison Aspects**:
  - Capabilities
  - Parameters (layers, size, etc.)
  - Performance metrics
  - Use cases
  - Available formats
  - File sizes

#### 5. GuideGenerator (`guide_generator.py`)
- **Purpose**: Generate development guides for models
- **Guide Types**:
  - Development guide
  - Usage guide
  - Integration guide
  - Quickstart guide

## Command Structure

### Main Commands

```bash
# Search for model by name
haconiwa scan model <model-name> [OPTIONS]

# Search file contents
haconiwa scan content <pattern> [OPTIONS]

# Analyze model structure
haconiwa scan analyze [OPTIONS]

# Compare models
haconiwa scan compare <model1> <model2> [...] [OPTIONS]

# Generate guide
haconiwa scan guide <model-name> [OPTIONS]

# List all models
haconiwa scan list [OPTIONS]
```

### Common Options

- `--path, -p`: Base path to search (default: current directory)
- `--format, -f`: Output format (text, json, yaml, summary, table, tree)
- `--ignore, -i`: Patterns to ignore
- `--whitelist, -w`: Whitelist specific directories

## Integration with Haconiwa

### 1. CLI Integration
The scan command is registered in the main haconiwa CLI (`cli.py`):

```python
from haconiwa.scan.cli import scan_app
app.add_typer(scan_app, name="scan")
```

### 2. CRD Support (Future)
The scan command can be extended to support CRD definitions:

```yaml
apiVersion: haconiwa.dev/v1
kind: ModelScan
metadata:
  name: ai-model-inventory
spec:
  scanPaths:
    - ./models
    - ./checkpoints
  ignorePatterns:
    - "*.tmp"
    - "__pycache__"
  outputFormat: json
  autoAnalyze: true
```

### 3. Space Integration
Scan results can be used to:
- Auto-configure AI agents with discovered models
- Generate task assignments based on model capabilities
- Create development environments for model work

## Use Cases

### 1. Model Discovery
```bash
# Find all GPT models
haconiwa scan model gpt --strip-prefix

# Find Claude models without prefix stripping
haconiwa scan model claude-3-opus --no-strip-prefix
```

### 2. Code Search
```bash
# Find all model loading code
haconiwa scan content "load_model|from_pretrained" --type .py

# Search for specific API usage
haconiwa scan content "openai.ChatCompletion" --context 5
```

### 3. Model Analysis
```bash
# Analyze entire model directory
haconiwa scan analyze --path ./models --format summary

# Analyze specific category
haconiwa scan analyze --category llm --show-structure
```

### 4. Model Comparison
```bash
# Compare multiple models
haconiwa scan compare o1-mini gpt-4 claude-3-opus --format table

# Compare specific aspects
haconiwa scan compare model1 model2 --aspects capabilities parameters
```

### 5. Guide Generation
```bash
# Generate development guide
haconiwa scan guide o1-mini --type development --output guide.md

# Generate quickstart
haconiwa scan guide claude-3-opus --type quickstart
```

## Implementation Details

### Model Name Normalization
The scanner supports intelligent prefix stripping for common AI model naming patterns:

```python
model_prefixes = [
    "gpt-", "claude-", "llama-", "mistral-", "gemini-",
    "palm-", "anthropic-", "openai-", "meta-", "google-"
]
```

### File Type Detection
Recognizes common AI model file formats:

```python
model_extensions = {
    '.pt': 'PyTorch',
    '.pth': 'PyTorch',
    '.onnx': 'ONNX',
    '.pb': 'TensorFlow',
    '.h5': 'Keras/TensorFlow',
    '.safetensors': 'SafeTensors',
    '.gguf': 'GGUF (llama.cpp)',
    # ... more formats
}
```

### Category Detection
Automatically categorizes models based on path and content:
- LLM (language models)
- Vision (computer vision)
- Audio (speech/sound)
- Multimodal
- Embedding
- Classification
- Generation

## Testing

The scan module includes comprehensive tests:

```
tests/test_scan/
├── test_scanner.py      # Scanner unit tests
├── test_cli.py          # CLI integration tests
└── __init__.py
```

### Test Coverage
- Model search functionality
- Content search with context
- Directory analysis
- Output formatting
- CLI command execution
- Edge cases and error handling

## Future Enhancements

### 1. Model Registry Integration
- Connect to HuggingFace, OpenAI, etc.
- Download model metadata
- Version tracking

### 2. Performance Profiling
- Benchmark model inference speed
- Memory usage analysis
- Optimization suggestions

### 3. Dependency Analysis
- Track model dependencies
- Generate requirements files
- Compatibility checking

### 4. Visual Model Explorer
- Web-based UI for model browsing
- Interactive comparison charts
- Dependency graphs

### 5. AI-Powered Analysis
- Use LLMs to analyze model code
- Generate better insights
- Suggest optimizations

## Conclusion

The `haconiwa scan` command provides a powerful tool for AI model discovery and analysis, fitting naturally into haconiwa's architecture. It supports the core mission of AI-coordinated development by making it easier to understand and work with AI models in a codebase.