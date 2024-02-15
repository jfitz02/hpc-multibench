#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utility functions to analyse the runs resulting from the test matrix."""

from pathlib import Path
from re import search as re_search

from hpc_multibench.configuration import DEFAULT_OUTPUT_DIRECTORY
from hpc_multibench.yaml_ingest import Bench

METRICS_REGEXES: dict[str, str] = {
    "name": r"===== RUN (.*) =====",
    "nx": r"nx: (\d+)",
    "ny": r"ny: (\d+)",
    "nz": r"nz: (\d+)",
    "total time": r"Time Summary:[\s\S]*Total\s*: ([\d\.]+)[\s\S]*\nFLOPS Summary",
    "ddot time": r"Time Summary:[\s\S]*DDOT\s*: ([\d\.]+)[\s\S]*\nFLOPS Summary",
    "waxpby time": r"Time Summary:[\s\S]*WAXPBY\s*: ([\d\.]+)[\s\S]*\nFLOPS Summary",
    "sparsemv time": r"Time Summary:[\s\S]*SPARSEMV\s*: ([\d\.]+)[\s\S]*\nFLOPS Summary",
    "total flops": r"FLOPS Summary:[\s\S]*Total\s*: ([\d\.]+)[\s\S]*\nMFLOPS Summary",
    "ddot flops": r"FLOPS Summary:[\s\S]*DDOT\s*: ([\d\.]+)[\s\S]*\nMFLOPS Summary",
    "waxpby flops": r"FLOPS Summary:[\s\S]*WAXPBY\s*: ([\d\.]+)[\s\S]*\nMFLOPS Summary",
    "sparsemv flops": r"FLOPS Summary:[\s\S]*SPARSEMV\s*: ([\d\.]+)[\s\S]*\nMFLOPS Summary",
    "total mflops": r"MFLOPS Summary:[\s\S]*Total\s*: ([\d\.]+)",
    "ddot mflops": r"MFLOPS Summary:[\s\S]*DDOT\s*: ([\d\.]+)",
    "waxpby mflops": r"MFLOPS Summary:[\s\S]*WAXPBY\s*: ([\d\.]+)",
    "sparsemv mflops": r"MFLOPS Summary:[\s\S]*SPARSEMV\s*: ([\d\.]+)",
}


def parse(results_file: Path, metrics: dict[str, str]) -> dict[str, str] | None:
    """."""
    run_output = results_file.read_text(encoding="utf-8")

    results: dict[str, str] = {}
    for name, regex in metrics.items():
        metric_search = re_search(regex, run_output)
        if metric_search is None:
            return None
        # Could support multiple groups by lists as keys?
        results[name] = metric_search.group(1)
    return results


def analyse(output_directory: Path) -> None:
    """."""
    for results_file in output_directory.iterdir():
        print(f"Parsing {results_file}")
        results = parse(results_file, METRICS_REGEXES)
        print(f"Got results: {results}\n")
        # Consider parsing into a pandas dataframe?
