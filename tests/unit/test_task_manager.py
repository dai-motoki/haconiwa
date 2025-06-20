import pytest
from unittest.mock import MagicMock, call
from pathlib import Path
from haconiwa.task.manager import TaskManager

@pytest.fixture
def task_manager(monkeypatch):
    """
    TaskManagerのテスト用のフィクスチャ。
    subprocess.runとPath.mkdirをモック化する。
    """
    # TaskManagerはシングルトンのため、テストごとにリセットする
    if TaskManager._instance:
        TaskManager._instance = None
        TaskManager._initialized = False

    manager = TaskManager()

    # subprocess.runをモック化
    mock_subprocess_run = MagicMock(return_value=MagicMock(returncode=0))
    monkeypatch.setattr("subprocess.run", mock_subprocess_run)
    manager.mock_subprocess_run = mock_subprocess_run

    # Path.mkdirとPath.existsをモック化
    mock_mkdir = MagicMock()
    monkeypatch.setattr(Path, "mkdir", mock_mkdir)
    manager.mock_mkdir = mock_mkdir

    mock_exists = MagicMock(return_value=True) # 常に存在すると仮定
    monkeypatch.setattr(Path, "exists", mock_exists)
    
    # _find_space_base_pathが常に有効なパスを返すようにする
    monkeypatch.setattr(manager, '_find_space_base_path', lambda x: Path(f"./{x}"))

    return manager

def test_create_worktree_with_slashes(task_manager):
    """
    タスク名にスラッシュが含まれる場合に、正しいgit worktreeコマンドが生成されるかをテストする。
    """
    task_name = "feature/01_cool_feature"
    branch_name = "feature/01_cool_feature"
    space_ref = "test-company"
    
    config = {
        "name": task_name,
        "branch": branch_name,
        "space_ref": space_ref,
        "worktree": True,
    }

    task_manager._create_worktree(task_name, branch_name, space_ref, config)

    # git worktree add コマンドが正しい引数で呼び出されたかを確認
    expected_worktree_path = Path(f"./{space_ref}/tasks/{task_name}")
    expected_main_repo_path = Path(f"./{space_ref}/tasks/main")
    
    expected_command = [
        "git",
        "-C",
        str(expected_main_repo_path),
        "worktree",
        "add",
        str(expected_worktree_path.absolute()),
        branch_name,
    ]
    
    # mock_subprocess_run.call_args_listの中から、worktree addコマンドを探す
    worktree_add_call = None
    for c in task_manager.mock_subprocess_run.call_args_list:
        if "worktree" in c.args[0] and "add" in c.args[0]:
            worktree_add_call = c
            break
            
    assert worktree_add_call is not None, "git worktree add command was not called"
    
    # コマンドの主要部分を検証（完全一致ではなく部分一致で堅牢に）
    actual_command = worktree_add_call.args[0]
    assert "worktree" in actual_command
    assert "add" in actual_command
    assert str(expected_worktree_path.absolute()) in actual_command
    assert branch_name in actual_command
    
    # 親ディレクトリが作成されたことを確認
    task_manager.mock_mkdir.assert_called_with(parents=True, exist_ok=True) 