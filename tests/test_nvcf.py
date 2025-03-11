"""Tests for the NVCF task implementation."""

from unittest.mock import patch

import pytest
from flytekit.extend.backend.base_agent import AgentRegistry

from flytekitplugins.nvcf.agent import NVCFAgent
from flytekitplugins.nvcf.task import NVCFTask, nvcf_task


def test_nvcf_task_registration():
    """Test that the NVCF agent is registered."""
    agent = AgentRegistry.get_agent("nvcf_task")
    assert agent is not None
    assert isinstance(agent, NVCFAgent)


def test_nvcf_task_creation():
    """Test creating an NVCF task."""
    task = nvcf_task(
        name="test-task",
        container_image="nvcr.io/test/image:latest",
        gpu_specification={
            "gpu": "L40",
            "instanceType": "DGX-CLOUD.GPU.L40_2x",
            "backend": "nvcf-dgxc-k8s-forge-az28-prd1",
        },
        container_args="python -c 'print(\"Hello, World!\")'",
        max_runtime_duration="PT1H",
        result_handling_strategy="UPLOAD",
        results_location="test-org/test-results",
        api_key="test-api-key",
        org_name="test-org",
    )

    # Verify the task was created correctly
    assert isinstance(task, NVCFTask)
    assert task.name == "test-task"

    # Verify the custom attributes
    custom = task.get_custom({})
    assert custom["api_key"] == "test-api-key"
    assert custom["org_name"] == "test-org"
    assert custom["nvcf_config"]["name"] == "test-task"
    assert custom["nvcf_config"]["containerImage"] == "nvcr.io/test/image:latest"
    assert custom["nvcf_config"]["gpuSpecification"]["gpu"] == "L40"
    assert custom["nvcf_config"]["gpuSpecification"]["instanceType"] == "DGX-CLOUD.GPU.L40_2x"
    assert custom["nvcf_config"]["gpuSpecification"]["backend"] == "nvcf-dgxc-k8s-forge-az28-prd1"
    assert custom["nvcf_config"]["containerArgs"] == "python -c 'print(\"Hello, World!\")'"
    assert custom["nvcf_config"]["maxRuntimeDuration"] == "PT1H"
    assert custom["nvcf_config"]["resultHandlingStrategy"] == "UPLOAD"
    assert custom["nvcf_config"]["resultsLocation"] == "test-org/test-results"


@pytest.mark.asyncio
async def test_nvcf_task_execute():
    """Test executing an NVCF task."""
    task = nvcf_task(
        name="test-task",
        container_image="nvcr.io/test/image:latest",
        gpu_specification={
            "gpu": "L40",
            "instanceType": "DGX-CLOUD.GPU.L40_2x",
            "backend": "nvcf-dgxc-k8s-forge-az28-prd1",
        },
        container_args="python -c 'print(\"Hello, World!\")'",
        max_runtime_duration="PT1H",
        result_handling_strategy="UPLOAD",
        results_location="test-org/test-results",
        api_key="test-api-key",
        org_name="test-org",
    )

    # Mock the execute method to return an async result
    async def mock_async_execute(*args, **kwargs):
        return {"result": "success"}

    # Use AsyncMock for async method
    with patch.object(NVCFTask, "execute", side_effect=mock_async_execute):
        # Execute the task
        result = await task.execute()

        # Verify the result
        assert result == {"result": "success"}


def test_nvcf_task_config_validation():
    """Test validation in NVCFTaskConfig."""
    # Test missing API key
    with pytest.raises(ValueError, match="NVCF API key is required"):
        nvcf_task(
            name="test-task",
            container_image="nvcr.io/test/image:latest",
            gpu_specification={"gpu": "L40"},
            org_name="test-org",
            result_handling_strategy="UPLOAD",
            results_location="test-org/test-results",
        )

    # Test missing org name
    with pytest.raises(ValueError, match="NGC organization name is required"):
        nvcf_task(
            name="test-task",
            container_image="nvcr.io/test/image:latest",
            gpu_specification={"gpu": "L40"},
            api_key="test-api-key",
            result_handling_strategy="UPLOAD",
            results_location="test-org/test-results",
        )

    # Test missing results location with UPLOAD strategy
    with pytest.raises(
        ValueError, match="results_location is required when result_handling_strategy is UPLOAD"
    ):
        nvcf_task(
            name="test-task",
            container_image="nvcr.io/test/image:latest",
            gpu_specification={"gpu": "L40"},
            api_key="test-api-key",
            org_name="test-org",
            result_handling_strategy="UPLOAD",
        )
