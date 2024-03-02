#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A class representing a test bench composing part of a test plan."""

from argparse import Namespace
from base64 import b64decode, b64encode
from csv import DictReader, DictWriter
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from pickle import dumps as pickle_dumps  # nosec
from pickle import loads as pickle_loads  # nosec
from shutil import rmtree
from typing import TYPE_CHECKING, Any

from typing_extensions import Self

from hpc_multibench.analysis import (  # extract_metrics,
    draw_bar_chart,
    draw_line_plot,
    draw_roofline_plot,
)
from hpc_multibench.yaml_model import BenchModel, RunConfigurationModel

if TYPE_CHECKING:
    from hpc_multibench.run_configuration import RunConfiguration

BASE_OUTPUT_DIRECTORY = Path("results/")


@dataclass(frozen=True)
class RunConfigurationMetadata:
    """Data about run configurations to persist between program instances."""

    job_id: int
    name: str
    output_file_name: str
    instantiation: dict[str, Any] | None

    def as_csv_row(self) -> dict[str, Any]:
        """Get a representation of the data able to be written to a CSV file."""
        row = self.__dict__
        row["instantiation"] = b64encode(pickle_dumps(row["instantiation"])).decode(
            "ascii"
        )
        return row

    @classmethod
    def from_csv_row(cls, row: dict[str, Any]) -> Self:
        """Construct the object from a representation usable in CSV files."""
        row["instantiation"] = pickle_loads(  # noqa: S301 # nosec
            b64decode(row["instantiation"])
        )
        return cls(**row)

    @classmethod
    def fields(cls) -> list[str]:
        """Return the field names of the dataclass."""
        return list(cls.__annotations__)


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
        return self.output_directory / "runs_metadata.csv"

    @property
    def run_configurations_metadata(self) -> list[RunConfigurationMetadata] | None:
        """Retrieve the run configuration metadata from its file."""
        if not self._run_configurations_metadata_file.exists():
            return None

        with self._run_configurations_metadata_file.open("r") as metadata_file:
            metadata_reader = DictReader(metadata_file)
            return [
                RunConfigurationMetadata.from_csv_row(row) for row in metadata_reader
            ]

    @run_configurations_metadata.setter
    def run_configurations_metadata(
        self, metadata: list[RunConfigurationMetadata]
    ) -> None:
        """
        Write out the run configuration metadata to its file.

        TODO: Consider whether this is actually right abstraction for passing
        between program runs.
        """
        existing_metadata = self.run_configurations_metadata
        with self._run_configurations_metadata_file.open("w+") as metadata_file:
            metadata_writer = DictWriter(
                metadata_file, fieldnames=RunConfigurationMetadata.fields()
            )
            metadata_writer.writeheader()
            if existing_metadata is not None:
                metadata_writer.writerows(
                    item.as_csv_row() for item in existing_metadata
                )
            metadata_writer.writerows(item.as_csv_row() for item in metadata)

    def record(self, args: Namespace) -> None:
        """Spawn run configurations for the test bench."""
        print(f"Recording data from test bench '{self.name}'")

        # Optionally clobber directory
        if not args.no_clobber and self.output_directory.exists():
            rmtree(self.output_directory)

        # Realise run configurations from list of instantiations, split up
        # by model so they only get built once
        realised_run_configurations: dict[str, list[RunConfiguration]] = {
            run_name: [
                run_model.realise(run_name, self.output_directory, instantiation)
                for instantiation in self.instantiations
            ]
            for run_name, run_model in self.run_configuration_models.items()
        }

        # Optionally dry run then stop before actually running
        if args.dry_run:
            # TODO: Could be closer inside the running logic
            for run_configurations in realised_run_configurations.values():
                first_flag: bool = True
                for run_configuration in run_configurations:
                    if first_flag:
                        first_flag = False
                    else:
                        run_configuration.pre_built = True
                    print(run_configuration, end="\n\n")
            return

        # TODO: Need to account for case where build commands is in the
        # matrix, then just needs to be a long chain of dependencies
        # TODO: Could spawn an extra job to just build then not run, which
        # everything else depends on? Probably better to document that fastest
        # job should be first, avoids spawning extraneous jobs which could all
        # fail if the configuration is wrong...

        # Run all run configurations and store their slurm job ids
        run_configuration_job_ids: dict[RunConfiguration, int | None] = {}
        for run_configurations in realised_run_configurations.values():
            # Add dependencies on the first job of that run configuration, so
            # you only need to build it once!
            first_job_id: int | None = None
            for run_configuration in run_configurations:
                if first_job_id is None:
                    job_id = run_configuration.run()
                    first_job_id = job_id
                else:
                    run_configuration.pre_built = True
                    job_id = run_configuration.run(dependencies=[first_job_id])
                run_configuration_job_ids[run_configuration] = job_id

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

        if args.wait:
            raise NotImplementedError("Waiting for queue not yet implemented")

    def report(self) -> None:
        """Analyse completed run configurations for the test bench."""
        print(f"Reporting data from test bench '{self.name}'")
        if self.run_configurations_metadata is None:
            print(f"Metadata file does not exist for test bench '{self.name}'!")
            return

        # TODO: Could type alias for slurm job id?
        # TODO: Error handling for name not being in models?
        # Reconstruct realised run configurations from the metadata file
        reconstructed_run_configurations: dict[int, RunConfiguration] = {
            metadata.job_id: self.run_configuration_models[metadata.name].realise(
                metadata.name, self.output_directory, metadata.instantiation
            )
            for metadata in self.run_configurations_metadata
        }

        # Collect outputs from the run configurations
        # TODO: Add async wait for incomplete jobs
        run_outputs: dict[int, tuple[RunConfiguration, str | None]] = {
            job_id: (run_configuration, run_configuration.collect(job_id))
            for job_id, run_configuration in reconstructed_run_configurations.items()
        }

        # # Extract the metrics from the outputs of the jobs
        # run_metrics: list[tuple[RunConfiguration, dict[str, str] | None]] = [
        #     (
        #         run_configuration,
        #         extract_metrics(output, self.bench_model.analysis.metrics),
        #     )
        #     for run_configuration, output in run_outputs.values()
        #     if output is not None
        # ]

        # Draw the specified line plots
        for line_plot in self.bench_model.analysis.line_plots:
            draw_line_plot(line_plot, run_outputs, self.bench_model.analysis.metrics)

        for bar_chart in self.bench_model.analysis.bar_charts:
            draw_bar_chart(bar_chart, run_outputs, self.bench_model.analysis.metrics)

        for roofline_plot in self.bench_model.analysis.roofline_plots:
            draw_roofline_plot(
                roofline_plot, run_outputs, self.bench_model.analysis.metrics
            )
