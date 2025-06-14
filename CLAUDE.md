# Claude Code Settings for Haconiwa Project

## Important Guidelines

### Path References
- **NEVER use full paths** in documentation or code comments
- Use relative paths or descriptive references instead
- Bad: `/Users/username/project/haconiwa/src/file.py`
- Good: `src/file.py` or `haconiwa/src/file.py`

### Code Development Guidelines
- **絶対にフルパスのハードコーディングをしない**
  - NG: `/Users/username/project/...`
  - OK: `Path.cwd()`, `Path(__file__).parent`, 相対パス
- **ハードコーディングは基本的に避ける**
  - 設定値は設定ファイルや環境変数から取得
  - マジックナンバーは定数として定義
  - 固定値の代わりに動的な計算や設定を使用

## Available Commands

### ripgrep (rg)
Fast file content search tool:
- **Use `rg` command directly** (not `~/bin/rg` or other paths)
- If `rg` is not available, ask user to install it via:
  ```bash
  brew install ripgrep  # macOS
  # or
  apt install ripgrep   # Ubuntu/Debian
  ```

Example usage:
```bash
rg "search_pattern" /path/to/search
rg "function_name" src/ -A5 -B5
```

## Creating Pull Requests

When creating a pull request, always open it in the web browser:

gh pr create --base <target-branch> --title "title" --body "description"
gh pr view <PR-number> --web  # Automatically open in browser

```

## Lint and Type Check Commands

When making code changes, always run:
```bash
# Python linting
ruff check src/

# Type checking
mypy src/
```