# Haconiwa バージョン管理スクリプト

## 概要

Haconiwaプロジェクトのバージョンを一括で更新するスクリプトです。

## 使用方法

### 1. 基本的な使用方法

```bash
# 特定のバージョンに更新
python scripts/bump_version.py --version 0.7.0 --type release

# 開発版バージョンに更新
python scripts/bump_version.py --version 0.7.1-dev --type development
```

### 2. 自動インクリメント

```bash
# パッチバージョンをインクリメント (0.6.3 → 0.6.4)
python scripts/bump_version.py --patch

# マイナーバージョンをインクリメント (0.6.3 → 0.7.0)
python scripts/bump_version.py --minor

# メジャーバージョンをインクリメント (0.6.3 → 1.0.0)
python scripts/bump_version.py --major
```

### 3. バージョンタイプ指定

```bash
# リリース版
python scripts/bump_version.py --version 1.0.0 --type release

# 開発版
python scripts/bump_version.py --version 1.1.0-dev --type development

# パッチリリース
python scripts/bump_version.py --patch --type patch
```

## 更新されるファイル

スクリプトは以下のファイルを自動的に更新します：

1. **`pyproject.toml`** - パッケージバージョン
2. **`.github/workflows/ci.yml`** - CI/CDでのPyPIバージョン指定
3. **`src/haconiwa/__init__.py`** - `__version__` 変数
4. **`CHANGELOG.md`** - 新しいリリースセクション追加
5. **`README.md`** - インストール例のバージョン更新

## 実行例

```bash
$ python scripts/bump_version.py --version 0.7.0 --type release

🔄 バージョン更新: 0.6.3 → 0.7.0
📝 更新タイプ: release

✅ pyproject.toml: 0.7.0
✅ ci.yml: haconiwa==0.7.0
✅ __init__.py: __version__ = "0.7.0"
✅ CHANGELOG.md: [0.7.0] セクション追加
✅ README.md: インストール例を 0.7.0 に更新

🎉 バージョン 0.7.0 への更新が完了しました！

次のステップ:
1. git add .
2. git commit -m "bump: version 0.6.3 → 0.7.0"
3. git tag v0.7.0
4. git push origin main --tags
```

## リリースワークフロー

### 通常リリース

```bash
# 1. バージョン更新
python scripts/bump_version.py --version 0.7.0 --type release

# 2. コミット・タグ作成
git add .
git commit -m "bump: version 0.6.3 → 0.7.0"
git tag v0.7.0

# 3. プッシュ
git push origin main --tags

# 4. PyPI デプロイ（GitHub Actionsで自動実行）
```

### 開発版リリース

```bash
# 1. 開発版バージョン更新
python scripts/bump_version.py --version 0.7.1-dev --type development

# 2. コミット
git add .
git commit -m "bump: version 0.7.0 → 0.7.1-dev"
git push origin dev
```

### パッチリリース

```bash
# 1. パッチバージョン自動インクリメント
python scripts/bump_version.py --patch --type patch

# 2. コミット・タグ
git add .
git commit -m "bump: patch version $(git describe --tags --abbrev=0) → $(git describe --tags --abbrev=0 | sed 's/v//')"
git tag v$(cat pyproject.toml | grep version | cut -d'"' -f2)
git push origin main --tags
```

## エラー対応

### よくあるエラー

1. **バージョン形式エラー**
   ```
   ValueError: 無効なバージョン形式: invalid.version
   ```
   → セマンティックバージョニング形式 (`x.y.z`) で指定してください

2. **ファイルが見つからない**
   ```
   FileNotFoundError: pyproject.toml が見つかりません
   ```
   → プロジェクトルートで実行してください

3. **権限エラー**
   ```
   PermissionError: ファイルへの書き込み権限がありません
   ```
   → ファイルが読み取り専用になっていないか確認してください

## カスタマイズ

スクリプトの動作をカスタマイズしたい場合は、`VersionBumper` クラスの以下のメソッドを編集してください：

- `update_pyproject_toml()` - pyproject.toml更新ロジック
- `update_ci_workflow()` - CI/CD設定更新ロジック
- `update_changelog()` - CHANGELOG生成ロジック

## 注意事項

- バックアップを取ってから実行することをお勧めします
- Git作業ディレクトリが清潔な状態で実行してください
- CI/CDパイプラインが正常に動作することを確認してください