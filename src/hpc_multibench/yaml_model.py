#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A set of objects modelling the YAML schema.

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

from collections.abc import Iterator
from itertools import product
from pathlib import Path
from re import search as re_search
from typing import Any

import matplotlib.pyplot as plt
from pydantic import BaseModel
from ruamel.yaml import YAML
from typing_extensions import Self

from hpc_multibench.configuration import RunConfiguration

BASE_OUTPUT_DIRECTORY = Path("results/")
NAME_REGEX = r"===== RUN (.*) ====="


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
        self, bench_name: str, run_configuration_name: str, variables: dict[str, Any]
    ) -> RunConfiguration:
        """Construct a run configuration from its data model."""
        # Get the output file path
        output_file_name = RunConfiguration.get_output_file_name(
            run_configuration_name, variables
        )
        output_file = BASE_OUTPUT_DIRECTORY / bench_name / output_file_name

        # TODO: Modify contents based on variables keys here

        run = RunConfiguration(run_configuration_name, self.run_command, output_file)
        run.sbatch_config = self.sbatch_config
        run.module_loads = self.module_loads
        run.environment_variables = self.environment_variables
        run.directory = Path(self.directory)
        run.build_commands = self.build_commands
        run.args = self.args

        # Fix this to work for more things than args...
        for key, value in variables.items():
            # TODO: Error checking on keys
            setattr(run, key, value)
            # if key == "args":
            #     run.args = value

        return run


class PlotModel(BaseModel):
    """A Pydantic model for plotting two variables."""

    x: str
    y: str


class AnalysisModel(BaseModel):
    """A Pydantic model for a test bench's analysis."""

    metrics: dict[str, str]
    plot: PlotModel

    def parse_output_file(self, output_file: Path) -> dict[str, str] | None:
        """."""
        run_output = output_file.read_text(encoding="utf-8")
        results: dict[str, str] = {}
        name_search = re_search(NAME_REGEX, run_output)
        if name_search is None:
            return None
        results["name"] = name_search.group(1)
        for name, regex in self.metrics.items():
            metric_search = re_search(regex, run_output)
            if metric_search is None:
                return None
            # TODO: Support multiple groups by lists as keys?
            results[name] = metric_search.group(1)
        return results


class BenchModel(BaseModel):
    """A Pydantic model for a test bench."""

    run_configurations: list[str]
    # This is a list of dictionaries to preserve matrix ordering!!!
    matrix: dict[str | tuple[str, ...], list[Any]]
    analysis: AnalysisModel

    def get_runs(
        self, bench_name: str, run_configurations: dict[str, RunConfigurationModel]
    ) -> Iterator[RunConfiguration]:
        """."""
        for variables in self.matrix_iterator:
            for run_configuration_name in self.run_configurations:
                if run_configuration_name not in run_configurations.keys():
                    raise RuntimeError(
                        f"'{run_configuration_name}' not in list of"
                        " defined run configurations!"
                    )

                yield run_configurations[run_configuration_name].realise(
                    bench_name, run_configuration_name, variables
                )

    def get_analysis(self, bench_name: str) -> Iterator[dict[str, str]]:
        """."""
        output_directory = BASE_OUTPUT_DIRECTORY / bench_name
        for output_file in output_directory.iterdir():
            results = self.analysis.parse_output_file(output_file)
            if results is not None:
                yield results

    def comparative_plot_results(
        self, bench_name: str
    ) -> dict[str, list[tuple[float, float]]]:
        """."""
        results: dict[str, list[tuple[float, float]]] = {}
        for result in self.get_analysis(bench_name):
            if result["name"] not in results:
                results[result["name"]] = []
            point = (
                float(result[self.analysis.plot.x]),
                float(result[self.analysis.plot.y]),
            )
            results[result["name"]].append(point)
        return {name: sorted(value) for name, value in results.items()}

    def plot(self, bench_name: str) -> None:
        """."""
        results = self.comparative_plot_results(bench_name)
        for name, result in results.items():
            print(name, result)
            plt.plot(*zip(*result, strict=True), marker="x", label=name)
        plt.xlabel(self.analysis.plot.x)
        plt.ylabel(self.analysis.plot.y)
        plt.title("Benchmark analysis")
        plt.legend()
        plt.show()

    @property
    def matrix_iterator(self) -> Iterator[dict[str, Any]]:
        """Get an iterator of values to update from the test matrix."""
        # TODO: How does a property play with iterators?
        shaped: list[list[list[tuple[str, Any]]]] = [
            (
                [[(key, value)] for value in values]
                if isinstance(key, str)
                else [
                    [(k, v) for k, v in zip(key, setting, strict=True)]
                    for setting in values
                ]
            )
            for key, values in self.matrix.items()
        ]
        for combination in product(*shaped):
            # # Consider the case
            # #   [sbatch_config, sbatch_config]:
            # #     - [{"nodes": 2}, {"mem-per-cpu": 1000}]
            # #
            # variables = {}
            # for items in combination:
            #     for item in items:
            #         if item[0] in variables and isinstance(item[1], dict):
            #             variables[item[0]].update(item[1])
            #         else:
            #             variables[item[0]] = item[1]
            # yield variables
            yield {item[0]: item[1] for items in combination for item in items}


class TestPlan(BaseModel):
    """A Pydantic model for a set of test benches and their executables."""

    run_configurations: dict[str, RunConfigurationModel]
    benches: dict[str, BenchModel]

    @classmethod
    def from_yaml(cls, file: Path) -> Self:
        """Construct the model from a YAML file."""
        with file.open(encoding="utf-8") as handle:
            return cls(**YAML(typ="safe").load(handle))

    def run(self) -> None:
        """."""
        for bench_name, bench in self.benches.items():
            for run in bench.get_runs(bench_name, self.run_configurations):
                print(run)
                # Run the configurations with `run.run()`

    def analyse(self) -> None:
        """."""
        for bench_name, bench in self.benches.items():
            bench.plot(bench_name)
