# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

"""
Ninaivalaigal Storage Library
Shared storage abstraction for file uploads (EPIC#022)
"""

from pathlib import Path

from setuptools import find_packages, setup

readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text() if readme_path.exists() else __doc__

setup(
    name="ninaivalaigal-storage",
    version="0.1.0",
    description="Shared storage abstractions for ninaivalaigal services",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Ninaivalaigal Team",
    author_email="platform@ninaivalaigal.com",
    license="Proprietary",
    packages=find_packages(exclude=("tests", "tests.*")),
    python_requires=">=3.11",
    install_requires=[
        "boto3>=1.34.0,<2.0.0",
    ],
    extras_require={
        "dev": [
            "moto[s3]>=5.0.0",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "License :: Other/Proprietary License",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
