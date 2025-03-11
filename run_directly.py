"""Direct execution script for testing the NVCF agent."""

import asyncio
import logging
import os

from flytekit import FlyteContext
from flytekit.models.core.identifier import Identifier
from flytekit.models.task import TaskTemplate

# Import the agent
from flytekitplugins.nvcf.agent import NVCFAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set your NVCF API key
api_key = os.environ.get("NVCF_API_KEY", "")
org_name = os.environ.get("NGC_ORG", "")


async def main():
    """Run a direct test of the NVCF agent."""
    # Create an instance of the agent
    agent = NVCFAgent()

    # Create a mock task template with the necessary configuration
    task_template = TaskTemplate(
        id=Identifier(
            resource_type="task", project="test", domain="test", name="test", version="1"
        ),
        type="nvcf_task",
        metadata=None,
        interface=None,
        custom={
            "api_key": api_key,
            "org_name": org_name,
            "base_url": "https://api.nvct.nvidia.com/v1/nvct",
            "nvcf_config": {
                "name": "direct-agent-test",
                "containerImage": "nvcr.io/0530795645140221/tasks_sample:latest",
                "gpuSpecification": {
                    "gpu": "L40S",
                    "instanceType": "gl40s_1.br25_2xlarge",
                    "backend": "GFN",
                },
                "secrets": [
                    {
                        "name": "NGC_API_KEY",  # Well-known secret name for uploading results
                        "value": api_key,
                    }
                ],
                "containerArgs": "python3 main.py",
                "maxRuntimeDuration": "PT1H",
                "maxQueuedDuration": "PT1H",
                "terminationGracePeriodDuration": "PT1H",
                "resultHandlingStrategy": "UPLOAD",
                "resultsLocation": "0530795645140221/sample-task-results1",
            },
        },
    )

    # Get a Flyte context
    ctx = FlyteContext.current_context()

    try:
        # Create the NVCF task
        logger.info("Creating NVCF task...")
        resource_meta = await agent.create(ctx, task_template)

        print(resource_meta)
        task_id = resource_meta.task_id
        logger.info(f"Created NVCF task with ID: {task_id}")

        # Get the initial status
        resource_meta = await agent.get(ctx, resource_meta, task_template)
        logger.info(
            f"Initial task status: {resource_meta.status}, "
            f"{resource_meta.percent_complete}% complete"
        )

        # Immediately delete the task without waiting for completion
        logger.info("Immediately deleting task...")
        await agent.delete(ctx, resource_meta, task_template)
        logger.info("Task deleted")

        # Try to get the status after deletion (this should fail or return a not-found status)
        try:
            logger.info("Attempting to get status after deletion...")
            resource_meta = await agent.get(ctx, resource_meta, task_template)
            logger.info(f"Task status after deletion attempt: {resource_meta.status}")
        except Exception as e:
            logger.info(f"As expected, could not get task status after deletion: {str(e)}")

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
