#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A class representing a test bench composing part of a test plan."""

from itertools import product
from pathlib import Path
from shutil import rmtree
from typing import TYPE_CHECKING, Any

from hpc_multibench.yaml_model import BenchModel, RunConfigurationModel

if TYPE_CHECKING:
    from hpc_multibench.run_configuration import RunConfiguration

BASE_OUTPUT_DIRECTORY = Path("results/")


class TestBench:
    """A test bench composing part of a test plan."""

    def __init__(
        self,
        name: str,
        run_configuration_models: dict[str, RunConfigurationModel],
        bench_model: BenchModel,
    ) -> None:
        """Instantiate the test bench."""
        self.name = name
        self.run_configuration_models = run_configuration_models
        self.bench_model = bench_model
        self.run_configurations: list[RunConfiguration] | None = None

        # Validate that all configurations named in the test bench are defined
        # in the test plan
        for run_configuration_name in bench_model.run_configurations:
            if run_configuration_name not in self.run_configuration_models.keys():
                raise RuntimeError(
                    f"'{run_configuration_name}' not in list of"
                    " defined run configurations!"
                )

    @property
    def output_directory(self) -> Path:
        """Get the output directory for the test bench."""
        return BASE_OUTPUT_DIRECTORY / self.name

    @property
    def instantiations(self) -> list[dict[str, Any]]:
        """Get a list of run configuration instantiations from the test matrix."""
        shaped: list[list[list[tuple[str, Any]]]] = [
            (
                [[(key, value)] for value in values]
                if isinstance(key, str)
                else [
                    [(k, v) for k, v in zip(key, setting, strict=True)]
                    for setting in values
                ]
            )
            for key, values in self.bench_model.matrix.items()
        ]
        return [
            {item[0]: item[1] for items in combination for item in items}
            for combination in product(*shaped)
        ]

    def record(
        self, clobber: bool = False, dry_run: bool = False, no_wait: bool = False
    ) -> None:
        """Spawn run configurations for the test bench."""
        print(f"Recording data from test bench '{self.name}'")

        # Optionally clobber directory
        if clobber:
            rmtree(self.output_directory)

        # Get instantiations from variable matrix
        print(self.instantiations)

        # Realise run configurations from list of instantiations
        self.run_configurations = [
            run_model.realise(self.name, run_name, instantiation)
            for instantiation in self.instantiations
            for run_name, run_model in self.run_configuration_models.items()
        ]

        # Optionally dry run then return
        if dry_run:
            for run_configuration in self.run_configurations:
                print(run_configuration, end="\n\n")
            return

        # Run all run configurations
        for run_configuration in self.run_configurations:
            # TODO: Need to store slurm job id mappings
            run_configuration.run()

        # Store slurm job id mappings

        # TODO: Optionally wait for all run configurations to dequeue/terminate

    def report(self) -> None:
        """Analyse completed run configurations for the test bench."""
        print(f"Reporting data from test bench '{self.name}'")
        # Load mappings from run config/args to slurm job ids
        # Collect outputs of all slurm job ids
        # Print outputs/do analysis
