#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A class representing the test plan defined from YAML for a tool run."""

from pathlib import Path

from hpc_multibench.yaml_model import TestPlanModel


class TestPlan:
    """The test plan defined from YAML for a tool run."""

    def __init__(self, yaml_path: Path) -> None:
        """Instantiate the test plan from a YAML file."""
        self.test_plan_model = TestPlanModel.from_yaml(yaml_path)

    def record(self) -> None:
        """Run all the test benches in the plan."""
        print(self.test_plan_model)

    def report(self) -> None:
        """Analyse all the test benches in the plan."""
