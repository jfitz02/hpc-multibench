#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A set of functions to analyse the results of a test bench run.

```python
from re import search as re_search

from hpc_multibench.yaml_model import RooflinePlotModel
from hpc_multibench.roofline_model import RooflineDataModel

PLOT_BACKEND: str = "seaborn"  # "plotext"

if PLOT_BACKEND == "plotext":
    import plotext as plt

    PLOTEXT_MARKER = "braille"
    PLOTEXT_THEME = "pro"
else:
    import matplotlib.pyplot as plt

    # from labellines import labelLines

    if PLOT_BACKEND == "seaborn":
        import pandas as pd
        import seaborn as sns

        sns.set_theme()


def extract_metrics(
    output: str, metric_definitions: dict[str, str]
) -> dict[str, str] | None:
    metrics: dict[str, str] = {}
    for metric, regex in metric_definitions.items():
        metric_search = re_search(regex, output)
        if metric_search is None:
            return None
        # TODO: Support multiple groups by lists as keys?
        metrics[metric] = metric_search.group(1)
    return metrics


def get_line_plot_data() -> dict[tuple[str, ...], list[tuple[float, float]]]:
    return {}


def draw_line_plot(data: dict[tuple[str, ...], list[tuple[float, float]]]) -> None:
    pass


def get_bar_chart_data() -> dict[tuple[str, ...], float]:
    return {}


def draw_bar_chart() -> None:
    pass


def get_roofline_plot_data() -> RooflineDataModel:
    pass


def draw_roofline_plot(title: str, data: RooflineDataModel) -> None:
    for label, memory_bound_data in data.memory_bound_ceilings.items():
        plt.plot(*zip(*memory_bound_data, strict=True), label=label)
    for label, compute_bound_data in data.compute_bound_ceilings.items():
        plt.plot(*zip(*compute_bound_data, strict=True), label=label)

    plt.xlabel("FLOPs/Byte")
    plt.ylabel("GFLOPs/sec")
    plt.xscale("log")
    plt.yscale("log")
    plt.legend()
    # for ax in plt.gcf().axes:
    #     labelLines(ax.get_lines())

    plt.title(title)
    plt.show()

```
"""
