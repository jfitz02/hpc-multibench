#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The main function for the HPC MultiBench tool."""

from argparse import ArgumentParser, Namespace
from pathlib import Path

from hpc_multibench.test_plan import TestPlan


def get_parser() -> ArgumentParser:
    """Get the argument parser for the tool."""
    parser = ArgumentParser(description="A tool to spawn and analyse HPC jobs.")
    parser.add_argument(
        "yaml_path", type=Path, help="the path to the configuration YAML file"
    )
    # TODO: add subcommands for `record`, `report`, and `interactive`
    # TODO: add flags `--dry-run`, `--clobber` and `--no-wait` for `record` subcommand
    return parser


def main() -> None:  # pragma: no cover
    """Run the tool."""
    args: Namespace = get_parser().parse_args()

    test_plan = TestPlan(args.yaml_path)
    test_plan.record()
