#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""".

```python
from hpc_multibench.configuration import RunConfiguration
from hpc_multibench.yaml_ingest import TestPlan, Bench


class TestHarness:
    def __init__(self, test_plan: TestPlan) -> None:
        self.run_configurations: dict[str, RunConfiguration] = {}
        self.benches: dict[str, Bench]
```
"""

from collections.abc import Iterator
from pathlib import Path
from typing import Any

from hpc_multibench.yaml_ingest import Executable, Bench, get_test_plan
from hpc_multibench.configuration import DEFAULT_OUTPUT_DIRECTORY, RunConfiguration


def get_run_configuration(
    name: str, output_file: Path, executable: Executable
) -> RunConfiguration:
    """Construct a run configuration from an executable model."""
    run = RunConfiguration(executable.run_command, output_file)
    run.name = name
    run.sbatch_config = executable.sbatch_config
    run.module_loads = executable.module_loads
    run.environment_variables = executable.environment_variables
    run.directory = Path(executable.directory)
    run.build_commands = executable.build_commands
    run.args = executable.args
    return run


def get_matrix_iterator(matrix: list[dict[str, list[Any]]]) -> Iterator[dict[str, Any]]:
    """
    Get an iterator of values to update from the test matrix.

    TODO: Make this work for more than the first element...
    """
    shaped: list[tuple[str, list[Any]]] = [
        (list(item.keys())[0], list(item.values())[0]) for item in matrix
    ]
    # https://docs.python.org/3/library/itertools.html#itertools.product
    item = shaped[0]
    for value in item[1]:
        yield {item[0]: value}


def get_matrix_variables_suffix(variables: dict[str, Any]) -> str:
    """."""
    return ",".join(
        f"{name}={value.replace('/','').replace(' ','_')}"
        for name, value in variables.items()
    )


def get_bench(
    bench_name: str, bench: Bench, executables: dict[str, Executable]
) -> list[RunConfiguration]:
    """."""
    bench_run_configurations: list[RunConfiguration] = []
    # Iterate through matrix

    for matrix_variables in get_matrix_iterator(bench.matrix):
        print(matrix_variables)
        for executable_name in bench.executables:
            if executable_name not in executables:
                raise RuntimeError(
                    f"Executable '{executable_name}' not in list of defined executables!"
                )
            executable = executables[executable_name]
            output_file = (
                DEFAULT_OUTPUT_DIRECTORY
                / f"{bench_name}/{executable_name}__{get_matrix_variables_suffix(matrix_variables)}__%j.out"
            )
            run_configuration = get_run_configuration(
                executable_name,
                output_file,
                executable,
            )

            for key, value in matrix_variables.items():
                if key == "args":
                    run_configuration.args = value

            bench_run_configurations.append(run_configuration)
    return bench_run_configurations


def get_benches(config_file: Path) -> dict[str, list[RunConfiguration]]:
    """."""
    test_plan = get_test_plan(config_file)

    return {
        bench_name: get_bench(bench_name, bench, test_plan.executables)
        for (bench_name, bench) in test_plan.benches.items()
    }

    # for (bench_name, bench) in test_plan.benches.items():
    #     for instance in variable:
    #         for executable in test_plan.executables:
