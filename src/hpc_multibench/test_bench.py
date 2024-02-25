#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A class representing a test bench composing part of a test plan."""

from argparse import Namespace
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from pickle import dump as pickle_dump  # nosec
from pickle import load as pickle_load  # nosec
from shutil import rmtree
from typing import Any

from hpc_multibench.yaml_model import BenchModel, RunConfigurationModel

BASE_OUTPUT_DIRECTORY = Path("results/")


@dataclass
class RunConfigurationMetadata:
    """Data about run configurations to persist between program instances."""

    job_id: int
    name: str
    output_file_name: str
    instantiation: dict[str, Any] | None


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

    @property
    def _run_configurations_metadata_file(self) -> Path:
        """Get the path to the file to save the run configuration metadata."""
        return self.output_directory / "run_configs.pickle"

    @property
    def run_configurations_metadata(self) -> list[RunConfigurationMetadata]:
        """Retrieve the run configuration metadata from its file."""
        # if not self._run_configurations_metadata_file.exists():
        #     pass
        # TODO: Could store in human-readable format, pickling only instantations
        with self._run_configurations_metadata_file.open("rb") as metadata_file:
            return pickle_load(metadata_file)  # type: ignore # noqa: PGH003, S301 # nosec

    @run_configurations_metadata.setter
    def run_configurations_metadata(
        self, metadata: list[RunConfigurationMetadata]
    ) -> None:
        """Write out the run configuration metadata to its file."""
        with self._run_configurations_metadata_file.open("wb+") as metadata_file:
            pickle_dump(metadata, metadata_file)

    def record(self, args: Namespace) -> None:
        """Spawn run configurations for the test bench."""
        print(f"Recording data from test bench '{self.name}'")

        # Optionally clobber directory
        if args.clobber:
            rmtree(self.output_directory)

        # Realise run configurations from list of instantiations
        run_configurations = [
            run_model.realise(run_name, self.output_directory, instantiation)
            for instantiation in self.instantiations
            for run_name, run_model in self.run_configuration_models.items()
        ]

        # Optionally dry run then stop before actually running
        if args.dry_run:
            for run_configuration in run_configurations:
                print(run_configuration, end="\n\n")
            return

        # Run all run configurations and store their slurm job ids
        run_configuration_job_ids = {
            run_configuration: run_configuration.run()
            for run_configuration in run_configurations
        }

        # Store slurm job id mappings, excluding ones which failed to launch
        self.run_configurations_metadata = [
            RunConfigurationMetadata(
                job_id,
                run_configuration.name,
                run_configuration.get_true_output_file_name(job_id),
                run_configuration.instantiation,
            )
            for run_configuration, job_id in run_configuration_job_ids.items()
            if job_id is not None
        ]

        if not args.no_wait:
            raise NotImplementedError("Waiting for queue not yet implemented")

    def report(self) -> None:
        """Analyse completed run configurations for the test bench."""
        print(f"Reporting data from test bench '{self.name}'")
        print(
            f"x: {self.bench_model.analysis.plot.x}, "
            f"y: {self.bench_model.analysis.plot.y}"
        )
        # TODO: Add better error message...
        print("\n".join(str(x) for x in self.run_configurations_metadata))
        # Load mappings from run config/args to slurm job ids
        # Collect outputs of all slurm job ids
        # Print outputs/do analysis
