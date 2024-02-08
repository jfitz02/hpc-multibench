#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Docstring for an example tool."""

from pathlib import Path

from yaml_ingest import absurd
from configuration import RunConfiguration

def get_greeting() -> str:
    """Get a string greeting."""
    return "Hello world!"


def get_cpp_reference_impl() -> RunConfiguration:
    """Build a run configuration for the reference implementation."""
    run = RunConfiguration("./test_HPCCG")
    run.build_commands = ["make -j 8"]
    run.sbatch_config = {
        "nodes": "1",
        "ntasks-per-node": "1",
        "cpus-per-task": "1",
        "mem-per-cpu": "3700",  # max on avon?
    }
    run.module_loads = ["GCC/11.3.0"]
    run.directory = Path("../0_cpp_versions/0_ref")
    return run


def main() -> None:  # pragma: no cover
    """Say hello."""
    print(get_greeting())
    print(absurd())
    print(get_cpp_reference_impl())
