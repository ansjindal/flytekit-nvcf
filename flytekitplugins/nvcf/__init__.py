"""
NVIDIA Cloud Functions (NVCF) plugin for Flytekit.

This plugin allows Flyte tasks to run on NVIDIA Cloud Functions.
"""

from flytekitplugins.nvcf.models import NVCFTaskConfig
from flytekitplugins.nvcf.task import NVCFTask, nvcf_task

# Import the agent to ensure it's registered
from flytekitplugins.nvcf.agent import agent  # noqa: F401

__all__ = [
    "NVCFTask",
    "nvcf_task",
    "NVCFTaskConfig",
    "agent",
]
