# Haconiwa Scan Command Demo

This demo showcases the capabilities of the `haconiwa scan` command for AI model search and analysis.

## Setup

First, let's create a sample AI model directory structure:

```bash
# Create sample model directories
mkdir -p models/{openai/gpt-4,anthropic/claude-3-opus,meta/llama-2-70b,google/gemini-pro}
mkdir -p models/vision/{openai/dall-e-3,stability/stable-diffusion-xl}
mkdir -p models/audio/openai/whisper-large
mkdir -p models/embeddings/{openai/text-embedding-ada-002,cohere/embed-english-v3}

# Create config files
cat > models/openai/gpt-4/config.json << EOF
{
  "model_name": "gpt-4",
  "model_type": "language",
  "parameters": "1.76T",
  "context_length": 128000,
  "capabilities": ["chat", "completion", "analysis", "coding"],
  "version": "gpt-4-1106-preview"
}
EOF

cat > models/anthropic/claude-3-opus/config.json << EOF
{
  "model_name": "claude-3-opus-20240229",
  "model_type": "language",
  "parameters": "Unknown",
  "context_length": 200000,
  "capabilities": ["chat", "analysis", "coding", "vision"],
  "training_cutoff": "2023-08"
}
EOF

# Create model files
touch models/openai/gpt-4/model.onnx
touch models/anthropic/claude-3-opus/model.safetensors
touch models/meta/llama-2-70b/model.bin
touch models/vision/openai/dall-e-3/model.pt
touch models/audio/openai/whisper-large/model.pth

# Create example usage files
cat > models/openai/gpt-4/example.py << EOF
import openai

client = openai.OpenAI()
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain quantum computing"}
    ]
)
print(response.choices[0].message.content)
EOF

cat > models/anthropic/claude-3-opus/example.py << EOF
import anthropic

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-3-opus-20240229",
    messages=[
        {"role": "user", "content": "Write a haiku about AI"}
    ],
    max_tokens=100
)
print(response.content[0].text)
EOF
```

## Demo Commands

### 1. Model Search

#### Basic Model Search
```bash
# Search for GPT-4 (with automatic prefix stripping)
haconiwa scan model gpt-4

# Output:
# Model Search: gpt-4
# ================================================
# Total files found: 3
# 
# Matches by category:
#   llm: 3 files
```

#### Search Without Prefix Stripping
```bash
# Keep the full model name
haconiwa scan model claude-3-opus --no-strip-prefix

# Search with JSON output
haconiwa scan model gpt-4 --format json
```

#### Search with Content Inclusion
```bash
# Include file contents in search results
haconiwa scan model whisper-large --content --format yaml
```

### 2. Content Search

#### Search for Specific Patterns
```bash
# Find all OpenAI API usage
haconiwa scan content "openai\." --type .py

# Search for model loading patterns
haconiwa scan content "load_model|from_pretrained|Model\(" --type .py --context 3
```

#### Search with Context
```bash
# Find anthropic usage with 5 lines of context
haconiwa scan content "anthropic" --context 5 --format json
```

### 3. Model Analysis

#### Analyze All Models
```bash
# Get overview of all models
haconiwa scan analyze --format summary

# Output:
# Model Analysis Summary
# ================================================
# Base path: ./models
# Total models: 8
# Total size: 15.3 GB
# 
# Insights:
#   • Found 8 models across 4 categories
#   • Total model storage: 15.3 GB
#   • Most common format: PyTorch (3 models)
#   • Models from 5 different providers
#   • Largest category: llm with 3 models
```

#### Analyze by Category
```bash
# Analyze only language models
haconiwa scan analyze --category llm --format json

# Show directory structure
haconiwa scan analyze --show-structure --format tree
```

### 4. Model Comparison

#### Compare Multiple Models
```bash
# Compare language models
haconiwa scan compare gpt-4 claude-3-opus llama-2-70b --format table

# Output (formatted as table):
# ┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
# ┃ Aspect        ┃ gpt-4           ┃ claude-3-opus    ┃ llama-2-70b   ┃
# ┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
# │ capabilities  │ chat, coding    │ chat, vision     │ chat          │
# │ parameters    │ 1.76T          │ Unknown          │ 70B           │
# │ context       │ 128000         │ 200000           │ 4096          │
# │ formats       │ ONNX           │ SafeTensors      │ Binary        │
# │ size          │ 3.2 GB         │ 2.8 GB           │ 140 GB        │
# └───────────────┴─────────────────┴──────────────────┴───────────────┘
```

#### Compare Specific Aspects
```bash
# Compare only capabilities and performance
haconiwa scan compare gpt-4 gemini-pro --aspects capabilities performance --format json
```

### 5. Guide Generation

#### Generate Development Guide
```bash
# Generate comprehensive development guide
haconiwa scan guide gpt-4 --type development

# Save to file
haconiwa scan guide claude-3-opus --type development --output claude-dev-guide.md
```

#### Generate Other Guide Types
```bash
# Quick start guide
haconiwa scan guide whisper-large --type quickstart

# Integration guide for production deployment
haconiwa scan guide dall-e-3 --type integration

# Usage guide with examples
haconiwa scan guide text-embedding-ada-002 --type usage
```

### 6. List Models

#### List All Models
```bash
# Table format (default)
haconiwa scan list

# Output:
# ┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━┓
# ┃ Provider   ┃ Model                   ┃ Category ┃ Files ┃
# ┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━┩
# │ openai     │ gpt-4                   │ llm      │ 3     │
# │ anthropic  │ claude-3-opus           │ llm      │ 3     │
# │ meta       │ llama-2-70b             │ llm      │ 2     │
# │ google     │ gemini-pro              │ llm      │ 2     │
# │ openai     │ dall-e-3                │ vision   │ 2     │
# │ stability  │ stable-diffusion-xl     │ vision   │ 2     │
# │ openai     │ whisper-large           │ audio    │ 2     │
# │ openai     │ text-embedding-ada-002  │ embedding│ 2     │
# └────────────┴─────────────────────────┴──────────┴───────┘
```

#### List with Filters
```bash
# List only OpenAI models
haconiwa scan list --provider openai --format json

# List only vision models
haconiwa scan list --category vision --format yaml

# Tree view of model structure
haconiwa scan list --format tree
```

## Advanced Usage

### 1. Using Ignore Patterns
```bash
# Ignore test and backup files
haconiwa scan model gpt-4 --ignore "*.test.*" --ignore "*.bak" --ignore "__pycache__"
```

### 2. Using Whitelist
```bash
# Only search in specific directories
haconiwa scan model claude --whitelist "*/anthropic/*" --whitelist "*/models/*"
```

### 3. Complex Content Search
```bash
# Search for multiple patterns with regex
haconiwa scan content "(import|from)\s+(openai|anthropic|transformers)" --type .py --format json
```

### 4. Batch Analysis
```bash
# Analyze and compare all models, output to file
haconiwa scan analyze --format json > model-analysis.json
haconiwa scan compare $(haconiwa scan list --format json | jq -r '.[].name' | tr '\n' ' ') --format json > model-comparison.json
```

### 5. Integration with Other Haconiwa Commands
```bash
# Use scan results to create tasks
MODEL_LIST=$(haconiwa scan list --provider openai --format json | jq -r '.[].name')
for model in $MODEL_LIST; do
    haconiwa task create "optimize-$model" --description "Optimize $model inference"
done

# Generate guides for all models in a space
haconiwa scan list --format json | jq -r '.[].name' | while read model; do
    haconiwa scan guide "$model" --type quickstart --output "guides/$model-quickstart.md"
done
```

## Tips and Best Practices

1. **Use appropriate output formats**:
   - `text` or `summary` for human reading
   - `json` for scripting and automation
   - `yaml` for configuration files
   - `table` for comparisons

2. **Leverage prefix stripping**:
   - Makes searches more flexible
   - Handles vendor prefixes automatically

3. **Combine with shell tools**:
   - Use `jq` for JSON processing
   - Pipe to `grep` for additional filtering
   - Save results for later analysis

4. **Regular model inventory**:
   ```bash
   # Weekly model inventory
   haconiwa scan analyze --format json > "model-inventory-$(date +%Y%m%d).json"
   ```

5. **Model documentation**:
   ```bash
   # Auto-generate docs for all models
   haconiwa scan list | awk '{print $2}' | while read model; do
       haconiwa scan guide "$model" --type development
   done > all-models-guide.md
   ```

## Troubleshooting

### Issue: No models found
```bash
# Check your path
haconiwa scan model gpt-4 --path ./models

# Use more flexible search
haconiwa scan content "gpt-4" --format summary
```

### Issue: Too many results
```bash
# Use whitelist to narrow search
haconiwa scan model gpt --whitelist "*/openai/*"

# Add ignore patterns
haconiwa scan model gpt --ignore "*.backup" --ignore "test/*"
```

### Issue: Slow performance
```bash
# Limit search depth with whitelist
haconiwa scan analyze --whitelist "*/models/*" --whitelist "*/checkpoints/*"

# Exclude large directories
haconiwa scan model llama --ignore "*/datasets/*" --ignore "*/cache/*"
```

## Conclusion

The `haconiwa scan` command provides powerful capabilities for AI model discovery, analysis, and documentation. It integrates seamlessly with other haconiwa commands and supports various output formats for both human and machine consumption.