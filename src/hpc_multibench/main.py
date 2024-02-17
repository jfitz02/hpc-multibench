#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Docstring for an example tool."""

from enum import Enum, auto
from pathlib import Path

from hpc_multibench.configuration import wait_till_queue_empty
from hpc_multibench.yaml_model import TestPlan


class Mode(Enum):
    RUN = auto()
    ANALYSE = auto()
    ALL = auto()


def main(yaml_path: Path, mode: Mode = Mode.RUN) -> None:  # pragma: no cover
    """Run the tool."""

    test_plan = TestPlan.from_yaml(yaml_path)

    if mode in (Mode.RUN, Mode.ALL):
        test_plan.run()

    if mode == Mode.ALL:
        wait_till_queue_empty()

    if mode in (Mode.ANALYSE, Mode.ALL):
        test_plan.analyse()
