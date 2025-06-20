# Haconiwa 開発戦略・ブランチ戦略・バージョン管理

## 🌿 ブランチ戦略

### 基本ブランチ構成

```
main (本番/リリース)
├── dev (開発統合)
├── feature/* (機能開発)
├── bugfix/* (バグ修正)
├── hotfix/* (緊急修正)
└── release/* (リリース準備)
```

### ブランチ詳細

#### 1. `main` ブランチ
- **用途**: 本番リリース用
- **保護**: プッシュ制限、PR必須
- **CI/CD**: PyPI版テスト、本番デプロイ
- **バージョン**: 安定版のみ (0.6.3, 0.7.0等)

#### 2. `dev` ブランチ  
- **用途**: 開発統合・次期リリース準備
- **CI/CD**: 開発版テスト (pip install -e .)
- **バージョン**: 開発版 (0.6.4-dev, 0.7.0-dev等)

#### 3. `feature/*` ブランチ
- **命名**: `feature/01_ai_strategy`, `feature/tmux_integration`
- **用途**: 新機能開発
- **マージ先**: `dev`ブランチ

#### 4. `release/*` ブランチ
- **命名**: `release/0.7.0`
- **用途**: リリース準備・最終テスト
- **作業**: バージョン更新、CHANGELOG更新
- **マージ先**: `main` + `dev`

## 🚀 CI/CD戦略

### 1. ブランチ別CI設定とインストール方法

| ワークフロー | 対象ブランチ | インストール方法 | 用途 |
|------------|------------|----------------|------|
| `ci.yml` | `main` | `pip install haconiwa==x.x.x` | **本番環境テスト** |
| `ci-dev.yml` | `dev`, `feature/*`, `bugfix/*` | `pip install -e .` | **開発環境テスト** |
| `ci-release.yml` | `release/*` | `pip install -e .` → wheel test | **リリース候補テスト** |

### 2. インストール方法の使い分け

#### 🔧 開発版 (`pip install -e .`)
```yaml
# 開発ブランチ用
- name: Install development version
  run: |
    pip install -e .[dev]  # editable install
```
**特徴:**
- コード変更が即座に反映
- デバッグしやすい
- 依存関係は pyproject.toml から解決

#### 📦 本番版 (`pip install haconiwa==x.x.x`)
```yaml
# main ブランチ用  
- name: Install production version
  run: |
    pip install haconiwa==0.6.3  # PyPI version
```
**特徴:**
- 実際のユーザー環境と同じ
- PyPI依存関係解決テスト
- インストール後の動作確認

#### 🚀 リリース候補版 (両方テスト)
```yaml
# release ブランチ用
- name: Install and test release candidate
  run: |
    pip install -e .          # 開発版でテスト
    python -m build           # パッケージビルド
    pip install dist/*.whl    # wheel版でテスト
```
**特徴:**
- 開発版とパッケージ版の両方をテスト
- リリース前の最終確認

### 2. テスト環境分離

| ブランチ | インストール方法 | 用途 |
|---------|----------------|------|
| `main` | `pip install haconiwa==0.6.3` | 本番環境テスト |
| `dev` | `pip install -e .` | 開発環境テスト |
| `feature/*` | `pip install -e .` | 機能開発テスト |

## 📦 バージョン管理戦略

### 1. セマンティックバージョニング

```
MAJOR.MINOR.PATCH[-PRERELEASE]

例:
0.6.3        # 安定版
0.7.0-dev    # 開発版
0.7.0-rc1    # リリース候補
1.0.0        # メジャーリリース
```

### 2. バージョン更新箇所

以下のファイルでバージョンを統一管理：

1. **`pyproject.toml`**
   ```toml
   version = "0.6.3"
   ```

2. **`.github/workflows/ci.yml`**  
   ```yaml
   pip install haconiwa==0.6.3
   ```

3. **`src/haconiwa/__init__.py`**
   ```python
   __version__ = "0.6.3"
   ```

4. **`CHANGELOG.md`**
   ```markdown
   ## [0.6.3] - 2025-06-20
   ```

5. **`README.md`** (インストール例)
   ```bash
   pip install haconiwa==0.6.3
   ```

## 🔧 バージョン管理自動化ツール

### 1. バージョン更新スクリプト

```bash
# scripts/bump_version.py
python scripts/bump_version.py --version 0.7.0 --type release
python scripts/bump_version.py --version 0.7.1-dev --type development
```

### 2. 自動更新対象ファイル

スクリプトで一括更新する対象：

- `pyproject.toml`
- `.github/workflows/ci.yml` (PyPI版バージョン)
- `src/haconiwa/__init__.py`
- `CHANGELOG.md` (新セクション追加)
- `README.md` (インストール例)
- `docs/` 内の関連ドキュメント

### 3. リリース自動化ワークフロー

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags: [ "v*" ]

jobs:
  release:
    steps:
      - name: Bump version
        run: python scripts/bump_version.py --version ${{ github.ref_name }}
      
      - name: Build and publish to PyPI
        run: |
          python -m build
          twine upload dist/*
      
      - name: Create GitHub Release
        uses: actions/create-release@v1
```

## 📋 開発ワークフロー

### 1. 機能開発フロー

```bash
# 1. 機能ブランチ作成
git checkout dev
git pull origin dev
git checkout -b feature/new_monitoring_system

# 2. 開発・テスト
pip install -e .
# 開発作業...

# 3. dev にマージ
git checkout dev
git merge feature/new_monitoring_system

# 4. リリース準備
git checkout -b release/0.7.0
python scripts/bump_version.py --version 0.7.0 --type release

# 5. main にマージ・タグ作成
git checkout main
git merge release/0.7.0
git tag v0.7.0
git push origin main --tags
```

### 2. ホットフィックスフロー

```bash
# 1. main から緊急修正ブランチ
git checkout main
git checkout -b hotfix/0.6.4

# 2. 修正・バージョン更新
python scripts/bump_version.py --version 0.6.4 --type patch

# 3. main と dev に両方マージ
git checkout main
git merge hotfix/0.6.4
git checkout dev  
git merge hotfix/0.6.4
```

## 🛠️ 実装優先順位

### Phase 1: 基本ブランチ戦略
1. `dev` ブランチ作成・保護設定
2. ブランチ別CI/CD設定
3. バージョン更新スクリプト作成

### Phase 2: 自動化強化
1. リリース自動化ワークフロー
2. CHANGELOG自動生成
3. バージョン管理の完全自動化

### Phase 3: 高度な機能
1. セマンティックリリース導入
2. 自動テスト環境分離
3. カナリアリリース対応

## 📄 関連ドキュメント

- [CONTRIBUTING.md](./CONTRIBUTING.md) - 開発参加ガイド
- [RELEASE_PROCESS.md](./RELEASE_PROCESS.md) - リリースプロセス
- [VERSION_MANAGEMENT.md](./VERSION_MANAGEMENT.md) - バージョン管理詳細

---

この戦略により、開発効率とリリース品質の両方を向上させることができます。