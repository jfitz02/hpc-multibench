#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Docstring for an example tool."""

from enum import Enum, auto
from pathlib import Path

from hpc_multibench.analysis import analyse
from hpc_multibench.configuration import DEFAULT_OUTPUT_DIRECTORY, wait_till_queue_empty
from hpc_multibench.test_harness import get_benches

class Mode(Enum):
    RUN = auto()
    ANALYSE = auto()
    ALL = auto()


def main(yaml_path: Path, mode: Mode = Mode.ANALYSE) -> None:  # pragma: no cover
    """Run the tool."""
    benches = get_benches(yaml_path)
    
    if mode in (Mode.RUN, Mode.ALL):
        # Build and run the test benches from the YAML
        for bench in benches.values():
            for run in bench:
                run.run()

        # Wait till the test benches are done
        wait_till_queue_empty()

    if mode in (Mode.ANALYSE, Mode.ALL):
        # Perform analysis on the results of the run
        for bench_name in benches.keys():
            analyse(DEFAULT_OUTPUT_DIRECTORY / bench_name)
