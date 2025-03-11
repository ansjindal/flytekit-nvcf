"""Direct execution script for testing the NVCF agent."""

import asyncio
import logging
import os

from flyteidl.core.execution_pb2 import TaskExecution
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
                "name": "ansjindal-direct-agent-test-v1-gfn",
                "containerImage": f"nvcr.io/{org_name}/tasks_sample:v1",
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
                "resultHandlingStrategy": "NONE",
                "resultsLocation": None # f"{org_name}/sample-task-results1",
            },
        },
    )

    try:
        # Create the NVCF task
        logger.info("Creating NVCF task...")
        resource_meta = await agent.create(task_template=task_template)

        print(resource_meta)
        task_id = resource_meta.task_id
        logger.info(f"Created NVCF task with ID: {task_id}")

        # Poll for task completion
        logger.info("Waiting for task completion...")
        while True:
            resource = await agent.get(resource_meta=resource_meta)
            logger.info(
                f"Task status: {TaskExecution.Phase.Name(resource.phase)}, "
                f"{resource_meta.percent_complete}% complete"
            )

            if resource.phase in [
                TaskExecution.SUCCEEDED,
                TaskExecution.FAILED,
                TaskExecution.ABORTED,
            ]:
                break

            # Wait for 10 seconds before next poll
            await asyncio.sleep(10)

        logger.info(f"Task finished with phase: {TaskExecution.Phase.Name(resource.phase)}")

        # Delete the completed task
        # logger.info("Deleting completed task...")
        # await agent.delete(resource_meta=resource_meta)
        # logger.info("Task deleted")

        # Try to get the status after deletion
        try:
            logger.info("Attempting to get status after deletion...")
            resource = await agent.get(resource_meta=resource_meta)
            logger.info(
                f"Task status after deletion attempt: {TaskExecution.Phase.Name(resource.phase)}"
            )
        except Exception as e:
            logger.info(f"As expected, could not get task status after deletion: {str(e)}")

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
