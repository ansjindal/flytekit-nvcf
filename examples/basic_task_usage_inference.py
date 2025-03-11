"""Basic example to use NVCF tasks in Flyte workflows."""

import os

from flytekit import workflow

from flytekitplugins.nvcf import nvcf_task

# Get API key and org name from environment variables
api_key = os.environ.get("NVCF_API_KEY")
org_name = os.environ.get("NGC_ORG")

# Define an NVCF task

my_inference_task = nvcf_task(
    name="inference-test-task-onprem",
    container_image=f"nvcr.io/{org_name}/inference_task:v5",
    gpu_specification={"gpu": "A100X", "instanceType": "ON-PREM.GPU.A100X_1x", "backend": "a100x-colossus-new"},
    container_args="",
    max_runtime_duration="PT1H",
    max_queued_duration="PT1H",
    termination_grace_period_duration="PT1H",
    result_handling_strategy="NONE",
    results_location=None,
    api_key=api_key,
    org_name=org_name,
)


# Define a workflow that uses the NVCF task
@workflow
def my_workflow():
    """Run a task on NVIDIA Cloud Functions.

    This workflow demonstrates how to use NVCF to run GPU-accelerated tasks
    without managing your own infrastructure.

    Returns:
        The results from the NVCF task execution.
    """
    result = my_inference_task()
    return result


# For local execution
if __name__ == "__main__":
    print(my_workflow())

