"""Tests for the NVCF agent implementation."""

from unittest.mock import MagicMock, patch

import pytest
from flyteidl.core.execution_pb2 import TaskExecution
from flytekit.extend.backend.base_agent import Resource
from flytekit.models.core.identifier import Identifier
from flytekit.models.task import TaskTemplate

from flytekitplugins.nvcf.agent import NVCFAgent, NVCFMetadata


@pytest.fixture
def mock_task_template():
    """Create a mock task template for testing."""
    return TaskTemplate(
        id=Identifier(
            resource_type="task", project="test", domain="test", name="test", version="1"
        ),
        type="nvcf_task",
        metadata=None,
        interface=None,
        custom={
            "api_key": "test-api-key",
            "org_name": "test-org",
            "base_url": "https://api.nvct.nvidia.com/v1/nvct",
            "nvcf_config": {
                "name": "test-task",
                "containerImage": "nvcr.io/test/image:latest",
                "gpuSpecification": {
                    "gpu": "L40S",
                    "instanceType": "gl40s_1.br25_2xlarge",
                    "backend": "GFN",
                },
                "containerArgs": "python -c 'print(\"Hello, World!\")'",
                "maxRuntimeDuration": "PT1H",
                "maxQueuedDuration": "PT1H",
                "terminationGracePeriodDuration": "PT15M",
                "resultHandlingStrategy": "UPLOAD",
                "resultsLocation": "test-org/test-results",
            },
        },
    )


@pytest.fixture
def mock_client():
    """Create a mock NGC client."""
    client = MagicMock()

    # Mock task creation response
    task_create_response = MagicMock()
    task_create_response.task.id = "test-task-id"
    task_create_response.task.status = "QUEUED"
    task_create_response.task.createdAt = "2023-01-01T00:00:00Z"
    client.cloud_function.tasks.create.return_value = task_create_response

    # Mock task info response
    task_info_response = MagicMock()
    task_info_response.task.status = "RUNNING"
    task_info_response.task.lastUpdatedAt = "2023-01-01T00:01:00Z"
    client.cloud_function.tasks.info.return_value = task_info_response

    # Mock task results
    client.cloud_function.tasks.results.return_value = [
        {"name": "output.txt", "url": "https://example.com/output.txt"}
    ]

    return client


@pytest.mark.asyncio
async def test_create(mock_task_template, mock_client):
    """Test creating a task."""
    agent = NVCFAgent()

    # Mock the client creation
    with patch.object(agent, "_get_client", return_value=mock_client):
        resource_meta = await agent.create(task_template=mock_task_template)

        # Verify the client was called correctly
        mock_client.cloud_function.tasks.create.assert_called_once()

        # Verify the returned metadata
        assert isinstance(resource_meta, NVCFMetadata)
        assert resource_meta.task_id == "test-task-id"
        assert resource_meta.status == "QUEUED"


@pytest.mark.asyncio
async def test_get(mock_task_template, mock_client):
    """Test getting task status."""
    agent = NVCFAgent()

    # Create a resource metadata object
    resource_meta = NVCFMetadata(
        api_key="test-api-key", org_name="test-org", task_id="test-task-id", status="QUEUED"
    )

    # Mock the client creation
    with patch.object(agent, "_get_client", return_value=mock_client):
        resource = await agent.get(resource_meta=resource_meta)

        # Verify the client was called correctly
        mock_client.cloud_function.tasks.info.assert_called_once_with("test-task-id")

        # Verify the returned resource
        assert isinstance(resource, Resource)
        assert resource.phase == TaskExecution.RUNNING
        assert resource_meta.status == "RUNNING"  # Check that metadata was updated
        assert len(resource.log_links) == 1  # Verify log links are present
        assert resource.message  # Verify message is present


@pytest.mark.asyncio
async def test_delete(mock_task_template, mock_client):
    """Test deleting a task."""
    agent = NVCFAgent()

    # Create a resource metadata object
    resource_meta = NVCFMetadata(
        api_key="test-api-key", org_name="test-org", task_id="test-task-id", status="RUNNING"
    )

    # Mock the client creation and safe_delete method
    with patch.object(agent, "_get_client", return_value=mock_client), patch.object(
        agent, "_safe_delete", return_value=None
    ):
        await agent.delete(resource_meta=resource_meta)

        # Verify the client was called correctly
        mock_client.cloud_function.tasks.cancel.assert_called_once_with("test-task-id")
        agent._safe_delete.assert_called_once_with(mock_client, "test-task-id")


def test_map_status_to_phase():
    """Test mapping NVCF task status to Flyte phase."""
    agent = NVCFAgent()

    # Test various status mappings
    assert agent._map_status_to_phase("queued") == TaskExecution.INITIALIZING
    assert agent._map_status_to_phase("launched") == TaskExecution.RUNNING
    assert agent._map_status_to_phase("running") == TaskExecution.RUNNING
    assert agent._map_status_to_phase("completed") == TaskExecution.SUCCEEDED
    assert agent._map_status_to_phase("errored") == TaskExecution.FAILED
    assert agent._map_status_to_phase("exceeded_max_runtime_duration") == TaskExecution.FAILED
    assert agent._map_status_to_phase("canceled") == TaskExecution.FAILED  # canceled maps to FAILED
    assert (
        agent._map_status_to_phase("unknown") == TaskExecution.INITIALIZING
    )  # unknown maps to INITIALIZING
