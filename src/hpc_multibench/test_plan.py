#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A class representing the test plan defined from YAML for a tool run."""

from copy import deepcopy
from pathlib import Path

from hpc_multibench.test_bench import TestBench
from hpc_multibench.yaml_model import TestPlanModel


class TestPlan:
    """The test plan defined from YAML for a tool run."""

    def __init__(self, yaml_path: Path) -> None:
        """Instantiate the test plan from a YAML file."""
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

    def record_all(self) -> None:
        """Run all the enabled test benches in the plan."""
        for bench in self.benches:
            if bench.bench_model.enabled:
                bench.record(dry_run=True)

    def report_all(self) -> None:
        """Analyse all the enabled test benches in the plan."""
        for bench in self.benches:
            if bench.bench_model.enabled:
                bench.report()
