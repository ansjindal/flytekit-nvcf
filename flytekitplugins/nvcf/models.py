"""Data models for the NVCF plugin."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from flytekit.extend.backend.base_agent import ResourceMeta


class NVCFTaskConfig:
    """Configuration for NVCF tasks."""

    def __init__(
        self,
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
    ):
        """Initialize NVCF task configuration.

        Args:
            name: Name of the NVCF task
            container_image: Container image to run
            gpu_specification: GPU specification (gpu, instanceType, backend)
            container_args: Optional container command
            container_environment: Optional environment variables
            models: Optional models to use
            secrets: Secrets to pass to the task
            max_runtime_duration: Maximum runtime duration (ISO 8601 format)
            max_queued_duration: Maximum queued duration (ISO 8601 format)
            termination_grace_period_duration: Termination grace period
            result_handling_strategy: Result handling strategy ("UPLOAD" or "NONE")
            results_location: Location for results
            api_key: NVCF API key
            org_name: NGC organization name
            base_url: NVCF API base URL
        """
        if result_handling_strategy == "UPLOAD" and not results_location:
            raise ValueError("results_location is required when result_handling_strategy is UPLOAD")

        if not api_key:
            raise ValueError("NVCF API key is required")

        if not org_name:
            raise ValueError("NGC organization name is required")

        self.name = name
        self.container_image = container_image
        self.gpu_specification = gpu_specification
        self.container_args = container_args
        self.container_environment = container_environment
        self.models = models
        self.secrets = secrets
        self.max_runtime_duration = max_runtime_duration
        self.max_queued_duration = max_queued_duration
        self.termination_grace_period_duration = termination_grace_period_duration
        self.result_handling_strategy = result_handling_strategy
        self.results_location = results_location
        self.api_key = api_key
        self.org_name = org_name
        self.base_url = base_url

    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary for the NVCF API."""
        nvcf_config = {
            "name": self.name,
            "containerImage": self.container_image,
            "gpuSpecification": self.gpu_specification,
            "maxQueuedDuration": self.max_queued_duration,
            "terminationGracePeriodDuration": self.termination_grace_period_duration,
            "resultHandlingStrategy": self.result_handling_strategy,
        }

        if self.container_args:
            nvcf_config["containerArgs"] = self.container_args

        if self.container_environment:
            nvcf_config["containerEnvironment"] = self.container_environment

        if self.models:
            nvcf_config["models"] = self.models

        if self.secrets:
            nvcf_config["secrets"] = self.secrets

        if self.max_runtime_duration:
            nvcf_config["maxRuntimeDuration"] = self.max_runtime_duration

        if self.results_location:
            nvcf_config["resultsLocation"] = self.results_location

        return nvcf_config


@dataclass
class NVCFMetadata(ResourceMeta):
    """
    Metadata for NVCF tasks.

    This class stores all the information needed to interact with an NVCF task,
    including authentication details and task status information.
    """

    # Authentication and connection details
    api_key: str
    org_name: str
    base_url: str = "https://api.nvct.nvidia.com/v1/nvct"

    # Task identification
    task_id: Optional[str] = None
    name: Optional[str] = None

    # Task status information
    status: Optional[str] = None
    percent_complete: Optional[int] = None
    created_at: Optional[str] = None
    last_updated_at: Optional[str] = None

    def update_status(
        self,
        status: str,
        percent_complete: Optional[int] = None,
        last_updated_at: Optional[str] = None,
    ):
        """Update the task status information."""
        self.status = status
        if percent_complete is not None:
            self.percent_complete = percent_complete
        if last_updated_at is not None:
            self.last_updated_at = last_updated_at
        return self

    def __repr__(self) -> str:
        """Return string representation of NVCFMetadata.

        Returns:
            str: A string representation of the metadata
        """
        return (
            f"NVCFMetadata(task_id='{self.task_id}', "
            f"name='{self.name}', status='{self.status}', "
            f"percent_complete={self.percent_complete})"
        )
