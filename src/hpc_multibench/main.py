#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Docstring for an example tool."""

from pathlib import Path

from hpc_multibench.analysis import analyse
from hpc_multibench.configuration import DEFAULT_OUTPUT_DIRECTORY, wait_till_queue_empty
from hpc_multibench.yaml_ingest import get_benches

DRY_RUN: bool = True


def main(yaml_path: Path) -> None:  # pragma: no cover
    """Run the tool."""
    # Build and run the test benches from the YAML
    for bench in get_benches(yaml_path).values():
        for run in bench:
            if DRY_RUN:
                print(run)
            else:
                run.run()

    # Coudl do different modes? run/analyse/all

    # Wait till the test benches are don
    if not DRY_RUN:
        wait_till_queue_empty()

    # Perform analysis on the results of the run
    analyse(DEFAULT_OUTPUT_DIRECTORY)
