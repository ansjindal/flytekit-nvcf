"""Basic example to use NVCF tasks in Flyte workflows."""

import os

from flytekit import workflow

from flytekitplugins.nvcf import nvcf_task

# Get API key and org name from environment variables
api_key = os.environ.get("NVCF_API_KEY")
org_name = os.environ.get("NGC_ORG")

# Define an NVCF task
my_task_gfn = nvcf_task(
    name="nvcf-task-wf-remote-gfn",
    container_image=f"nvcr.io/{org_name}/tasks_sample:v1",
    gpu_specification={"gpu": "L40S", "instanceType": "gl40s_1.br25_2xlarge", "backend": "GFN"},
    container_args="python3 main.py",
    max_runtime_duration="PT1H",
    max_queued_duration="PT1H",
    termination_grace_period_duration="PT1H",
    result_handling_strategy="NONE",
    results_location=None,
    api_key=api_key,
    org_name=org_name,
)

my_task_dgx = nvcf_task(
    name="nvcf-task-wf-remote",
    container_image=f"nvcr.io/{org_name}/tasks_sample:v1",
    gpu_specification={"gpu": "L40", "instanceType": "DGX-CLOUD.GPU.L40_2x", "backend": "nvcf-dgxc-k8s-forge-az28-prd1"},
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
    result_gfn = my_task_gfn()
    result_dgx = my_task_dgx()
    return result_gfn, result_dgx


# For local execution
if __name__ == "__main__":
    print(my_workflow())
