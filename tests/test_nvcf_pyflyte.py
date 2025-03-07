"""Tests for NVCF agent using pyflyte."""

import os
from typing import NamedTuple

from flytekit import task, workflow
from flytekitplugins.nvcf import NVCFTask


class TaskOutput(NamedTuple):
    """Output type for the NVCF task."""
    cuda_available: bool
    task_id: str


@task(task_config=NVCFTask(
    name="test-nvcf-task",
    task_config={
        "containerImage": "nvcr.io/nvidia/pytorch:23.12-py3",
        "gpuSpecification": {
            "gpu": "L40S",
            "instanceType": "gl40s_1.br25_2xlarge",
            "backend": "GFN",
        },
        "containerArgs": "python -c 'import torch; print(f'CUDA available: {torch.cuda.is_available()}')'",
        "maxRuntimeDuration": "PT5M",
        "maxQueuedDuration": "PT5M",
        "terminationGracePeriodDuration": "PT1M",
        "resultHandlingStrategy": "UPLOAD",
        "resultsLocation": "test-results",
        "apiKey": "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",
        "orgName": "0530795645140221"
    }
))
def nvcf_task() -> TaskOutput:
    """Task that runs on NVCF."""
    # This task will be executed on NVCF
    try:
        import torch
        cuda_available = torch.cuda.is_available()
    except ImportError:
        # If running locally without torch, return a mock result
        cuda_available = False

    return TaskOutput(
        cuda_available=cuda_available,
        task_id=os.getenv("NVCF_TASK_ID", "local-execution")
    )


@workflow
def nvcf_workflow() -> TaskOutput:
    """Workflow that runs the NVCF task."""
    return nvcf_task()


if __name__ == "__main__":
    # This allows running the workflow directly with pyflyte
    result = nvcf_workflow()
    print(f"Result: {result}")
