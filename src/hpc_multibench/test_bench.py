#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A class representing a test bench composing part of a test plan."""


from hpc_multibench.yaml_model import RunConfigurationModel, BenchModel

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

    def record(
        self, clobber: bool = False, dry_run: bool = False, no_wait: bool = False
    ) -> None:
        """."""
        print(self.name)
        # Optionally clobber directory
        # Get instantiations from variable matrix
        # Realise run configurations from list of instantiations
        # Optionally dry run then return
        # Run all run configurations
        # Optionally wait for all run configurations to dequeue/terminate

    def report(self) -> None:
        """."""
        # Load mappings from run config/args to slurm job ids
        # Collect outputs of all slurm job ids
        # Print outputs/do analysis
