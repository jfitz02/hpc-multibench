#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A set of objects modelling the YAML schema for a test plan."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel
from ruamel.yaml import YAML
from typing_extensions import Self


class RunConfigurationModel(BaseModel):
    """A Pydantic model for an executable."""

    sbatch_config: dict[str, Any]
    module_loads: list[str]
    environment_variables: dict[str, Any]
    directory: Path
    build_commands: list[str]
    run_command: str
    args: str | None = None

    # TODO: Could provide `realise()`?


class PlotModel(BaseModel):
    """A Pydantic model for plotting two values against each other."""

    # TODO: Needs work to expand capability


class AnalysisModel(BaseModel):
    """A Pydantic model for a test bench's analysis operations."""

    metrics: dict[str, str]
    plot: PlotModel


class BenchModel(BaseModel):
    """A Pydantic model for a test bench."""

    run_configurations: list[str]
    matrix: dict[str | tuple[str, ...], list[Any]]
    analysis: AnalysisModel
    enabled: bool = True


class TestPlanModel(BaseModel):
    """A Pydantic model for a set of test benches and their executables."""

    run_configurations: dict[str, RunConfigurationModel]
    benches: dict[str, BenchModel]

    @classmethod
    def from_yaml(cls, file: Path) -> Self:
        """Construct the model from a YAML file."""
        with file.open(encoding="utf-8") as handle:
            return cls(**YAML(typ="safe").load(handle))
