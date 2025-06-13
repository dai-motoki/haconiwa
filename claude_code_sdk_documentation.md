# Claude Code SDK ドキュメント

## 概要

Claude Code SDKは、Claude Codeをアプリケーションにプログラマティックに統合するためのツールです。このSDKを使用することで、AIパワードのコーディングアシスタントやツールを構築できます。

## 利用可能なSDK

### 1. Python SDK
- **パッケージ名**: `claude-code-sdk`
- **インストール**: `pip install claude-code-sdk`

### 2. TypeScript/JavaScript SDK  
- **パッケージ名**: `@anthropic-ai/claude-code`
- **インストール**: `npm install @anthropic-ai/claude-code`

### 3. コマンドラインSDK
- ターミナルから直接利用可能

## 基本的な使用例

### Python SDK

```python
import anyio
from claude_code_sdk import query, ClaudeCodeOptions, Message

async def main():
    messages: list[Message] = []
    async for message in query(
        prompt="Write a haiku about foo.py",
        options=ClaudeCodeOptions(max_turns=3)
    ):
        messages.append(message)
        print(message)

anyio.run(main)
```

### TypeScript SDK

```typescript
import { query } from "@anthropic-ai/claude-code";

async function main() {
    for await (const message of query({
        prompt: "Write a haiku about foo.py",
        options: { maxTurns: 3 }
    })) {
        console.log(message);
    }
}

main();
```

## 主な設定オプション (ClaudeCodeOptions)

- **`max_turns`**: 会話の最大ターン数
- **`system_prompt`**: カスタムシステムプロンプト
- **`cwd`**: 作業ディレクトリ（文字列またはPathオブジェクト）
- **`allowed_tools`**: 許可するツールのリスト（例: "Read", "Write", "Bash"）
- **`permission_mode`**: 権限処理モード（例: "acceptEdits"）

## 主な機能

### 1. 非インタラクティブな実行
プログラムからClaude Codeを呼び出し、結果を取得

### 2. マルチターン会話
複数回のやり取りを通じた対話的なコーディング支援

### 3. MCP (Model Context Protocol) サーバー統合
外部コンテキストプロバイダーとの連携

### 4. ツール権限の細かい制御
使用可能なツールを明示的に指定

### 5. 出力形式の選択
- テキスト形式
- JSON形式
- ストリーミング形式

## 高度な機能

### 前回の会話の再開
```python
async for message in query(
    prompt="Continue from where we left off",
    options=ClaudeCodeOptions(
        resume_conversation_id="previous-conversation-id"
    )
):
    print(message)
```

### カスタムシステムプロンプトの追加
```python
options = ClaudeCodeOptions(
    system_prompt="Always write clean, well-documented code"
)
```

### 権限プロンプトツールのカスタマイズ
独自の権限確認フローを実装可能

## 統合例

### GitHub Actions
Claude Code GitHub Actionsを使用することで、以下が可能：
- 自動コードレビュー
- PR作成
- イシュートリアージ

### IDE統合
- VS Code拡張機能（ベータ版）
- JetBrains IDE拡張機能（ベータ版）

## リソース

- **公式ドキュメント**: https://docs.anthropic.com/en/docs/claude-code/sdk
- **GitHubリポジトリ**: https://github.com/anthropics/claude-code
- **PyPI (Python)**: https://pypi.org/project/claude-code-sdk/
- **npm (TypeScript)**: https://www.npmjs.com/package/@anthropic-ai/claude-code

## 注意事項

- Anthropic APIキーが必要
- Node.js環境が必要（TypeScript SDK使用時）
- 適切なエラーハンドリングを実装することを推奨