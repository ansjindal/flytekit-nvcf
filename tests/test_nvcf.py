"""Tests for the NVCF task implementation."""

from unittest.mock import patch

import pytest
from flytekit.extend.backend.base_agent import AgentRegistry

from flytekitplugins.nvcf.agent import NVCFAgent
from flytekitplugins.nvcf.models import NVCFTaskConfig
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
        gpu_specification={"gpu": "L40S", "instanceType": "gl40s_1.br25_2xlarge", "backend": "GFN"},
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
    assert custom["nvcf_config"]["gpuSpecification"]["gpu"] == "L40S"
    assert custom["nvcf_config"]["containerArgs"] == "python -c 'print(\"Hello, World!\")'"
    assert custom["nvcf_config"]["maxRuntimeDuration"] == "PT1H"
    assert custom["nvcf_config"]["resultHandlingStrategy"] == "UPLOAD"
    assert custom["nvcf_config"]["resultsLocation"] == "test-org/test-results"


def test_nvcf_task_config_validation():
    """Test validation in NVCFTaskConfig."""
    # Test missing API key
    with pytest.raises(ValueError, match="NVCF API key is required"):
        NVCFTaskConfig(
            name="test-task",
            container_image="nvcr.io/test/image:latest",
            gpu_specification={"gpu": "L40S"},
            org_name="test-org",
            result_handling_strategy="UPLOAD",
            results_location="test-org/test-results",
        )

    # Test missing org name
    with pytest.raises(ValueError, match="NGC organization name is required"):
        NVCFTaskConfig(
            name="test-task",
            container_image="nvcr.io/test/image:latest",
            gpu_specification={"gpu": "L40S"},
            api_key="test-api-key",
            result_handling_strategy="UPLOAD",
            results_location="test-org/test-results",
        )

    # Test missing results location with UPLOAD strategy
    with pytest.raises(
        ValueError, match="results_location is required when result_handling_strategy is UPLOAD"
    ):
        NVCFTaskConfig(
            name="test-task",
            container_image="nvcr.io/test/image:latest",
            gpu_specification={"gpu": "L40S"},
            api_key="test-api-key",
            org_name="test-org",
            result_handling_strategy="UPLOAD",
        )


@patch("flytekitplugins.nvcf.task.AgentRegistry.get_agent")
def test_nvcf_task_execute(mock_get_agent):
    """Test executing an NVCF task."""
    # Create a mock agent
    mock_agent = NVCFAgent()
    mock_agent.execute = lambda task, **kwargs: {"result": "success"}
    mock_get_agent.return_value = mock_agent

    # Create a task
    task = nvcf_task(
        name="test-task",
        container_image="nvcr.io/test/image:latest",
        gpu_specification={"gpu": "L40S", "instanceType": "gl40s_1.br25_2xlarge", "backend": "GFN"},
        container_args="python -c 'print(\"Hello, World!\")'",
        max_runtime_duration="PT1H",
        result_handling_strategy="UPLOAD",
        results_location="test-org/test-results",
        api_key="test-api-key",
        org_name="test-org",
    )

    # Execute the task
    result = task.execute()

    # Verify the agent was called
    mock_get_agent.assert_called_once_with("nvcf_task")
    assert result == {"result": "success"}
