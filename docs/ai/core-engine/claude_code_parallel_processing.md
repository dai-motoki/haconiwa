# Claude Code SDK 並列処理ガイド

## 概要

Claude Code SDKはPythonの非同期処理（async/await）をサポートしており、理論的には複数のファイルを並列で処理することが可能です。ただし、公式ドキュメントには明示的な並列処理の例は記載されていないため、実装には注意が必要です。

## 基本的な並列処理の実装

### 1. asyncio.gatherを使った並列実行

```python
import asyncio
from claude_code_sdk import query, ClaudeCodeOptions

async def process_file(file_path, prompt):
    """単一ファイルを処理する非同期関数"""
    options = ClaudeCodeOptions(
        allowed_tools=["Read", "Write", "Edit"],
        permission_mode='acceptEdits'
    )
    
    results = []
    async for message in query(
        prompt=f"Edit file {file_path}: {prompt}", 
        options=options
    ):
        results.append(message)
    return results

async def edit_multiple_files():
    """複数ファイルを並列で編集"""
    files_to_edit = [
        ("src/main.py", "Add type hints to all functions"),
        ("src/utils.py", "Refactor helper functions"),
        ("src/database.py", "Add error handling"),
        ("src/api.py", "Implement rate limiting"),
        ("tests/test_main.py", "Update test cases"),
        # ... 10個のファイルまで追加可能
    ]
    
    # 全てのタスクを作成
    tasks = [
        asyncio.create_task(process_file(file, prompt)) 
        for file, prompt in files_to_edit
    ]
    
    # 並列実行
    results = await asyncio.gather(*tasks)
    return results

# 実行
import anyio
anyio.run(edit_multiple_files)
```

### 2. エラーハンドリングを含む実装

```python
async def robust_parallel_processor(files_and_prompts):
    """エラーハンドリングを含む堅牢な並列処理"""
    
    async def safe_process_file(file_path, edit_prompt):
        try:
            options = ClaudeCodeOptions(
                allowed_tools=["Read", "Write", "Edit"],
                permission_mode='acceptEdits'
            )
            
            results = []
            async for message in query(
                prompt=f"Edit {file_path}: {edit_prompt}", 
                options=options
            ):
                results.append(message)
            
            return {
                "file": file_path, 
                "status": "success", 
                "results": results
            }
            
        except Exception as e:
            return {
                "file": file_path, 
                "status": "error", 
                "error": str(e)
            }
    
    # 並列タスクの作成と実行
    tasks = [
        asyncio.create_task(safe_process_file(file_path, prompt))
        for file_path, prompt in files_and_prompts
    ]
    
    # タイムアウト付きで実行（60秒）
    try:
        results = await asyncio.wait_for(
            asyncio.gather(*tasks),
            timeout=60.0
        )
        return results
    except asyncio.TimeoutError:
        return [{"status": "error", "error": "Operation timed out"}]
```

### 3. 10個のファイルを一斉に修正する実例

```python
async def batch_edit_ten_files():
    """10個のファイルを一斉に修正"""
    
    # 修正対象のファイルと指示
    files_to_modify = [
        ("src/models/user.py", "Add validation methods and type hints"),
        ("src/models/product.py", "Implement inventory tracking"),
        ("src/models/order.py", "Add status management"),
        ("src/services/auth.py", "Implement JWT authentication"),
        ("src/services/payment.py", "Add payment gateway integration"),
        ("src/api/routes/users.py", "Add CRUD endpoints"),
        ("src/api/routes/products.py", "Implement search functionality"),
        ("src/utils/validators.py", "Create input validation functions"),
        ("src/utils/formatters.py", "Add data formatting utilities"),
        ("src/config/settings.py", "Update configuration structure")
    ]
    
    results = await robust_parallel_processor(files_to_modify)
    
    # 結果の集計
    success_count = sum(1 for r in results if r.get("status") == "success")
    error_count = sum(1 for r in results if r.get("status") == "error")
    
    print(f"Successfully processed: {success_count} files")
    print(f"Errors encountered: {error_count} files")
    
    # エラーの詳細を表示
    for result in results:
        if result.get("status") == "error":
            print(f"Error in {result['file']}: {result['error']}")
    
    return results

# 実行
import anyio
anyio.run(batch_edit_ten_files)
```

## 代替アプローチ

### 1. 単一プロンプトで複数ファイル編集

並列処理の代わりに、1つのプロンプトで複数ファイルの編集を依頼する方法：

```python
async def edit_multiple_files_single_prompt():
    """単一のプロンプトで複数ファイルを編集"""
    
    prompt = """
    Please make the following changes to multiple files:
    
    1. src/models/user.py - Add validation methods and type hints
    2. src/models/product.py - Implement inventory tracking
    3. src/models/order.py - Add status management
    4. src/services/auth.py - Implement JWT authentication
    5. src/services/payment.py - Add payment gateway integration
    6. src/api/routes/users.py - Add CRUD endpoints
    7. src/api/routes/products.py - Implement search functionality
    8. src/utils/validators.py - Create input validation functions
    9. src/utils/formatters.py - Add data formatting utilities
    10. src/config/settings.py - Update configuration structure
    
    Process all files and make the requested changes.
    """
    
    options = ClaudeCodeOptions(
        allowed_tools=["Read", "Write", "Edit", "MultiEdit"],
        permission_mode='acceptEdits',
        max_turns=10  # 複数ファイル処理のため増やす
    )
    
    async for message in query(prompt=prompt, options=options):
        print(message)
```

### 2. セマフォを使った同時実行数の制限

```python
async def controlled_parallel_processing(files_and_prompts, max_concurrent=3):
    """同時実行数を制限した並列処理"""
    
    # セマフォで同時実行数を制限
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_with_semaphore(file_path, prompt):
        async with semaphore:
            return await process_file(file_path, prompt)
    
    tasks = [
        asyncio.create_task(process_with_semaphore(file_path, prompt))
        for file_path, prompt in files_and_prompts
    ]
    
    return await asyncio.gather(*tasks)
```

## 注意事項

### 1. 制限事項
- **API レート制限**: Anthropic APIのレート制限に注意
- **プロセス制限**: Claude Code CLIの内部実装による制限の可能性
- **ファイル競合**: 同じファイルへの同時編集は避ける

### 2. ベストプラクティス
- 独立したファイルのみを並列処理する
- 適切なエラーハンドリングを実装する
- タイムアウトを設定する
- 同時実行数を制限する（3-5個程度を推奨）

### 3. パフォーマンス考慮事項
- 並列処理が常に高速とは限らない
- ファイルの依存関係を考慮する
- 大規模な変更は段階的に実行する

## まとめ

Claude Code SDKで10個のファイルを一斉に修正することは技術的に可能です。`asyncio.gather`を使用して複数の`query()`を並列実行できますが、公式にサポートされた方法ではないため、実装時は注意が必要です。単一のプロンプトで複数ファイルの編集を依頼する方法も検討する価値があります。