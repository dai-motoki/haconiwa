__all__ = ["TaskManager"]

class TaskManager:
    def __init__(self):
        self.tasks = []

    def add_task(self, task):
        self.tasks.append(task)

    def remove_task(self, task):
        self.tasks.remove(task)

    def list_tasks(self):
        return self.tasks

    def clear_tasks(self):
        self.tasks.clear()

# git-worktree integration functionality can be added here
