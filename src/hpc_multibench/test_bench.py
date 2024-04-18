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
from re import search as re_search
from shutil import rmtree
from statistics import fmean, stdev
from time import sleep
from typing import Any

from typing_extensions import Self

from hpc_multibench.plot.export_data import export_data
from hpc_multibench.plot.plot_matplotlib import (
    draw_bar_chart,
    draw_line_plot,
    draw_roofline_plot,
)
from hpc_multibench.run_configuration import RunConfiguration, get_queued_job_ids
from hpc_multibench.uncertainties import UFloat
from hpc_multibench.yaml_model import BenchModel, RunConfigurationModel

DRY_RUN_SEPARATOR = "\n\n++++++++++\n\n\n"


@dataclass(frozen=True)
class RunConfigurationMetadata:
    """Data about run configurations to persist between program instances."""

    job_id: int
    rerun_count: int
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
        row["job_id"] = int(row["job_id"])
        row["rerun_count"] = int(row["rerun_count"])
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
        base_output_directory: Path,
    ) -> None:
        """Instantiate the test bench."""
        self.name = name
        self.run_configuration_models = run_configuration_models
        self.bench_model = bench_model
        self.base_output_directory = base_output_directory

        # Validate that all configurations named in the test bench are defined
        # in the test plan
        for run_configuration_name in bench_model.run_configurations:
            if run_configuration_name not in self.run_configuration_models:
                raise RuntimeError(
                    f"'{run_configuration_name}' not in list of"
                    " defined run configurations!"
                )

    @property
    def output_directory(self) -> Path:
        """Get the output directory for the test bench."""
        return self.base_output_directory / self.name

    @property
    def instantiations(self) -> list[dict[str, Any]]:
        """Get a list of run configuration instantiations from the test matrix."""
        shaped: list[list[list[tuple[str, Any]]]] = [
            (
                [[(key, value)] for value in values]
                if isinstance(key, str)
                else [list(zip(key, setting, strict=True)) for setting in values]
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

    @property
    def all_job_ids(self) -> list[int]:
        """Get the total number of jobs submitted by the test bench."""
        run_configurations_metadata = self.run_configurations_metadata
        if run_configurations_metadata is None:
            return []
        return [metadata.job_id for metadata in run_configurations_metadata]

    def wait_for_queue(
        self,
        max_time_to_wait: int = 172_800,
        backoff: list[int] | None = None,
        verbose: bool = True,  # noqa: FBT001, FBT002
    ) -> bool:
        """Wait till the queue is drained of jobs submitted by this test bench."""
        if backoff is None or len(backoff) < 1:
            backoff = [5, 10, 15, 30, 60]

        time_waited = 0
        backoff_index = 0
        while time_waited < max_time_to_wait:
            wait_time = backoff[backoff_index]
            sleep(wait_time)
            time_waited += wait_time

            queued_jobs = set(get_queued_job_ids())
            required_jobs = set(self.all_job_ids)
            if len(required_jobs - queued_jobs) == len(required_jobs):
                return False
            if verbose:
                print(
                    f"{len(required_jobs - queued_jobs)}/{len(required_jobs)} "
                    f"jobs left for test bench '{self.name}'"
                )

            if backoff_index < len(backoff) - 1:
                backoff_index += 1

        return True

    def record(self, args: Namespace) -> None:
        """Spawn run configurations for the test bench."""
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

        # TODO: Need to account for case where build commands is in the
        # matrix, then just needs to be a long chain of dependencies

        # Run all run configurations and store their slurm job ids
        run_configuration_job_ids: list[dict[int, RunConfiguration]] = []
        dry_run_outputs: list[str] = []
        for run_configurations in realised_run_configurations.values():
            # Add dependencies on the first job of that run configuration, so
            # you only need to build it once!
            first_job_id: int | None = None
            for run_configuration in run_configurations:
                rerun_map: dict[int, RunConfiguration] = {}
                for _ in range(self.bench_model.reruns.number):
                    if first_job_id is None:
                        if args.dry_run:
                            dry_run_outputs.append(str(run_configuration))
                            run_configuration.pre_built = True
                            continue
                        job_id = run_configuration.run()
                        first_job_id = job_id
                    else:
                        if args.dry_run:
                            dry_run_outputs.append(str(run_configuration))
                            continue
                        run_configuration.pre_built = True
                        job_id = run_configuration.run(dependencies=[first_job_id])
                    if job_id is None:
                        print(
                            f"Run configuration '{run_configuration.name}' "
                            f"with instantiation '{run_configuration.instantiation}' "
                            "failed to queue!"
                        )
                        continue
                    rerun_map[job_id] = run_configuration
                run_configuration_job_ids.append(rerun_map)

        # Stop after printing the run configurations if dry running
        if args.dry_run:
            print(DRY_RUN_SEPARATOR.join(dry_run_outputs))
            return

        # Store slurm job id mappings, excluding ones which failed to launch
        self.run_configurations_metadata = [
            RunConfigurationMetadata(
                job_id,
                rerun_count,
                run_configuration.name,
                run_configuration.get_true_output_file_name(job_id),
                run_configuration.instantiation,
            )
            for run_config_rerun_job_ids in run_configuration_job_ids
            for rerun_count, (job_id, run_configuration) in enumerate(
                run_config_rerun_job_ids.items()
            )
        ]

    def extract_metrics(self, output: str) -> dict[str, str] | None:
        """
        Extract the specified metrics from the output file.

        Note that run instantiations can be extracted via regex from output.
        """
        metrics: dict[str, str] = {}
        for metric, regex in self.bench_model.analysis.metrics.items():
            metric_search = re_search(regex, output)
            if metric_search is None:
                return None
            # TODO: Support multiple groups by lists as keys?
            metrics[metric] = metric_search.group(1)
        return metrics

    def get_run_outputs(
        self,
    ) -> list[dict[int, tuple[RunConfiguration, str | None]]] | None:
        """Get the outputs of the test bench runs."""
        if self.run_configurations_metadata is None:
            print(f"Metadata file does not exist for test bench '{self.name}'!")
            return None

        # Reconstruct realised run configurations from the metadata file
        reconstructed_run_configurations: list[dict[int, RunConfiguration]] = []
        prev_rerun_count: int = -1
        rerun_group: dict[int, RunConfiguration] = {}
        for metadata in self.run_configurations_metadata:
            # Split the data up by re-runs
            if metadata.rerun_count != prev_rerun_count + 1 and len(rerun_group) > 0:
                reconstructed_run_configurations.append(rerun_group)
                rerun_group = {}
            prev_rerun_count = metadata.rerun_count

            # Add the realised run configuration to its re-run dictionary
            if metadata.name not in self.run_configuration_models:
                # print(f"Skipping {metadata.name} since excluded from YAML file.")
                continue
            rerun_group[metadata.job_id] = self.run_configuration_models[
                metadata.name
            ].realise(metadata.name, self.output_directory, metadata.instantiation)
        reconstructed_run_configurations.append(rerun_group)

        # Collect outputs from the run configurations
        run_outputs: list[dict[int, tuple[RunConfiguration, str | None]]] = [
            {
                job_id: (run_configuration, run_configuration.collect(job_id))
                for job_id, run_configuration in rerun_group.items()
            }
            for rerun_group in reconstructed_run_configurations
        ]

        return run_outputs

    def get_run_metrics(
        self, run_outputs: list[dict[int, tuple[RunConfiguration, str | None]]]
    ) -> list[dict[int, tuple[RunConfiguration, dict[str, str]]]]:
        """."""
        run_metrics: list[dict[int, tuple[RunConfiguration, dict[str, str]]]] = []
        for rerun_group in run_outputs:
            rerun_metrics: dict[int, tuple[RunConfiguration, dict[str, str]]] = {}
            for job_id, (run_configuration, output) in rerun_group.items():
                if output is None:
                    print(
                        f"Run configuration '{run_configuration.name}'"
                        " has no output!"
                    )
                    continue

                metrics = self.extract_metrics(output)
                if metrics is None:
                    print(
                        "Unable to extract metrics from run"
                        f" configuration '{run_configuration.name}'!"
                    )
                    continue

                rerun_metrics[job_id] = (run_configuration, metrics)
            run_metrics.append(rerun_metrics)
        return run_metrics

    def aggregate_run_metrics(  # noqa: C901
        self, run_metrics: list[dict[int, tuple[RunConfiguration, dict[str, str]]]]
    ) -> list[tuple[RunConfiguration, dict[str, str | UFloat]]]:
        """."""
        all_aggregated_metrics: list[
            tuple[RunConfiguration, dict[str, str | UFloat]]
        ] = []
        for rerun_group in run_metrics:
            # Get the mapping of metrics to their values across re-runs
            canonical_run_configuration: RunConfiguration | None = None
            grouped_metrics: dict[str, list[str]] = {}
            for run_configuration, metrics in rerun_group.values():
                if canonical_run_configuration is None:
                    canonical_run_configuration = run_configuration

                for metric, value in metrics.items():
                    if metric not in grouped_metrics:
                        grouped_metrics[metric] = []
                    grouped_metrics[metric].append(value)

            aggregated_metrics: dict[str, str | UFloat] = {}
            reruns_model = self.bench_model.reruns
            for metric, values in grouped_metrics.items():
                # Just pick the first value of the metric if it cannot be
                # aggregated
                if (
                    reruns_model.number == 1
                    or metric in reruns_model.unaggregatable_metrics
                ):
                    aggregated_metrics[metric] = values[0]
                    continue

                # Remove highest then lowest in turn till depleted or one left
                pruned_values: list[float] = sorted([float(value) for value in values])
                highest_discard = reruns_model.highest_discard
                lowest_discard = reruns_model.lowest_discard
                while len(pruned_values) > 1 and (
                    highest_discard > 0 or lowest_discard > 0
                ):
                    if highest_discard > 0:
                        pruned_values = pruned_values[:-1]
                        highest_discard -= 1
                        if len(values) <= 1:
                            break
                    if lowest_discard > 0:
                        pruned_values = pruned_values[1:]
                        lowest_discard -= 1

                # Take the average and standard deviation of the metrics
                metric_mean = fmean(pruned_values)
                metric_stdev = (
                    stdev(pruned_values)
                    if reruns_model.undiscarded_number >= 2  # noqa: PLR2004
                    else 0.0
                )
                aggregated_metrics[metric] = UFloat(metric_mean, metric_stdev)

            # Update the metrics
            if canonical_run_configuration is not None:
                all_aggregated_metrics.append(
                    (canonical_run_configuration, aggregated_metrics)
                )

        return all_aggregated_metrics

    def calculate_derived_metrics(
        self, input_metrics: list[tuple[RunConfiguration, dict[str, str | UFloat]]]
    ) -> list[tuple[RunConfiguration, dict[str, str | UFloat]]]:
        """Calculate derived metrics from definitions in the YAML file."""
        output_metrics: list[tuple[RunConfiguration, dict[str, str | UFloat]]] = []

        # {"run configuration name" : {"run configuration name": {"instantation string": "instantation number"}}}
        instantiation_numbers: dict[str, dict[str, int]] = {}
        # {"run configuration name" : {"instantation #": {"metric": "value"}}}
        all_metrics: dict[str, dict[int, dict[str, str | UFloat]]] = {}
        for run_configuration, metrics in input_metrics:
            if run_configuration.instantiation is None:
                continue
            if run_configuration.name not in instantiation_numbers:
                instantiation_numbers[run_configuration.name] = {}
            instantiation_number = len(instantiation_numbers[run_configuration.name])
            instantiation_numbers[run_configuration.name][
                RunConfiguration.get_instantiation_repr(run_configuration.instantiation)
            ] = instantiation_number

            if run_configuration.name not in all_metrics:
                all_metrics[run_configuration.name] = {}
            all_metrics[run_configuration.name][instantiation_number] = metrics

        for run_configuration, metrics in input_metrics:
            if run_configuration.instantiation is None:
                continue
            instantiation_number = instantiation_numbers[run_configuration.name][
                RunConfiguration.get_instantiation_repr(run_configuration.instantiation)
            ]

            # Present a helpful data structure for accessing other run configurations
            # Comparisons are made instantiation-wise, so elise that variable
            # {"run configuration name": {"metric": "value"}}
            _corresponding_metrics: dict[str, dict[str, str | UFloat]] = {
                run_configuration_name: instantiation_metrics
                for (
                    run_configuration_name,
                    run_configuration_metrics,
                ) in all_metrics.items()
                for (
                    iter_instantiation_number,
                    instantiation_metrics,
                ) in run_configuration_metrics.items()
                if instantiation_number == iter_instantiation_number
            }
            # {"instantiation #": {"metric": "value"}}
            _sequential_metrics: dict[int, dict[str, str | UFloat]] = all_metrics[
                run_configuration.name
            ]

            for (
                metric,
                derivation,
            ) in self.bench_model.analysis.derived_metrics.items():
                value = eval(derivation)  # nosec: B307 # noqa: S307
                if hasattr(value, "nominal_value") and hasattr(value, "std_dev"):
                    value = UFloat(value.nominal_value, value.std_dev)
                metrics[metric] = value
            output_metrics.append((run_configuration, metrics))

        return output_metrics

    def report(self) -> None:
        """Analyse completed run configurations for the test bench."""
        run_outputs = self.get_run_outputs()
        if run_outputs is None:
            return

        run_metrics = self.get_run_metrics(run_outputs)
        aggregated_metrics = self.aggregate_run_metrics(run_metrics)
        derived_metrics = self.calculate_derived_metrics(aggregated_metrics)

        # Draw the specified plots
        for line_plot in self.bench_model.analysis.line_plots:
            if not line_plot.enabled:
                continue
            draw_line_plot(line_plot, derived_metrics)

        for bar_chart in self.bench_model.analysis.bar_charts:
            if not bar_chart.enabled:
                continue
            draw_bar_chart(bar_chart, derived_metrics)

        for roofline_plot in self.bench_model.analysis.roofline_plots:
            if not roofline_plot.enabled:
                continue
            draw_roofline_plot(roofline_plot, derived_metrics)

        for export_schema in self.bench_model.analysis.data_exports:
            if not export_schema.enabled:
                continue
            export_data(export_schema, derived_metrics)
