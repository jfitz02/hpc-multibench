#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A set of objects modelling the YAML schema.

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
from pathlib import Path
from typing import Any, Self

import yaml
from pydantic import BaseModel

from hpc_multibench.configuration import RunConfiguration
DEFAULT_OUTPUT_DIRECTORY = Path("results/")


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

    def get_runs(
        self, bench_name: str, run_configurations: dict[str, RunConfigurationModel]
    ) -> Iterator[RunConfiguration]:
        """."""
        for matrix_variables in self.matrix_iterator:
            for run_configuration_name in run_configurations:
                if run_configuration_name not in run_configurations.keys():
                    raise RuntimeError(
                        f"'{run_configuration_name}' not in list of"
                        " defined run configurations!"
                    )

                output_file = BenchModel.get_output_file(
                    bench_name, run_configuration_name, matrix_variables
                )

                run_configuration = run_configurations[
                    run_configuration_name
                ].realise(run_configuration_name, output_file)

                # Fix this to work for more things than args...
                for key, value in matrix_variables.items():
                    if key == "args":
                        run_configuration.args = value

                yield run_configuration

    @property
    def matrix_iterator(self) -> Iterator[dict[str, Any]]:
        """Get an iterator of values to update from the test matrix."""
        shaped: list[tuple[str, list[Any]]] = [
            (list(item.keys())[0], list(item.values())[0]) for item in self.matrix
        ]
        # https://docs.python.org/3/library/itertools.html#itertools.product
        item = shaped[0]
        for value in item[1]:
            yield {item[0]: value}

    @classmethod
    def get_output_file(
        cls, bench_name: str, run_configuration_name: str, variables: dict[str, Any]
    ) -> Path:
        """Construct the output file path for a run."""
        variables_str = ",".join(
            f"{name}={value.replace('/','').replace(' ','_')}"
            for name, value in variables.items()
        )
        file_name = (
            f"{bench_name}/{run_configuration_name}__"
            f"{variables_str}__%j.out"
        )
        return DEFAULT_OUTPUT_DIRECTORY / file_name


class TestPlan(BaseModel):
    """A Pydantic model for a set of test benches and their executables."""

    run_configurations: dict[str, RunConfigurationModel]
    benches: dict[str, BenchModel]

    @classmethod
    def from_yaml(cls, file: Path) -> Self:
        """Construct the model from a YAML file."""
        with file.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        return cls(**data)

    def run(self) -> None:
        """."""
        for bench_name, bench in self.benches.items():
            for run in bench.get_runs(bench_name, self.run_configurations):
                # run.run()
                print(run)

    def analyse(self) -> None:
        """."""
