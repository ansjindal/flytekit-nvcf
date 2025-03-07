"""Script to run the NVCF workflow using pyflyte."""

import os
from flytekit.remote import FlyteRemote
from flytekit.configuration import Config

# Set required environment variables
os.environ["NVCF_API_KEY"] = os.getenv("NVCF_API_KEY", "")
os.environ["NVCF_ORG_NAME"] = os.getenv("NVCF_ORG_NAME", "")

if not os.getenv("NVCF_API_KEY") or not os.getenv("NVCF_ORG_NAME"):
    raise ValueError("NVCF_API_KEY and NVCF_ORG_NAME environment variables are required")

# Configure Flyte remote
remote = FlyteRemote(
    Config.for_sandbox(),
    "flytekit-nvcf",  # project name
    "development",    # domain
)

# Launch the workflow
execution = remote.execute(
    "flytekit-nvcf",
    "development",
    "test-nvcf-workflow",
    "1.0.0",
    inputs={},
)

# Wait for completion and get results
result = execution.wait_for_completion()
print("Workflow completed successfully!")
print(f"Result: {result}")
