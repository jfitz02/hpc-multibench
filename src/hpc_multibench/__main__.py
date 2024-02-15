#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A python template project."""

from pathlib import Path

from hpc_multibench.main import main

if __name__ == "__main__":
    main(Path("./yaml_examples/kudu_plan.yaml"))
