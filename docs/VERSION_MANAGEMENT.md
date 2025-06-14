# Haconiwa バージョン管理ガイド

このドキュメントは、haconiwaプロジェクトのバージョン管理プロセスについて説明します。

## 📋 バージョニング体系

このプロジェクトは[Semantic Versioning (SemVer)](https://semver.org/lang/ja/)に従います：

- **MAJOR** (`1.0.0`): 後方互換性のない変更
- **MINOR** (`0.1.0`): 後方互換性のある新機能追加
- **PATCH** (`0.0.1`): 後方互換性のあるバグ修正

## 🚀 リリースプロセス

### 自動リリース（推奨）

```bash
# 1. リリーススクリプトを使用
./scripts/release.sh 0.1.5

# 2. GitHubでRelease作成
# https://github.com/dai-motoki/haconiwa/releases/new
```

### 手動リリース

```bash
# 1. バージョン更新
# pyproject.toml の version を更新
# README_JA.md と README.md の最新バージョンを更新

# 2. CHANGELOG.md 更新
# 新しいバージョンのセクションを追加

# 3. パッケージビルド・アップロード
python -m build
python -m twine upload dist/*

# 4. Git操作
git add .
git commit -m "chore: release v0.1.5"
git tag -a "v0.1.5" -m "Release v0.1.5"
git push origin main
git push origin v0.1.5

# 5. GitHub Release作成
# https://github.com/dai-motoki/haconiwa/releases/new でリリース作成
```

## 📝 CHANGELOG更新

新しいリリースのたびに[CHANGELOG.md](../CHANGELOG.md)を更新：

```markdown
## [0.1.5] - 2025-01-07

### Added
- 新機能の説明

### Changed  
- 変更された機能の説明

### Fixed
- 修正されたバグの説明

### Deprecated
- 非推奨になった機能

### Removed
- 削除された機能

### Security
- セキュリティに関する修正
```

## 🏷️ Git タグ規則

- タグ形式: `v{MAJOR}.{MINOR}.{PATCH}` (例: `v0.1.4`)
- 注釈付きタグを使用: `git tag -a "v0.1.4" -m "Release v0.1.4"`
- タグメッセージには簡潔な変更概要を含める

## 📦 PyPI リリース

1. **テスト環境での確認**（推奨）
   ```bash
   python -m twine upload --repository testpypi dist/*
   ```

2. **本番環境へのアップロード**
   ```bash
   python -m twine upload dist/*
   ```

## 🔄 バージョン管理ファイル

### 更新が必要なファイル
- `pyproject.toml` - パッケージバージョン
- `README_JA.md` - 最新バージョン表示
- `README.md` - 最新バージョン表示  
- `CHANGELOG.md` - 変更履歴

### 自動生成ファイル
- `dist/` - ビルド成果物（`.gitignore`で除外済み）
- `build/` - ビルド一時ファイル（`.gitignore`で除外済み）

## 🔧 トラブルシューティング

### PyPIアップロード時のメタデータエラー

**エラー:** `InvalidDistribution: Metadata is missing required fields: Name, Version`

```bash
ERROR    InvalidDistribution: Metadata is missing required fields: Name, Version.
         Make sure the distribution includes the files where those fields are specified, and
         is using a supported Metadata-Version: 1.0, 1.1, 1.2, 2.0, 2.1, 2.2, 2.3.
```

**原因:** `pkginfo`ライブラリが古いバージョンの場合、メタデータの解析に問題が発生することがある

**解決方法:**
```bash
# pkginfoライブラリをアップグレード
pip install --upgrade pkginfo

# 再度ビルドしてアップロード
rm -rf dist/*
python -m build
twine upload dist/*
```

### src/レイアウトでのビルドエラー

**問題:** pyproject.tomlでsrc/ベースのプロジェクト構造を使用している場合のパッケージ認識エラー

**解決方法:** pyproject.tomlに以下の設定を追加：

```toml
[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
```

### その他の一般的なエラー

1. **twineの認証エラー**
   ```bash
   # PyPIのAPIトークンを使用する場合
   twine upload --username __token__ --password YOUR_API_TOKEN dist/*
   ```

2. **ビルドファイルの競合**
   ```bash
   # 古いビルドファイルをクリーン
   rm -rf dist/* build/*
   python -m build
   ```

## 📋 チェックリスト

リリース前の確認事項：

- [ ] 全てのテストがパス
- [ ] `CHANGELOG.md` が更新済み
- [ ] バージョン番号が正しく更新済み
- [ ] 必要な依存パッケージが最新（特に`pkginfo`, `twine`, `build`）
- [ ] PyPIアップロードが成功
- [ ] Gitタグが作成・プッシュ済み
- [ ] GitHub Releaseが作成済み
- [ ] 実際のインストールテスト完了

## 🔗 関連リンク

- 📄 [CHANGELOG.md](../CHANGELOG.md)
- 📦 [PyPI - haconiwa](https://pypi.org/project/haconiwa/)
- 🔖 [GitHub Releases](https://github.com/dai-motoki/haconiwa/releases)
- 📐 [Semantic Versioning](https://semver.org/lang/ja/)
- 📝 [Keep a Changelog](https://keepachangelog.com/ja/1.0.0/) 