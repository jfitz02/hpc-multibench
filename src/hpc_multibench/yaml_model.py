#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A set of objects modelling the YAML schema for a test plan."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel
from ruamel.yaml import YAML
from typing_extensions import Self

from hpc_multibench.run_configuration import RunConfiguration


class RunConfigurationModel(BaseModel):
    """A Pydantic model for an executable."""

    sbatch_config: dict[str, Any]
    module_loads: list[str]
    environment_variables: dict[str, Any]
    directory: Path
    build_commands: list[str]
    run_command: str
    args: str | None = None

    def realise(
        self,
        name: str,
        output_directory: Path,
        instantiation: dict[str, Any] | None,
    ) -> RunConfiguration:
        """Construct a run configuration from its data model."""
        run = RunConfiguration(name, self.run_command, output_directory)
        run.sbatch_config = self.sbatch_config
        run.module_loads = self.module_loads
        run.environment_variables = self.environment_variables
        run.directory = Path(self.directory)
        run.build_commands = self.build_commands
        run.args = self.args
        run.instantiation = instantiation

        # Update the run configuration based on the instantiation
        if instantiation is not None:
            for key, value in instantiation.items():
                # TODO: Error checking on keys
                if key == "sbatch_config":
                    run.sbatch_config.update(value)
                # TODO: Further root cause why this was causing duplicate runs
                # elif key == "environment_variables":
                #     run.environment_variables.update(value)
                else:
                    setattr(run, key, value)

        return run


class LinePlotModel(BaseModel):
    """A Pydantic model for a line plot of two variables."""

    title: str
    x: str
    y: str
    split_metrics: list[str] = []
    fix_metrics: dict[str, Any] = {}


class BarChartModel(BaseModel):
    """A Pydantic model for a bar chart of a single variable."""

    title: str
    y: str
    split_metrics: list[str] = []
    fix_metrics: dict[str, Any] = {}


class RooflinePlotModel(BaseModel):
    """A Pydantic model for a roofline plot from two metrics."""

    title: str
    gflops_per_sec: str
    mbytes_per_sec: str
    ert_json: Path


class ExportModel(BaseModel):
    """A Pydantic model for a exporting a set of metrics."""

    export_path: Path | None
    export_format: str = "csv"
    # metrics: list[str] | None = None


class AnalysisModel(BaseModel):
    """A Pydantic model for a test bench's analysis operations."""

    # TODO: Could separate properties (strings) and metrics (floats)
    metrics: dict[str, str]
    # TODO: Offer singular interface `line_plot` which is just one plot
    line_plots: list[LinePlotModel] = []
    bar_charts: list[BarChartModel] = []
    roofline_plots: list[RooflinePlotModel] = []
    data_exports: list[ExportModel] = []


class RerunModel(BaseModel):
    """A Pydantic model for the test bench's statistical re-runs."""

    number: int
    highest_discard: int = 0
    lowest_discard: int = 0
    unaggregatable_metrics: list[str] = []

    @property
    def undiscarded_number(self) -> int:
        """Return the number of undiscarded reruns."""
        return self.number - self.highest_discard - self.lowest_discard


class BenchModel(BaseModel):
    """A Pydantic model for a test bench."""

    run_configurations: list[str]
    matrix: dict[str | tuple[str, ...], list[Any]]
    analysis: AnalysisModel
    reruns: RerunModel = RerunModel(number=1)
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
