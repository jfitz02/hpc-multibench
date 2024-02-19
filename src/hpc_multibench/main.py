#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Docstring for an example tool."""

from enum import Enum, auto
from pathlib import Path

# from hpc_multibench.tui.user_interface import UserInterface
from hpc_multibench.yaml_model import TestPlan


class Mode(Enum):
    """."""

    RUN = auto()
    ANALYSE = auto()
    ALL = auto()


def main(yaml_path: Path, mode: Mode = Mode.ANALYSE) -> None:  # pragma: no cover
    """Run the tool."""
    test_plan = TestPlan.from_yaml(yaml_path)

    # UserInterface(test_plan).run()

    if mode in (Mode.RUN, Mode.ALL):
        test_plan.run()

    if mode == Mode.ALL:
        pass  # wait_till_queue_empty()

    if mode in (Mode.ANALYSE, Mode.ALL):
        test_plan.analyse()
