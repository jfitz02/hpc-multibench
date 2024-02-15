#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utility functions to analyse the runs resulting from the test matrix."""

from pathlib import Path
from re import search as re_search

NAME_REGEX = r"===== RUN (.*) ====="
DIMENSIONS_NAMES = ("nx", "ny", "nz")
DIMENSIONS_REGEX = "".join([name + r": (\d+)\s+" for name in DIMENSIONS_NAMES])
METRIC_NAMES = ("Total", "DDOT", "WAXPBY", "SPARSEMV")
TIMES_REGEX = r"Time Summary:\s+" + "".join(
    [name + r"\s*: ([\d\.]+)\s+" for name in METRIC_NAMES]
)
FLOPS_REGEX = r"FLOPS Summary:\s+" + "".join(
    [name + r"\s*: ([\d\.]+)\s+" for name in METRIC_NAMES]
)
MFLOPS_REGEX = r"MFLOPS Summary:\s+" + "".join(
    [name + r"\s*: ([\d\.]+)\s+" for name in METRIC_NAMES]
)


METRICS_REGEXES: dict[tuple[str, ...], str] = {
    ("name",): NAME_REGEX,
    DIMENSIONS_NAMES: DIMENSIONS_REGEX,
    tuple([f"{metric} time" for metric in METRIC_NAMES]): TIMES_REGEX,
    tuple([f"{metric} flops" for metric in METRIC_NAMES]): FLOPS_REGEX,
    tuple([f"{metric} mflops" for metric in METRIC_NAMES]): MFLOPS_REGEX,
}


def parse(results_file: Path) -> dict[str, str] | None:
    """."""
    run_output = results_file.read_text(encoding="utf-8")

    results: dict[str, str] = {}
    for names, regex in METRICS_REGEXES.items():
        for i,name in enumerate(names):
            metric_search = re_search(regex, run_output)
            if metric_search is None:
                return None
            results[name] = metric_search.group(i+1)
    return results


def analyse(output_directory: Path) -> None:
    """."""
    for results_file in output_directory.iterdir():
        print(f"Parsing {results_file}")
        results = parse(results_file)
        print(f"Got results: {results}\n")
        # Consider parsing into a pandas dataframe?
