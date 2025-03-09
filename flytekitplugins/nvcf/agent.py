"""Agent implementation for NVCF tasks."""

import asyncio
import datetime
import logging
from typing import Any, Dict, List, Optional

import simplejson
from flytekit import FlyteContext
from flytekit.extend.backend.base_agent import (
    AgentRegistry,
    AsyncAgentBase,
    AsyncAgentExecutorMixin,
    Resource,
)
from flytekit.models.literals import LiteralMap
from flytekit.models.task import TaskTemplate
from flyteidl.core.execution_pb2 import TaskExecution
from isodate import parse_duration

# Import NGC SDK
from ngcsdk import Client
from nvcf.api.deployment_spec import GPUSpecification

from flytekitplugins.nvcf.models import NVCFMetadata

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler if it doesn't exist
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


class NVCFAgent(AsyncAgentExecutorMixin, AsyncAgentBase):
    """Agent for executing tasks on NVIDIA Cloud Functions (NVCF) using the NGC SDK."""

    name = "NVCF Agent"  # Define as class variable

    def __init__(self):
        """Initialize the NVCF agent."""
        self._task_type_name = "nvcf_task"
        super().__init__(task_type_name=self._task_type_name, metadata_type=NVCFMetadata)

    @property
    def task_type_name(self):
        """Return the task type name."""
        return self._task_type_name

    def _get_client(self, metadata: NVCFMetadata) -> Client:
        """Create and configure an NGC client."""
        client = Client()
        client.configure(api_key=metadata.api_key, org_name=metadata.org_name)
        return client

    async def create(
        self,
        task_template: TaskTemplate,
        inputs: Optional[LiteralMap] = None,
        output_prefix: str = None,
        task_execution_metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> NVCFMetadata:
        """Submit a task to NVCF using NGC SDK.

        Args:
            task_template: Task template containing configuration
            inputs: Optional input literals
            output_prefix: Optional output prefix
            task_execution_metadata: Optional task execution metadata

        Returns:
            NVCFMetadata containing task information
        """
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
                api_key=metadata.api_key,
                org_name=metadata.org_name,
                base_url=metadata.base_url,
                task_id=task_id,
                name=name,
                status=output.task.status,
                percent_complete=0,
                created_at=output.task.createdAt,
            )
        except Exception as e:
            logger.error(f"Failed to create NVCF task: {str(e)}")
            raise RuntimeError(f"Failed to create NVCF task: {str(e)}")

    async def get(self, resource_meta: NVCFMetadata, **kwargs) -> Resource:
        """Get the status of a NVCF task using NGC SDK."""
        task_id = resource_meta.task_id
        if not task_id:
            logger.warning("Task ID is missing in resource metadata")
            return Resource(
                phase=TaskExecution.UNDEFINED,
                message="Task ID is missing in resource metadata",
            )

        # Create NGC client
        client = self._get_client(resource_meta)
        try:
            # Use synchronous call since it works reliably with Flyte UI
            task_data = client.cloud_function.tasks.info(task_id)

            status = task_data.task.status
            phase, _ = self._map_status_to_phase(status)  # Ignore phase_version
            logger.info(f"Task {task_id}: Status: {status} Mapped to Flyte phase: {TaskExecution.Phase.Name(phase)}")

            if status == "FAILED":
                return Resource(
                    phase=phase,
                    message="Task execution failed"
                )

            outputs = None
            if status == "COMPLETED":
                logger.info(f"Task {task_id}: Task completed successfully, retrieving results")
                # try:
                #     # Use synchronous call for results too
                #     outputs = list(client.cloud_function.tasks.results(task_id))
                #     if outputs:
                #         logger.info(f"Task {task_id}: Retrieved results successfully")
                # except Exception as e:
                #     logger.warning(f"Failed to retrieve task results: {str(e)}")

            return Resource(
                phase=phase,
                message=str(status),
                outputs=outputs if outputs else None,
            )
        except Exception as e:
            logger.error(f"Failed to get NVCF task status: {str(e)}")
            return Resource(
                phase=TaskExecution.FAILED,
                message=f"Unable to determine task status: {str(e)}",
            )

    # async def _get_task_results(self, client: Client, task_id: str) -> List[Dict[str, Any]]:
    #     """Retrieve the results of a completed task."""
    #     try:
    #         # Run in a thread to avoid blocking the event loop
    #         loop = asyncio.get_event_loop()
    #         results = await loop.run_in_executor(
    #             None, lambda: list(client.cloud_function.tasks.results(task_id))
    #         )
    #         return results
    #     except Exception as e:
    #         logger.warning(f"Failed to retrieve task results: {str(e)}")
    #         return []

    # async def _get_task_events(self, client: Client, task_id: str) -> List[Dict[str, Any]]:
    #     """Retrieve the event logs for a task."""
    #     try:
    #         events = await asyncio.wait_for(
    #             asyncio.to_thread(lambda: list(client.cloud_function.tasks.events(task_id))),
    #             timeout=2.0
    #         )
    #         return events
    #     except asyncio.TimeoutError:
    #         logger.warning(f"Task {task_id}: Events retrieval timed out")
    #         return []
    #     except Exception as e:
    #         logger.warning(f"Failed to retrieve task events: {str(e)}")
    #         return []

    def _map_status_to_phase(self, status: str) -> tuple:
        """Map NVCF status to Flyte execution phase.

        Returns:
            tuple: (TaskExecution phase, phase version)
            Phase version is used to determine the order of states when multiple states map to the same phase.
        """
        # Log the incoming status for debugging
        logger.debug(f"Mapping NVCF status: {status}")

        if status == "QUEUED":
            return TaskExecution.QUEUED, 0
        elif status in ["LAUNCHED", "RUNNING"]:
            return TaskExecution.RUNNING, 0
        elif status == "COMPLETED":
            return TaskExecution.SUCCEEDED, 0
        elif status in ["FAILED", "ERRORED", "EXCEEDED_MAX_RUNTIME_DURATION", "EXCEEDED_MAX_QUEUED_DURATION"]:
            return TaskExecution.FAILED, 0
        elif status == "CANCELED":
            return TaskExecution.ABORTED, 0
        else:
            logger.warning(f"Unknown NVCF status: {status}, mapping to UNDEFINED")
            return TaskExecution.UNDEFINED, 0

    async def delete(
        self, resource_meta: NVCFMetadata, **kwargs
    ) -> None:
        """Cancel and delete a NVCF task using NGC SDK."""
        task_id = resource_meta.task_id

        if not task_id:
            logger.warning("Task ID is missing in resource metadata, nothing to delete")
            return

        # Create NGC client
        client = self._get_client(resource_meta)

        try:
            # First try to cancel the task if it's still running
            status = resource_meta.status
            if status in ["QUEUED", "LAUNCHED", "RUNNING"]:
                try:
                    # Run in a thread to avoid blocking the event loop
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(
                        None, lambda: client.cloud_function.tasks.cancel(task_id)
                    )
                    logger.info(f"Canceled NVCF task with ID: {task_id}")

                    # Add a small delay to allow the cancellation to take effect
                    await asyncio.sleep(2)

                except Exception as e:
                    logger.warning(f"Failed to cancel task, proceeding to delete: {str(e)}")

            # Then delete the task
            try:
                loop = asyncio.get_event_loop()
                # Handle the case where delete returns an empty response
                await loop.run_in_executor(None, lambda: self._safe_delete(client, task_id))
                logger.info(f"Deleted NVCF task with ID: {task_id}")
            except Exception as e:
                # If deletion fails, check if the task still exists
                try:
                    task_info = await loop.run_in_executor(
                        None, lambda: client.cloud_function.tasks.info(task_id)
                    )
                    logger.error(f"Task still exists with status: {task_info.task.status}")
                    raise RuntimeError(f"Failed to delete task: {str(e)}")
                except Exception:
                    # If we can't get task info, it might be already deleted
                    logger.info(f"Task {task_id} appears to be already deleted or inaccessible")
        except Exception as e:
            logger.error(f"Failed to delete NVCF task: {str(e)}")
            raise RuntimeError(f"Failed to delete NVCF task: {str(e)}")

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
            raise e

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


# Create and register the agent
agent = NVCFAgent()
AgentRegistry.register(agent)
logger.info(f"Registering NVCF agent with name: {agent.name}")
