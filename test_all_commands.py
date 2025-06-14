#!/usr/bin/env python3
"""Comprehensive test for all haconiwa commands to check implementation status."""

import subprocess
import sys
from typing import List, Tuple
import json


def run_command(cmd: List[str]) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, and stderr."""
    try:
        # Set PYTHONPATH to include src directory
        import os
        env = os.environ.copy()
        env["PYTHONPATH"] = "./src"
        
        result = subprocess.run(
            ["python", "src/haconiwa/cli.py"] + cmd,
            capture_output=True,
            text=True,
            timeout=5,
            env=env
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -2, "", str(e)


def test_command(cmd: List[str], description: str) -> dict:
    """Test a single command and return results."""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Command: haconiwa {' '.join(cmd)}")
    print('-'*60)
    
    exit_code, stdout, stderr = run_command(cmd)
    
    success = exit_code == 0 or (exit_code == 1 and "Missing" not in stderr and "No such" not in stderr)
    
    result = {
        "command": " ".join(cmd),
        "description": description,
        "exit_code": exit_code,
        "success": success,
        "has_output": bool(stdout.strip()),
        "error": stderr.strip() if stderr.strip() else None
    }
    
    if success and stdout:
        print(f"✅ SUCCESS - Output preview:")
        print(stdout[:200] + "..." if len(stdout) > 200 else stdout)
    else:
        print(f"❌ FAILED - Exit code: {exit_code}")
        if stderr:
            print(f"Error: {stderr[:200]}")
    
    return result


def main():
    """Test all haconiwa commands."""
    print("🧪 Haconiwa Command Implementation Test")
    print("="*60)
    
    # Define all commands to test
    test_cases = [
        # Main commands
        (["--help"], "Main help"),
        (["--version"], "Version info"),
        
        # Core commands
        (["core", "--help"], "Core help"),
        (["core", "init", "--help"], "Core init help"),
        (["core", "status", "--help"], "Core status help"),
        
        # Space commands (formerly company)
        (["space", "--help"], "Space help"),
        (["space", "list"], "Space list"),
        (["space", "ls"], "Space ls (alias)"),
        (["space", "start", "--help"], "Space start help"),
        (["space", "stop", "--help"], "Space stop help"),
        (["space", "attach", "--help"], "Space attach help"),
        (["space", "clone", "--help"], "Space clone help"),
        (["space", "run", "--help"], "Space run help"),
        (["space", "delete", "--help"], "Space delete help"),
        
        # Tool commands (NEW!)
        (["tool", "--help"], "Tool help"),
        (["tool", "list"], "Tool list"),
        (["tool", "install", "--help"], "Tool install help"),
        (["tool", "configure", "--help"], "Tool configure help"),
        (["tool", "scan-filepath", "--help"], "Tool scan-filepath help"),
        (["tool", "scan-db", "--help"], "Tool scan-db help"),
        
        # Tool parallel-dev commands (NEW!)
        (["tool", "parallel-dev", "--help"], "Tool parallel-dev help"),
        (["tool", "parallel-dev", "claude", "--help"], "Tool parallel-dev claude help"),
        (["tool", "parallel-dev", "status"], "Tool parallel-dev status"),
        (["tool", "parallel-dev", "history"], "Tool parallel-dev history"),
        (["tool", "parallel-dev", "cancel", "--help"], "Tool parallel-dev cancel help"),
        
        # Policy commands
        (["policy", "--help"], "Policy help"),
        (["policy", "ls"], "Policy list"),
        (["policy", "test", "--help"], "Policy test help"),
        (["policy", "delete", "--help"], "Policy delete help"),
        
        # Monitor commands
        (["monitor", "--help"], "Monitor help"),
        (["monitor", "help"], "Monitor detailed help"),
        (["mon", "--help"], "Monitor short alias help"),
        
        # World commands
        (["world", "--help"], "World help"),
        (["world", "create", "--help"], "World create help"),
        (["world", "list"], "World list"),
        (["world", "switch", "--help"], "World switch help"),
        
        # Agent commands
        (["agent", "--help"], "Agent help"),
        (["agent", "spawn", "--help"], "Agent spawn help"),
        (["agent", "ps"], "Agent ps"),
        (["agent", "kill", "--help"], "Agent kill help"),
        
        # Task commands
        (["task", "--help"], "Task help"),
        (["task", "new", "--help"], "Task new help"),
        (["task", "assign", "--help"], "Task assign help"),
        (["task", "status"], "Task status"),
        
        # Watch commands
        (["watch", "--help"], "Watch help"),
        (["watch", "tail", "--help"], "Watch tail help"),
        (["watch", "logs"], "Watch logs"),
        
        # Apply command (v1.0)
        (["apply", "--help"], "Apply help"),
        
        # Init command
        (["init", "--help"], "Init help"),
        
        # Deprecated commands (should still work)
        (["company", "--help"], "Company help (deprecated)"),
        (["resource", "--help"], "Resource help (deprecated)"),
    ]
    
    # Run all tests
    results = []
    for cmd, description in test_cases:
        result = test_command(cmd, description)
        results.append(result)
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    total = len(results)
    successful = sum(1 for r in results if r["success"])
    failed = total - successful
    
    print(f"\nTotal commands tested: {total}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    
    # List failed commands
    if failed > 0:
        print("\n❌ Failed commands:")
        for r in results:
            if not r["success"]:
                print(f"  - {r['description']}: {r['command']} (exit: {r['exit_code']})")
                if r["error"]:
                    print(f"    Error: {r['error'][:100]}")
    
    # Check specific new features
    print("\n🎯 New Feature Check:")
    new_features = [
        ("tool list", "Tool list command"),
        ("tool parallel-dev --help", "Parallel-dev subcommand"),
        ("tool parallel-dev claude --help", "Claude parallel execution"),
        ("tool parallel-dev status", "Status monitoring"),
        ("tool parallel-dev history", "Execution history"),
    ]
    
    for cmd_str, feature in new_features:
        cmd_found = any(r["command"] == cmd_str and r["success"] for r in results)
        status = "✅" if cmd_found else "❌"
        print(f"  {status} {feature}")
    
    # Save results
    with open("command_test_results.json", "w") as f:
        json.dump({
            "total": total,
            "successful": successful,
            "failed": failed,
            "results": results
        }, f, indent=2)
    
    print(f"\n📁 Detailed results saved to: command_test_results.json")
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()