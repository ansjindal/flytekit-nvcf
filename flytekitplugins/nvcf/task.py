"""Task implementation for NVCF tasks."""

from typing import Any, Dict, List, Optional

from flytekit.core.interface import Interface
from flytekit.core.task import PythonTask, TaskMetadata

from flytekitplugins.nvcf.models import NVCFTaskConfig


class NVCFTask(PythonTask):
    """Task implementation for NVCF tasks."""

    def __init__(self, name: str, task_config: NVCFTaskConfig, **kwargs):
        """Initialize NVCF task.

        Args:
            name: Task name
            task_config: NVCF task configuration
            **kwargs: Additional task parameters
        """
        self._config = task_config

        metadata = kwargs.pop("metadata", TaskMetadata())

        # Define a simple interface - inputs and outputs can be customized as needed
        interface = kwargs.pop("interface", Interface())

        super().__init__(
            name=name, metadata=metadata, interface=interface, task_type="nvcf_task", **kwargs
        )

    def get_custom(self, settings):
        """Return custom task attributes for serialization."""
        return {
            "api_key": self._config.api_key,
            "org_name": self._config.org_name,
            "base_url": self._config.base_url,
            "nvcf_config": self._config.to_dict(),
        }

    def get_container(self, settings):
        """No container is needed as this runs via the agent."""
        return None

    def execute(self, **kwargs) -> Any:
        """Execute the task locally via the agent."""
        # The agent will handle the actual execution
        # This method is only called during local execution
        # Import here to avoid circular import
        from flytekit.extend.backend.base_agent import AgentRegistry

        agent = AgentRegistry.get_agent("nvcf_task")
        if not agent:
            raise RuntimeError("NVCF agent is not registered")

        # The agent will handle the execution
        return agent.execute(self, **kwargs)


def nvcf_task(
    name: str,
    container_image: str,
    gpu_specification: Dict[str, Any],
    container_args: Optional[str] = None,
    container_environment: Optional[List[Dict[str, str]]] = None,
    models: Optional[List[Dict[str, Any]]] = None,
    secrets: Optional[List[Dict[str, str]]] = None,
    max_runtime_duration: Optional[str] = None,
    max_queued_duration: Optional[str] = "PT6H",
    termination_grace_period_duration: Optional[str] = "PT15M",
    result_handling_strategy: str = "UPLOAD",
    results_location: Optional[str] = None,
    api_key: str = None,
    org_name: str = None,
    base_url: str = "https://api.nvct.nvidia.com/v1/nvct",
    **kwargs,
) -> NVCFTask:
    """
    Create a Flyte task that runs on NVIDIA Cloud Functions.

    Args:
        name: Name of the NVCF task
        container_image: Container image to run
        gpu_specification: GPU specification (gpu, instanceType, backend)
        container_args: Optional container command
        container_environment: Optional environment variables
        models: Optional models to use
        secrets: Secrets to pass to the task
        max_runtime_duration: Maximum runtime duration (ISO 8601 format, e.g., "PT7H")
        max_queued_duration: Maximum queued duration (ISO 8601 format)
        termination_grace_period_duration: Termination grace period
        result_handling_strategy: Result handling strategy ("UPLOAD" or "NONE")
        results_location: Location for results (required if result_handling_strategy is "UPLOAD")
        api_key: NVCF API key
        org_name: NGC organization name
        base_url: NVCF API base URL
        **kwargs: Additional task parameters

    Returns:
        A Flyte task that will execute on NVCF
    """
    config = NVCFTaskConfig(
        name=name,
        container_image=container_image,
        gpu_specification=gpu_specification,
        container_args=container_args,
        container_environment=container_environment,
        models=models,
        secrets=secrets,
        max_runtime_duration=max_runtime_duration,
        max_queued_duration=max_queued_duration,
        termination_grace_period_duration=termination_grace_period_duration,
        result_handling_strategy=result_handling_strategy,
        results_location=results_location,
        api_key=api_key,
        org_name=org_name,
        base_url=base_url,
    )

    return NVCFTask(name=name, task_config=config, **kwargs)
