"""Tests for the NVCF agent implementation."""

from unittest.mock import MagicMock, patch

import pytest
from flytekit import FlyteContext
from flytekit.models.core.identifier import Identifier
from flytekit.models.task import TaskTemplate

from flytekitplugins.nvcf.agent import NVCFAgent
from flytekitplugins.nvcf.models import NVCFMetadata


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
        ctx = FlyteContext.current_context()
        resource_meta = await agent.create(ctx, mock_task_template)

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
        ctx = FlyteContext.current_context()
        updated_meta = await agent.get(ctx, resource_meta, mock_task_template)

        # Verify the client was called correctly
        mock_client.cloud_function.tasks.info.assert_called_once_with("test-task-id")

        # Verify the returned metadata
        assert updated_meta.status == "RUNNING"


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
        ctx = FlyteContext.current_context()
        await agent.delete(ctx, resource_meta, mock_task_template)

        # Verify the client was called correctly
        mock_client.cloud_function.tasks.cancel.assert_called_once_with("test-task-id")
        agent._safe_delete.assert_called_once_with(mock_client, "test-task-id")


def test_map_status_to_phase():
    """Test mapping NVCF status to Flyte phase."""
    agent = NVCFAgent()

    # Test various status mappings
    assert agent._map_status_to_phase("QUEUED") == ("QUEUED", 0)
    assert agent._map_status_to_phase("LAUNCHED") == ("RUNNING", 1)
    assert agent._map_status_to_phase("RUNNING") == ("RUNNING", 2)
    assert agent._map_status_to_phase("COMPLETED") == ("SUCCEEDED", 0)
    assert agent._map_status_to_phase("ERRORED") == ("FAILED", 0)
    assert agent._map_status_to_phase("CANCELED") == ("ABORTED", 0)
    assert agent._map_status_to_phase("UNKNOWN_STATUS") == ("UNKNOWN", 0)
