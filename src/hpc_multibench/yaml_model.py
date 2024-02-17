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

from pydantic import BaseModel
from ruamel.yaml import YAML
from typing_extensions import Self

from hpc_multibench.configuration import RunConfiguration

BASE_OUTPUT_DIRECTORY = Path("results/")


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
            if key == "args":
                run.args = value

        return run


class AnalysisModel(BaseModel):
    """A Pydantic model for a test bench's analysis."""

    metrics: dict[str, str]
    plots: dict[str, str]

    def parse_output_file(self, output_file: Path) -> dict[str, str] | None:
        """."""
        run_output = output_file.read_text(encoding="utf-8")

        results: dict[str, str] = {}
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
    matrix: list[dict[str, list[Any]]]
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

    @property
    def matrix_iterator(self) -> Iterator[dict[str, Any]]:
        """Get an iterator of values to update from the test matrix."""
        # Turn into lists of tuples
        # If the args is changed to if ordered keys just work, this will need
        # modification
        shaped: list[list[tuple[str, Any]]] = [
            [(list(item.keys())[0], value) for value in list(item.values())[0]]
            for item in self.matrix
        ]
        # https://docs.python.org/3/library/itertools.html#itertools.product
        for combination in product(*shaped):
            yield {item[0]: item[1] for item in combination}


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

    def analyse(self) -> None:
        """."""
        for bench_name, bench in self.benches.items():
            for result in bench.get_analysis(bench_name):
                print(result)
