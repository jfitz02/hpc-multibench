#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A class representing the test plan defined from YAML for a tool run."""

from argparse import Namespace
from copy import deepcopy
from pathlib import Path

from hpc_multibench.test_bench import TestBench
from hpc_multibench.yaml_model import TestPlanModel


class TestPlan:
    """The test plan defined from YAML for a tool run."""

    def __init__(self, yaml_path: Path) -> None:
        """Instantiate the test plan from a YAML file."""
        self.yaml_path = yaml_path
        test_plan_model = TestPlanModel.from_yaml(yaml_path)
        self.benches = [
            TestBench(
                name=bench_name,
                run_configuration_models={
                    name: deepcopy(config)
                    for name, config in test_plan_model.run_configurations.items()
                    if name in bench_model.run_configurations
                },
                bench_model=bench_model,
            )
            for bench_name, bench_model in test_plan_model.benches.items()
        ]

    def record_all(self, args: Namespace) -> None:
        """Run all the enabled test benches in the plan."""
        for bench in self.benches:
            if bench.bench_model.enabled:
                print(f"Recording data from test bench '{bench.name}'")
                bench.record(args)

        if args.wait:
            for bench in self.benches:
                if bench.bench_model.enabled:
                    status = (
                        "timed out while waiting for queued jobs"
                        if bench.wait_for_queue()
                        else "finished all queued jobs"
                    )
                    print(f"Test bench '{bench.name}' {status}!")

    def report_all(self, _args: Namespace) -> None:
        """Analyse all the enabled test benches in the plan."""
        for bench in self.benches:
            if bench.bench_model.enabled:
                print(f"Reporting data from test bench '{bench.name}'")
                bench.report()
