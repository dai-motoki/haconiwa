"""Tool module for external tool integrations."""

from .parallel_dev import parallel_dev_app, ParallelDevManager

__all__ = [
    "parallel_dev_app",
    "ParallelDevManager"
]