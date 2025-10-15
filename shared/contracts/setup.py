# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

"""
Ninaivalaigal API Contracts Package
Shared contracts for REST APIs and gRPC services
"""

from pathlib import Path

from setuptools import find_packages, setup

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else __doc__

setup(
    name="ninaivalaigal-contracts",
    version="1.0.0",
    description="Shared API contracts for ninaivalaigal microservices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Ninaivalaigal Team",
    author_email="api@ninaivalaigal.com",
    url="https://github.com/yourusername/ninaivalaigal",
    license="Proprietary",
    packages=find_packages(exclude=["tests", "tests.*"]),
    package_data={
        "": ["*.proto", "*.yaml", "*.json"],
    },
    include_package_data=True,
    python_requires=">=3.11",
    install_requires=[
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
        "grpcio>=1.60.0",
        "grpcio-tools>=1.60.0",
        "protobuf>=4.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
            "ruff>=0.1.0",
        ],
        "validation": [
            "openapi-spec-validator>=0.6.0",
            "buf>=1.28.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
    ],
    keywords="api contracts openapi grpc protobuf microservices",
    project_urls={
        "Documentation": "https://docs.ninaivalaigal.com/contracts",
        "Source": "https://github.com/yourusername/ninaivalaigal",
        "Tracker": "https://github.com/yourusername/ninaivalaigal/issues",
    },
)
