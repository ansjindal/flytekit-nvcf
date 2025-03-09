import os

from flytekit import workflow

from flytekitplugins.nvcf import nvcf_task

# Get API key and org name from environment variables
api_key = os.environ.get("NVCF_API_KEY","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")
org_name = os.environ.get("NGC_ORG","0530795645140221")

# Define an NVCF task
my_task = nvcf_task(
    name="my-nvcf-task",
    container_image="nvcr.io/0530795645140221/tasks_sample:latest",
    gpu_specification={"gpu": "L40S", "instanceType": "gl40s_1.br25_2xlarge", "backend": "GFN"},
    container_args="python3 main.py",
    max_runtime_duration="PT1H",
    max_queued_duration="PT1H",
    termination_grace_period_duration="PT1H",
    result_handling_strategy="",
    results_location=f"{org_name}/task-results",
    api_key=api_key,
    org_name=org_name,
    secrets=[
        {
            "name": "NGC_API_KEY",  # Well-known secret name for uploading results
            "value": api_key,
        }
    ],
)


# Define a workflow that uses the NVCF task
@workflow
def my_workflow():
    result = my_task()
    return result


# For local execution
if __name__ == "__main__":
    print(my_workflow())
