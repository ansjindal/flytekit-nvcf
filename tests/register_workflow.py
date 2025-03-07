"""Script to register the NVCF workflow with Flyte."""

from flytekit.remote import FlyteRemote
from flytekit.configuration import Config
from flytekit.models.core.identifier import Identifier

from test_nvcf_pyflyte import test_nvcf_workflow

# Configure Flyte remote
remote = FlyteRemote(
    Config.for_sandbox(),
    "flytekit-nvcf",  # project name
    "development",    # domain
)

# Register the workflow
remote.register(
    test_nvcf_workflow,
    project="flytekit-nvcf",
    domain="development",
    name="test-nvcf-workflow",
    version="1.0.0",
)
