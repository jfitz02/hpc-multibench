#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Docstring for an example tool."""

from pathlib import Path

from hpc_multibench.configuration import wait_till_queue_empty
from hpc_multibench.yaml_ingest import get_benches


def main(yaml_path: Path) -> None:  # pragma: no cover
    """Run the tool."""
    for bench in get_benches(yaml_path).values():
        for run in bench:
            run.run()
    wait_till_queue_empty()
    print("Done!")
