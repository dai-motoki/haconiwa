#!/usr/bin/env python3
"""
Haconiwa バージョン一括更新スクリプト

Usage:
    python scripts/bump_version.py --version 0.7.0 --type release
    python scripts/bump_version.py --version 0.7.1-dev --type development
    python scripts/bump_version.py --patch  # パッチバージョンを自動インクリメント
    python scripts/bump_version.py --minor  # マイナーバージョンを自動インクリメント
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple


class VersionBumper:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.version_files = [
            "pyproject.toml",
            ".github/workflows/ci.yml", 
            "src/haconiwa/__init__.py",
            "CHANGELOG.md",
            "README.md"
        ]
    
    def get_current_version(self) -> str:
        """pyproject.tomlから現在のバージョンを取得"""
        pyproject_path = self.project_root / "pyproject.toml"
        content = pyproject_path.read_text()
        
        match = re.search(r'version = "([^"]+)"', content)
        if match:
            return match.group(1)
        raise ValueError("バージョンが見つかりません")
    
    def increment_version(self, current: str, increment_type: str) -> str:
        """バージョンを自動インクリメント"""
        # セマンティックバージョンの解析
        match = re.match(r"(\d+)\.(\d+)\.(\d+)(?:-(.+))?", current)
        if not match:
            raise ValueError(f"無効なバージョン形式: {current}")
        
        major, minor, patch, prerelease = match.groups()
        major, minor, patch = int(major), int(minor), int(patch)
        
        if increment_type == "patch":
            patch += 1
        elif increment_type == "minor":
            minor += 1
            patch = 0
        elif increment_type == "major":
            major += 1
            minor = 0
            patch = 0
        
        return f"{major}.{minor}.{patch}"
    
    def update_pyproject_toml(self, new_version: str) -> None:
        """pyproject.tomlのバージョンを更新"""
        file_path = self.project_root / "pyproject.toml"
        content = file_path.read_text()
        
        # バージョン行のみを更新（tool.mypyやtool.pytestは除外）
        updated = re.sub(
            r'^version = "[^"]+"',
            f'version = "{new_version}"',
            content,
            flags=re.MULTILINE
        )
        
        file_path.write_text(updated)
        print(f"✅ pyproject.toml: {new_version}")
    
    def update_ci_workflow(self, new_version: str) -> None:
        """CI/CDワークフローのPyPIバージョンを更新"""
        file_path = self.project_root / ".github/workflows/ci.yml"
        content = file_path.read_text()
        
        # PyPIインストール行を更新
        updated = re.sub(
            r'pip install haconiwa==[\d\.]+([-\w]*)?',
            f'pip install haconiwa=={new_version}',
            content
        )
        
        file_path.write_text(updated)
        print(f"✅ ci.yml: haconiwa=={new_version}")
    
    def update_init_py(self, new_version: str) -> None:
        """__init__.pyの__version__を更新"""
        file_path = self.project_root / "src/haconiwa/__init__.py"
        content = file_path.read_text()
        
        # __version__行を追加または更新
        if '__version__' in content:
            updated = re.sub(
                r'__version__ = "[^"]+"',
                f'__version__ = "{new_version}"',
                content
            )
        else:
            # ファイル先頭に追加
            updated = f'__version__ = "{new_version}"\n\n' + content
        
        file_path.write_text(updated)
        print(f"✅ __init__.py: __version__ = \"{new_version}\"")
    
    def update_changelog(self, new_version: str, version_type: str) -> None:
        """CHANGELOGに新しいセクションを追加"""
        file_path = self.project_root / "CHANGELOG.md"
        today = datetime.now().strftime("%Y-%m-%d")
        
        if file_path.exists():
            content = file_path.read_text()
        else:
            content = "# Changelog\n\n"
        
        # バージョンタイプに応じた説明
        if version_type == "development":
            description = "### 開発版"
        elif version_type == "release":
            description = "### リリース版"
        elif version_type == "patch":
            description = "### パッチリリース"
        else:
            description = "### 更新"
        
        # 新しいセクションを先頭に挿入
        new_section = f"""## [{new_version}] - {today}

{description}

- バージョン {new_version} をリリース

"""
        
        # "# Changelog"の後に挿入
        if "# Changelog" in content:
            updated = content.replace("# Changelog\n\n", f"# Changelog\n\n{new_section}")
        else:
            updated = new_section + content
        
        file_path.write_text(updated)
        print(f"✅ CHANGELOG.md: [{new_version}] セクション追加")
    
    def update_readme(self, new_version: str) -> None:
        """READMEのインストール例を更新"""
        file_path = self.project_root / "README.md"
        if not file_path.exists():
            return
        
        content = file_path.read_text()
        
        # pip install例を更新
        updated = re.sub(
            r'pip install haconiwa==[\d\.]+([-\w]*)?',
            f'pip install haconiwa=={new_version}',
            content
        )
        
        # pip install haconiwa (バージョン指定なし)は更新しない
        if updated != content:
            file_path.write_text(updated)
            print(f"✅ README.md: インストール例を {new_version} に更新")
    
    def bump_version(self, new_version: str = None, version_type: str = "release") -> None:
        """バージョンを一括更新"""
        current_version = self.get_current_version()
        
        if new_version is None:
            raise ValueError("新しいバージョンを指定してください")
        
        print(f"🔄 バージョン更新: {current_version} → {new_version}")
        print(f"📝 更新タイプ: {version_type}")
        print()
        
        # 各ファイルを更新
        self.update_pyproject_toml(new_version)
        self.update_ci_workflow(new_version)
        self.update_init_py(new_version)
        self.update_changelog(new_version, version_type)
        self.update_readme(new_version)
        
        print()
        print(f"🎉 バージョン {new_version} への更新が完了しました！")
        print()
        print("次のステップ:")
        print("1. git add .")
        print(f"2. git commit -m \"bump: version {current_version} → {new_version}\"")
        print("3. git tag v" + new_version)
        print("4. git push origin main --tags")


def main():
    parser = argparse.ArgumentParser(description="Haconiwa バージョン一括更新")
    
    # バージョン指定方法
    version_group = parser.add_mutually_exclusive_group(required=True)
    version_group.add_argument("--version", help="新しいバージョン (例: 0.7.0)")
    version_group.add_argument("--patch", action="store_true", help="パッチバージョンをインクリメント")
    version_group.add_argument("--minor", action="store_true", help="マイナーバージョンをインクリメント")
    version_group.add_argument("--major", action="store_true", help="メジャーバージョンをインクリメント")
    
    # バージョンタイプ
    parser.add_argument("--type", choices=["release", "development", "patch"], 
                       default="release", help="バージョンタイプ")
    
    args = parser.parse_args()
    
    # プロジェクトルートを特定
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    bumper = VersionBumper(project_root)
    
    try:
        if args.version:
            new_version = args.version
        else:
            current = bumper.get_current_version()
            if args.patch:
                new_version = bumper.increment_version(current, "patch")
            elif args.minor:
                new_version = bumper.increment_version(current, "minor")
            elif args.major:
                new_version = bumper.increment_version(current, "major")
        
        bumper.bump_version(new_version, args.type)
        
    except Exception as e:
        print(f"❌ エラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()