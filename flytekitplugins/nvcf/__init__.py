"""
NVIDIA Cloud Functions (NVCF) plugin for Flytekit.

This plugin allows Flyte tasks to run on NVIDIA Cloud Functions.
"""

from flytekitplugins.nvcf.models import NVCFTaskConfig
from flytekitplugins.nvcf.task import NVCFTask, nvcf_task

__all__ = [
    "NVCFTask",
    "nvcf_task",
    "NVCFTaskConfig",
]
