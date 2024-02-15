#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ingest YAML data.

Sample code for adding defaults:
```python
class Defaults(BaseModel):
    sbatch_config: Optional[list[str]] = None
    module_loads: Optional[list[str]] = None
    environment_variables: Optional[list[str]] = None
    directory: Optional[Path] = None
    build_commands: Optional[list[str]] = None
    run_commands: Optional[list[str]] = None
    args: Optional[str] = None
```
"""

from pathlib import Path
from typing import Any


import yaml
from pydantic import BaseModel


class Executable(BaseModel):
    """A Pydantic model for an executable."""

    sbatch_config: dict[str, Any]
    module_loads: list[str]
    environment_variables: dict[str, Any]
    directory: Path
    build_commands: list[str]
    run_command: str
    args: str | None = None


class Analysis(BaseModel):
    """A Pydantic model for a test bench's analysis."""

    metrics: dict[str, str]
    plots: dict[str, str]


class Bench(BaseModel):
    """A Pydantic model for a test bench."""

    executables: list[str]
    # This is a list of dictionaries to preserve matrix ordering!!!
    matrix: list[dict[str, list[Any]]]
    analysis: Analysis


class TestPlan(BaseModel):
    """A Pydantic model for a set of test benches and their executables."""

    executables: dict[str, Executable]
    benches: dict[str, Bench]


def get_test_plan(config_file: Path) -> TestPlan:
    """Ingest the YAML file as a test plan using Pydantic."""
    with config_file.open(encoding="utf-8") as config_handle:
        config_data = yaml.safe_load(config_handle)
    return TestPlan(**config_data)
