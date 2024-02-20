#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Docstring for an example tool."""

from argparse import ArgumentParser, Namespace
from enum import Enum, auto
from pathlib import Path

from hpc_multibench.tui.user_interface import UserInterface
from hpc_multibench.yaml_model import TestPlan


class Mode(Enum):
    """."""

    RUN = auto()
    ANALYSE = auto()
    ALL = auto()


def get_parser() -> ArgumentParser:
    """Get the argument parser for the tool."""
    parser = ArgumentParser(description="A tool to spawn and analyse HPC jobs.")
    parser.add_argument(
        "yaml_path", type=Path, help="the path to the configuration YAML file"
    )
    mutex_group = parser.add_mutually_exclusive_group()
    mutex_group.add_argument(
        "-m",
        "--mode",
        type=Mode,
        default=Mode.RUN,
        help="the mode to run the tool in (default: run)",
    )
    mutex_group.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="show the interactive TUI",
    )
    return parser


def main() -> None:  # pragma: no cover
    """Run the tool."""
    # We can set yaml_path to `Path("./yaml_examples/kudu_plan.yaml")`
    args: Namespace = get_parser().parse_args()
    test_plan = TestPlan.from_yaml(args.yaml_path)

    if args.interactive:
        UserInterface(test_plan).run()

    else:
        if args.mode in (Mode.RUN, Mode.ALL):
            test_plan.run()

        if args.mode == Mode.ALL:
            pass  # wait_till_queue_empty()

        if args.mode in (Mode.ANALYSE, Mode.ALL):
            test_plan.analyse()
