#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""".

```python
from hpc_multibench.configuration import RunConfiguration
from hpc_multibench.yaml_ingest import TestPlan, BenchModel


class TestHarness:
    def __init__(self, test_plan: TestPlan) -> None:
        self.run_configurations: dict[str, RunConfiguration] = {}
        self.benches: dict[str, BenchModel]
```
"""

from collections.abc import Iterator
from pathlib import Path
from typing import Any

from hpc_multibench.yaml_ingest import RunConfigurationModel, BenchModel, TestPlanModel
from hpc_multibench.configuration import DEFAULT_OUTPUT_DIRECTORY, RunConfiguration


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
    bench_name: str, bench: BenchModel, executables: dict[str, RunConfigurationModel]
) -> list[RunConfiguration]:
    """."""
    bench_run_configurations: list[RunConfiguration] = []
    # Iterate through matrix

    for matrix_variables in get_matrix_iterator(bench.matrix):
        print(matrix_variables)
        for executable_name in bench.run_configurations:
            if executable_name not in executables:
                raise RuntimeError(
                    f"'{executable_name}' not in list of defined run configurations!"
                )
            executable = executables[executable_name]
            output_file = (
                DEFAULT_OUTPUT_DIRECTORY
                / f"{bench_name}/{executable_name}__{get_matrix_variables_suffix(matrix_variables)}__%j.out"
            )
            run_configuration = executable.realise(
                executable_name,
                output_file,
            )

            for key, value in matrix_variables.items():
                if key == "args":
                    run_configuration.args = value

            bench_run_configurations.append(run_configuration)
    return bench_run_configurations


def get_benches(config_file: Path) -> dict[str, list[RunConfiguration]]:
    """."""
    test_plan = TestPlanModel.from_yaml(config_file)

    return {
        bench_name: get_bench(bench_name, bench, test_plan.run_configurations)
        for (bench_name, bench) in test_plan.benches.items()
    }

    # for (bench_name, bench) in test_plan.benches.items():
    #     for instance in variable:
    #         for executable in test_plan.executables:
