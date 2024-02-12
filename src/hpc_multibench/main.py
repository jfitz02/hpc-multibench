#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Docstring for an example tool."""

from pathlib import Path

from hpc_multibench.yaml_ingest import get_benches


def main() -> None:  # pragma: no cover
    """Run the tool."""
    yaml_path = Path("./yaml_examples/cpp_rust_comp_plan.yaml")
    benches = get_benches(yaml_path)
    print(benches)
