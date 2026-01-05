"""
Setup script for SmartCom - Custom Serial Port Communication Tool
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="smartcom",
    version="0.1.0-alpha",
    author="SmartCom Team",
    author_email="team@smartcom.dev",
    description="Custom serial port communication tool with protocol parsing",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/peterChengg/smartcom",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: System :: Hardware :: Serial Drivers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.3.0",
            "pytest-qt>=4.2.0",
            "pytest-cov>=4.1.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.3.0",
            "flake8>=6.0.0",
            "mypy>=1.3.0",
            "coverage>=7.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "smartcom=src.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)