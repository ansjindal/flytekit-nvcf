"""Setup script for the NVCF plugin for Flytekit."""

from setuptools import setup

PLUGIN_NAME = "nvcf"

microlib_name = f"flytekitplugins-{PLUGIN_NAME}"

plugin_requires = [
    "flytekit>1.10.7",
    "ngcsdk>=0.1.0",
    "isodate>=0.6.1",
    "flyteidl>1.10.7",
    "simplejson>=3.17.0",
    "grpcio>=1.70.0",
    "grpcio-tools>=1.70.0",
]

dev_requires = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.18.0",
    "mock>=4.0.0",
    "pytest-cov>=4.0.0",
]

__version__ = "0.0.0+develop"

setup(
    name=microlib_name,
    version=__version__,
    author="flyteorg",
    author_email="ansjindal@nvidia.com",
    description="This package holds the NVIDIA Cloud Functions plugins for flytekit",
    namespace_packages=["flytekitplugins"],
    packages=[f"flytekitplugins.{PLUGIN_NAME}"],
    install_requires=plugin_requires,
    extras_require={
        "dev": dev_requires,
    },
    license="apache2",
    python_requires=">=3.10",
    classifiers=[
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    entry_points={"flytekit.plugins": [f"{PLUGIN_NAME}=flytekitplugins.{PLUGIN_NAME}"]},
)
