"""
Tests for the ModelScanner class
"""

import pytest
from pathlib import Path
import tempfile
import json
from haconiwa.scan.scanner import ModelScanner


class TestModelScanner:
    """Test cases for ModelScanner"""
    
    @pytest.fixture
    def temp_model_dir(self):
        """Create a temporary directory with model files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            
            # Create model directories
            (base_path / "models" / "openai" / "gpt-4").mkdir(parents=True)
            (base_path / "models" / "anthropic" / "claude-3-opus").mkdir(parents=True)
            (base_path / "models" / "meta" / "llama-2-70b").mkdir(parents=True)
            
            # Create config files
            gpt4_config = {
                "model_name": "gpt-4",
                "model_type": "language",
                "parameters": "1.76T"
            }
            with open(base_path / "models" / "openai" / "gpt-4" / "config.json", "w") as f:
                json.dump(gpt4_config, f)
            
            claude_config = {
                "model_name": "claude-3-opus",
                "model_type": "language",
                "capabilities": ["chat", "analysis", "coding"]
            }
            with open(base_path / "models" / "anthropic" / "claude-3-opus" / "config.json", "w") as f:
                json.dump(claude_config, f)
            
            # Create model files
            (base_path / "models" / "openai" / "gpt-4" / "model.pt").touch()
            (base_path / "models" / "anthropic" / "claude-3-opus" / "model.safetensors").touch()
            (base_path / "models" / "meta" / "llama-2-70b" / "model.bin").touch()
            
            # Create example files
            example_code = """
# Example usage of GPT-4
import openai

client = openai.Client()
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
"""
            with open(base_path / "models" / "openai" / "gpt-4" / "example.py", "w") as f:
                f.write(example_code)
            
            yield base_path
    
    def test_search_by_model_name(self, temp_model_dir):
        """Test searching for models by name"""
        scanner = ModelScanner(temp_model_dir)
        
        # Test with exact name
        results = scanner.search_by_model_name("gpt-4")
        assert results['model_name'] == "gpt-4"
        assert results['total_files'] > 0
        assert len(results['categories']) > 0
        
        # Test with prefix stripping
        results = scanner.search_by_model_name("claude-3-opus")
        assert results['normalized_name'] == "3-opus"  # "claude-" prefix stripped
        assert results['total_files'] > 0
    
    def test_search_by_model_name_no_strip(self, temp_model_dir):
        """Test searching without prefix stripping"""
        scanner = ModelScanner(temp_model_dir, strip_prefix=False)
        
        results = scanner.search_by_model_name("claude-3-opus")
        assert results['normalized_name'] == "claude-3-opus"
    
    def test_search_content(self, temp_model_dir):
        """Test content searching"""
        scanner = ModelScanner(temp_model_dir)
        
        # Search for pattern in files
        results = scanner.search_content("openai", file_types=[".py"])
        assert results['total_matches'] > 0
        assert results['files_searched'] > 0
        assert len(results['matches']) > 0
        
        # Verify match details
        first_match = results['matches'][0]
        assert 'file' in first_match
        assert 'line_number' in first_match
        assert 'line' in first_match
        assert 'context' in first_match
    
    def test_list_all_models(self, temp_model_dir):
        """Test listing all models"""
        scanner = ModelScanner(temp_model_dir)
        
        models = scanner.list_all_models()
        assert len(models) >= 3  # We created 3 models
        
        # Check model info structure
        for model in models:
            assert 'name' in model
            assert 'provider' in model
            assert 'category' in model
            assert 'file_count' in model
            assert 'files' in model
    
    def test_list_models_with_filters(self, temp_model_dir):
        """Test listing models with category and provider filters"""
        scanner = ModelScanner(temp_model_dir)
        
        # Filter by provider
        openai_models = scanner.list_all_models(provider="openai")
        assert all(m['provider'] == 'openai' for m in openai_models)
        
        # Filter by category
        llm_models = scanner.list_all_models(category="llm")
        assert all('llm' in m['category'] for m in llm_models)
    
    def test_ignore_patterns(self, temp_model_dir):
        """Test ignore patterns functionality"""
        # Create files that should be ignored
        (temp_model_dir / "models" / "__pycache__").mkdir(parents=True)
        (temp_model_dir / "models" / ".git").mkdir(parents=True)
        (temp_model_dir / "models" / "test.pyc").touch()
        
        scanner = ModelScanner(temp_model_dir)
        
        # These should not appear in results
        results = scanner.search_by_model_name("pycache")
        assert results['total_files'] == 0
        
        results = scanner.search_by_model_name("git")
        assert results['total_files'] == 0
    
    def test_whitelist(self, temp_model_dir):
        """Test whitelist functionality"""
        scanner = ModelScanner(
            temp_model_dir,
            whitelist=["*/openai/*", "*/anthropic/*"]
        )
        
        # Should find openai and anthropic models
        results = scanner.search_by_model_name("gpt-4")
        assert results['total_files'] > 0
        
        results = scanner.search_by_model_name("claude-3-opus")
        assert results['total_files'] > 0
        
        # Should not find meta models (not in whitelist)
        results = scanner.search_by_model_name("llama-2-70b")
        assert results['total_files'] == 0
    
    def test_file_info_with_content(self, temp_model_dir):
        """Test getting file info with content"""
        scanner = ModelScanner(temp_model_dir)
        
        results = scanner.search_by_model_name("gpt-4", include_content=True)
        
        # Find the example.py file in results
        example_file = None
        for files in results['matches'].values():
            for f in files:
                if f['name'] == 'example.py':
                    example_file = f
                    break
        
        assert example_file is not None
        assert 'content' in example_file
        assert 'import openai' in example_file['content']
    
    def test_model_name_normalization(self, temp_model_dir):
        """Test model name normalization"""
        scanner = ModelScanner(temp_model_dir)
        
        # Test various prefixes
        test_cases = [
            ("gpt-4", "4"),
            ("claude-3-opus", "3-opus"),
            ("llama-2-70b", "2-70b"),
            ("mistral-7b", "7b"),
            ("gemini-pro", "pro")
        ]
        
        for original, expected in test_cases:
            normalized = scanner._normalize_model_name(original)
            assert normalized == expected
    
    def test_category_determination(self, temp_model_dir):
        """Test category determination logic"""
        scanner = ModelScanner(temp_model_dir)
        
        # Test various paths
        test_paths = [
            (Path("models/llm/gpt4"), "llm"),
            (Path("models/vision/clip"), "vision"),
            (Path("models/audio/whisper"), "audio"),
            (Path("models/multimodal/flamingo"), "multimodal"),
            (Path("models/embedding/ada"), "embedding"),
            (Path("models/random/model"), "general")
        ]
        
        for path, expected_category in test_paths:
            category = scanner._determine_category(path)
            assert category == expected_category