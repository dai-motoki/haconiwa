# haconiwa/agent/__init__.py

"""
Agent Integration Package
エージェント統合パッケージ

Claude Code、Cursor、その他のエージェントツールとの統合機能を提供します。
"""

class Agent:
    def __init__(self):
        self.agents = []

    def register_agent(self, agent):
        self.agents.append(agent)

    def get_agents(self):
        return self.agents

# エージェント管理機能のインスタンスを作成
agent_manager = Agent()