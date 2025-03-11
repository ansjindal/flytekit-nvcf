"""Agent implementation for NVCF tasks."""

import asyncio
import datetime
import logging
from typing import Any, Dict, List, Optional

import simplejson
from flyteidl.core.execution_pb2 import TaskExecution, TaskLog
from flytekit.extend.backend.base_agent import (
    AgentRegistry,
    AsyncAgentBase,
    AsyncAgentExecutorMixin,
    Resource,
)
from flytekit.extend.backend.utils import convert_to_flyte_phase
from flytekit.models.literals import LiteralMap
from flytekit.models.task import TaskTemplate
from isodate import parse_duration

# Import NGC SDK
from ngcsdk import Client
from nvcf.api.deployment_spec import GPUSpecification

from flytekitplugins.nvcf.models import NVCFMetadata

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler if it doesn't exist
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


class NVCFAgent(AsyncAgentExecutorMixin, AsyncAgentBase):
    """Agent for executing tasks on NVIDIA Cloud Functions (NVCF)."""

    name = "NVCF Agent"  # Define as class variable

    def __init__(self):
        """Initialize the NVCF agent."""
        super().__init__(task_type_name="nvcf_task", metadata_type=NVCFMetadata)

    @property
    def name(self) -> str:
        """Return the agent name."""
        return "NVCF Agent"  # This will be the name displayed in the agent list

    @property
    def task_type_name(self):
        """Return the task type name."""
        return "nvcf_task"

    def _get_client(self, metadata: NVCFMetadata) -> Client:
        """Create and configure an NGC client."""
        client = Client()
        client.configure(api_key=metadata.api_key, org_name=metadata.org_name)
        return client

    async def create(
        self, task_template: TaskTemplate, inputs: Optional[LiteralMap] = None, **kwargs
    ) -> NVCFMetadata:
        """Create a new NVCF task."""
        metadata = self._get_metadata(task_template)

        # Extract task configuration from custom attributes
        task_config = task_template.custom.get("nvcf_config", {})
        if not task_config:
            raise ValueError("NVCF task configuration is missing.")

        # Create NGC client
        client = self._get_client(metadata)

        # Convert task configuration to NGC SDK format
        name = task_config.get("name")
        container_image = task_config.get("containerImage")
        container_args = task_config.get("containerArgs")

        # Convert environment variables to the format expected by NVCF SDK
        container_env = None
        if task_config.get("containerEnvironment"):
            container_env = [
                f"{env['key']}:{env['value']}" for env in task_config.get("containerEnvironment")
            ]

        # Convert GPU specification
        gpu_spec = task_config.get("gpuSpecification")
        if gpu_spec:
            gpu_specification = GPUSpecification(
                gpu=gpu_spec.get("gpu"),
                instance_type=gpu_spec.get("instanceType"),
                backend=gpu_spec.get("backend"),
            )
        else:
            raise ValueError("GPU specification is required")

        # Convert models
        models = None
        if task_config.get("models"):
            models = [
                f"{model.get('name')}:{model.get('version')}" for model in task_config.get("models")
            ]

        # Convert durations
        max_runtime_duration = None
        if task_config.get("maxRuntimeDuration"):
            max_runtime_duration = parse_duration(task_config.get("maxRuntimeDuration"))

        max_queued_duration = None
        if task_config.get("maxQueuedDuration"):
            max_queued_duration = parse_duration(task_config.get("maxQueuedDuration"))

        termination_grace_period_duration = None
        if task_config.get("terminationGracePeriodDuration"):
            termination_grace_period_duration = parse_duration(
                task_config.get("terminationGracePeriodDuration")
            )

        # Convert secrets
        secrets = None
        if task_config.get("secrets"):
            secrets = [
                f"{secret.get('name')}:{secret.get('value')}"
                for secret in task_config.get("secrets")
            ]

        # Create the task using NGC SDK
        try:
            # Run in a thread to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            output = await loop.run_in_executor(
                None,
                lambda: client.cloud_function.tasks.create(
                    name=name,
                    container_image=container_image,
                    container_args=container_args,
                    container_environment_variables=container_env,
                    gpu_specification=gpu_specification,
                    models=models,
                    max_runtime_duration=max_runtime_duration,
                    max_queued_duration=max_queued_duration,
                    termination_grace_period_duration=termination_grace_period_duration,
                    result_handling_strategy=task_config.get("resultHandlingStrategy", "UPLOAD"),
                    result_location=task_config.get("resultsLocation"),
                    secrets=secrets,
                ),
            )

            task_id = output.task.id
            logger.info(f"Created NVCF task with ID: {task_id}")

            # Return a more comprehensive NVCFMetadata object
            return NVCFMetadata(
                task_id=task_id,
                api_key=metadata.api_key,
                org_name=metadata.org_name,
                base_url=metadata.base_url,
                name=name,
                status=output.task.status,
                percent_complete=0,
                created_at=output.task.createdAt,
            )
        except Exception as e:
            logger.error(f"Failed to create NVCF task: {str(e)}")
            raise RuntimeError(f"Failed to create NVCF task: {str(e)}")

    async def get(self, resource_meta: NVCFMetadata, **kwargs) -> Resource:
        """Get the status and outputs of an NVCF task."""
        task_id = resource_meta.task_id

        if not task_id:
            logger.warning("Task ID is missing in resource metadata")
            return Resource(
                phase=TaskExecution.UNDEFINED,
                message="Task ID is missing in resource metadata",
            )
        client = self._get_client(resource_meta)

        try:
            loop = asyncio.get_event_loop()
            task_data = await loop.run_in_executor(
                None, lambda: client.cloud_function.tasks.info(task_id)
            )

            status = task_data.task.status
            percent_complete = getattr(task_data.task, "percentComplete", 0)

            # Map NVCF status to Flyte phase
            phase = self._map_status_to_phase(status)

            logger.info(
                f"Task {task_id}: Status: {status},  Flyte ph: {TaskExecution.Phase.Name(phase)}"
            )

            if status == "FAILED":
                return Resource(phase=phase, message="Task execution failed")

            # Create log links
            log_links = [
                TaskLog(
                    uri=f"https://nvcf.ngc.nvidia.com/tasks/{task_id}",
                    name="NVCF Console",
                )
            ]

            # Get outputs if task is completed
            if status == "COMPLETED":
                try:
                    logger.info(f"Task {task_id}: Task completed successfully, retrieving results")
                    # outputs = await self._get_task_results(client, task_id)
                except Exception as e:
                    logger.warning(f"Failed to retrieve task results: {str(e)}")

            # Update resource_meta with the latest status
            resource_meta.status = status
            resource_meta.percent_complete = percent_complete

            # Return Resource with phase, outputs, and log links
            return Resource(
                phase=phase,
                message=f"Task status: {status}, {percent_complete}% complete",
                log_links=log_links,
                outputs=None,
            )

        except Exception as e:
            logger.error(f"Failed to get NVCF task status: {str(e)}")
            return Resource(
                phase=TaskExecution.FAILED,
                message=f"Failed to get NVCF task status: {str(e)}",
            )

    async def _get_task_results(self, client: Client, task_id: str) -> List[Dict[str, Any]]:
        """Retrieve the results of a completed task."""
        try:
            # Run in a thread to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None, lambda: list(client.cloud_function.tasks.results(task_id))
            )
            return results
        except Exception as e:
            logger.warning(f"Failed to retrieve task results: {str(e)}")
            return []

    def _map_status_to_phase(self, status: str) -> TaskExecution.Phase:
        """Map NVCF task status to Flyte execution phase."""
        # Convert status to lowercase for convert_to_flyte_phase
        status = status.lower()

        # Map NVCF states to states that convert_to_flyte_phase understands
        if status == "queued":
            return convert_to_flyte_phase("pending")  # Will convert to INITIALIZING
        elif status in ["launched", "running"]:
            return convert_to_flyte_phase("running")
        elif status == "completed":
            return convert_to_flyte_phase("succeeded")
        elif status in ["errored", "exceeded_max_runtime_duration", "exceeded_max_queued_duration"]:
            return convert_to_flyte_phase("failed")
        elif status == "canceled":
            return convert_to_flyte_phase("canceled")
        else:
            return convert_to_flyte_phase("pending")  # Use pending for unknown state

    async def delete(self, resource_meta: NVCFMetadata, **kwargs) -> None:
        """Cancel and delete an NVCF task."""
        task_id = resource_meta.task_id
        if not task_id:
            logger.warning("Task ID is missing in resource metadata")

        client = self._get_client(resource_meta)

        try:
            try:
                loop = asyncio.get_event_loop()
                task_data = await loop.run_in_executor(
                    None, lambda: client.cloud_function.tasks.info(task_id)
                )
                status = task_data.task.status
                # Map NVCF status to Flyte phase
                phase = self._map_status_to_phase(status)

                logger.info(
                    f"Task {task_id}: Status: {status}, Flyte ph: {TaskExecution.Phase.Name(phase)}"
                )
                # Cancel if running
                if status in ["QUEUED", "LAUNCHED", "RUNNING"]:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(
                        None, lambda: client.cloud_function.tasks.cancel(task_id)
                    )
                    logger.info(f"Canceled NVCF task with ID: {task_id}")
                    await asyncio.sleep(2)
            except Exception as e:
                logger.info(f"Could not get task status, task may be already deleted: {str(e)}")

            # Try to delete the task
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, lambda: self._safe_delete(client, task_id))
                logger.info(f"Deleted NVCF task with ID: {task_id}")
            except Exception as e:
                logger.warning(f"Failed to delete task, but continuing: {str(e)}")
                # Don't raise an exception here, as the task might already be deleted

        except Exception as e:
            logger.error(f"Error during delete operation for task {task_id}: {str(e)}")

    def _safe_delete(self, client: Client, task_id: str) -> None:
        """Safely delete a task, handling empty responses."""
        try:
            # Try to delete the task
            response = client.cloud_function.tasks.delete(task_id)
            return response
        except simplejson.errors.JSONDecodeError:
            # If we get a JSON decode error, it might be an empty response
            # which is actually fine for deletion operations
            logger.info("Received empty response from delete operation, assuming success")
            return None
        except Exception as e:
            # Re-raise any other exceptions
            logger.warning(f"Failed to delete task, but continuing: {str(e)}")

    def _get_metadata(self, task_template: TaskTemplate) -> NVCFMetadata:
        """Extract NGC metadata from task template."""
        custom = task_template.custom or {}

        api_key = custom.get("api_key")
        org_name = custom.get("org_name")

        if not api_key:
            raise ValueError(
                "NVCF API key is missing. Please provide 'api_key' in task definition."
            )

        if not org_name:
            raise ValueError(
                "Organization name is missing. Please provide 'org_name' in task definition."
            )

        return NVCFMetadata(api_key=api_key, org_name=org_name)

    def _get_current_time(self) -> str:
        """Get the current time in a format suitable for NVCFMetadata."""
        return datetime.datetime.now().isoformat()


# Register the agent with Flyte
agent = NVCFAgent()
AgentRegistry.register(agent)
logger.info(f"Registering NVCF agent: {agent.name}")
