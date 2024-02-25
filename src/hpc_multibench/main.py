#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The main function for the HPC MultiBench tool."""

from argparse import ArgumentParser
from pathlib import Path

from hpc_multibench.test_plan import TestPlan


def get_parser() -> ArgumentParser:  # pragma: no cover
    """Get the argument parser for the tool."""
    parser = ArgumentParser(description="A tool to spawn and analyse HPC jobs.")
    parser.add_argument(
        "-y",
        "--yaml-path",
        required=True,
        type=Path,
        help="the path to the configuration YAML file",
    )
    # # Consider ergonomics of `subcommand yaml_path`, when running `record`
    # # then `report` on same yaml file in sequence
    # for sub_parser in (parser_record, parser_report, parser_interactive):
    #     sub_parser.add_argument(
    #         "yaml_path", type=Path, help="the path to the configuration YAML file"
    #     )

    sub_parsers = parser.add_subparsers(dest="command", required=True)
    parser_record = sub_parsers.add_parser(
        "record", help="record data from running the test benches"
    )
    parser_record.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="print but don't submit the generated sbatch files",
    )
    parser_record.add_argument(
        "-n",
        "--no-wait",
        action="store_true",
        help="don't wait for the submitted jobs to finish to exit",
    )
    parser_record.add_argument(
        "-c",
        "--clobber",
        action="store_true",
        help="delete any previous run results of the test benches",
    )
    _parser_report = sub_parsers.add_parser(
        "report", help="report analysis about completed test bench runs"
    )
    _parser_interactive = sub_parsers.add_parser(
        "interactive", help="launch interactive mode"
    )
    return parser


def main() -> None:  # pragma: no cover
    """Run the tool."""
    args = get_parser().parse_args()
    test_plan = TestPlan(args.yaml_path)

    if args.command == "record":
        test_plan.record_all(args)

    elif args.command == "report":
        test_plan.report_all(args)

    elif args.command == "interactive":
        raise NotImplementedError("Interactive mode is not implemented!")
