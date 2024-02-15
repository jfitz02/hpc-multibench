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
from typing import Any, Self

import yaml
from pydantic import BaseModel

from hpc_multibench.configuration import RunConfiguration

class RunConfigurationModel(BaseModel):
    """A Pydantic model for an executable."""

    sbatch_config: dict[str, Any]
    module_loads: list[str]
    environment_variables: dict[str, Any]
    directory: Path
    build_commands: list[str]
    run_command: str
    args: str | None = None
    
    def realise(self, name: str, output_file: Path) -> RunConfiguration:
        """Construct a run configuration from its data model."""
        run = RunConfiguration(self.run_command, output_file)
        run.name = name
        run.sbatch_config = self.sbatch_config
        run.module_loads = self.module_loads
        run.environment_variables = self.environment_variables
        run.directory = Path(self.directory)
        run.build_commands = self.build_commands
        run.args = self.args
        return run


class AnalysisModel(BaseModel):
    """A Pydantic model for a test bench's analysis."""

    metrics: dict[str, str]
    plots: dict[str, str]


class BenchModel(BaseModel):
    """A Pydantic model for a test bench."""

    run_configurations: list[str]
    # This is a list of dictionaries to preserve matrix ordering!!!
    matrix: list[dict[str, list[Any]]]
    analysis: AnalysisModel


class TestPlanModel(BaseModel):
    """A Pydantic model for a set of test benches and their executables."""

    run_configurations: dict[str, RunConfigurationModel]
    benches: dict[str, BenchModel]

    @classmethod
    def from_yaml(cls, file: Path) -> Self:
        """Construct the model from a YAML file."""
        with file.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        return cls(**data)
