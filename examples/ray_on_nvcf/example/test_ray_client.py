from ray.job_submission import JobSubmissionClient, JobStatus
import time

# If using a remote cluster, replace 127.0.0.1 with the head node's IP address.
# Replace <function-id> and <API-KEY> with the actual values.
client = JobSubmissionClient("https://<function-id>.invocation.api.nvcf.nvidia.com",
    headers={"Authorization": "Bearer <API-KEY>"}
)
job_id = client.submit_job(
    # Entrypoint shell command to execute
    entrypoint="python gpu_matrix_multiply.py",
    # Path to the local directory that contains the script.py file
    runtime_env={"working_dir": "./"}
)
print(job_id)

def wait_until_status(job_id, status_to_wait_for, timeout_seconds=5):
    start = time.time()
    while time.time() - start <= timeout_seconds:
        status = client.get_job_status(job_id)
        print(f"status: {status}")
        if status in status_to_wait_for:
            break
        time.sleep(1)


wait_until_status(job_id, {JobStatus.SUCCEEDED, JobStatus.STOPPED, JobStatus.FAILED})
logs = client.get_job_logs(job_id)
print(logs)
