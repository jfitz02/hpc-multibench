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

from hpc_multibench.configuration import RunConfiguration


class Executable(BaseModel):
    """."""

    sbatch_config: dict[str, Any]
    module_loads: list[str]
    environment_variables: dict[str, Any]
    directory: Path
    build_commands: list[str]
    run_command: str
    args: str | None = None


class Bench(BaseModel):
    """."""

    executables: list[str]
    matrix: list[dict[str, list[Any]]]


class TestPlan(BaseModel):
    """."""

    executables: dict[str, Executable]
    benches: dict[str, Bench]


def get_test_plan(config_file: Path) -> TestPlan:
    """."""
    with config_file.open(encoding="utf-8") as config_handle:
        config_data = yaml.safe_load(config_handle)
    return TestPlan(**config_data)


def get_run_configuration(name: str, executable: Executable) -> RunConfiguration:
    """."""
    run = RunConfiguration(executable.run_command)
    run.name = name
    run.sbatch_config = executable.sbatch_config
    run.module_loads = executable.module_loads
    run.environment_variables = executable.environment_variables
    run.directory = Path(executable.directory)
    run.build_commands = executable.build_commands
    run.args = executable.args
    return run


def get_bench(
    bench_name: str, bench: Bench, executables: dict[str, Executable]
) -> list[RunConfiguration]:
    """."""
    bench_run_configurations: list[RunConfiguration] = []
    # Iterate through matrix
    for executable_name in bench.executables:
        if executable_name not in executables:
            raise RuntimeError(
                f"Executable '{executable_name}' not in list of defined executables!"
            )
        executable = executables[executable_name]

        # Update executable based on matrix
        bench_run_configurations.append(
            get_run_configuration(f"{bench_name}/{executable_name}", executable)
        )
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
