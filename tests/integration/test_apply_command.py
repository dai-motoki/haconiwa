import pytest
from typer.testing import CliRunner
from pathlib import Path
from haconiwa.cli import app
from unittest.mock import MagicMock
import subprocess

runner = CliRunner()

@pytest.fixture(autouse=True)
def mock_tmux(monkeypatch):
    """TMUXの呼び出しをすべてモック化する"""
    mock_run = MagicMock(return_value=MagicMock(returncode=0, stdout=""))
    monkeypatch.setattr("subprocess.run", mock_run)
    return mock_run

def test_apply_creates_task_directories_with_slashes(tmp_path: Path):
    """
    `haconiwa apply` コマンドが、スラッシュを含むタスクディレクトリを正しく作成することをテストする。
    """
    # テスト用の設定ファイルを作成
    test_company_yaml = tmp_path / "test-haconiwa-dev-company-ci.yaml"
    test_company_yaml.write_text("""
apiVersion: haconiwa.dev/v1
kind: Organization
metadata:
  name: haconiwa-dev-company-org
spec:
  companyName: "Haconiwa Development Company"
  hierarchy:
    departments:
      - id: "executive"
        name: "Executive Team"
        roles:
          - { title: "Chief Executive Officer", agentId: "ceo-motoki" }
          - { title: "Chief Technology Officer", agentId: "cto-yamada" }
---
apiVersion: haconiwa.dev/v1
kind: Task
spec:
  taskBranchName: feature/01_ai_strategy
  assignee: "ceo-motoki"
---
apiVersion: haconiwa.dev/v1
kind: Task
spec:
  taskBranchName: feature/02_tech_architecture
  assignee: "cto-yamada"
""")
    
    test_world_yaml = tmp_path / "test-haconiwa-world-ci.yaml"
    test_world_yaml.write_text(f"""
apiVersion: haconiwa.dev/v1
kind: Space
metadata:
  name: test-world
spec:
  nations:
  - cities:
    - villages:
      - companies:
        - name: haconiwa-dev-company
          basePath: "{str(tmp_path / 'haconiwa-dev-company')}"
          organizationRef: "haconiwa-dev-company-org"
          configFile: "{str(test_company_yaml)}"
          gitRepo:
            url: "https://example.com/repo.git" # モックするのでURLはなんでも良い
""")

    # `git init`をシミュレート
    main_repo_path = tmp_path / "haconiwa-dev-company/tasks/main"
    main_repo_path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=main_repo_path, check=True)
    subprocess.run(["git", "-C", str(main_repo_path), "commit", "--allow-empty", "-m", "Initial commit"])

    # コマンドを実行
    result = runner.invoke(app, ["apply", "-f", str(test_world_yaml), "--no-attach"])

    # 検証
    assert result.exit_code == 0
    assert "haconiwa-dev-company" in result.stdout
    assert "feature/01_ai_strategy" in result.stdout
    
    task_dir_1 = tmp_path / "haconiwa-dev-company/tasks/feature/01_ai_strategy"
    task_dir_2 = tmp_path / "haconiwa-dev-company/tasks/feature/02_tech_architecture"
    
    assert task_dir_1.is_dir()
    assert task_dir_2.is_dir()
    
    # .haconiwa/agent_assignment.json が作成されていることを確認
    assert (task_dir_1 / ".haconiwa/agent_assignment.json").is_file() 