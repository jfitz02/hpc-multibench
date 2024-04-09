#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A set of functions using plotext to plot the results of a test bench run."""

from typing import Any

from hpc_multibench.plot.plot_data import (
    get_bar_chart_data,
    get_line_plot_data,
    get_roofline_plot_data,
)
from hpc_multibench.run_configuration import RunConfiguration
from hpc_multibench.uncertainties import UFloat
from hpc_multibench.yaml_model import BarChartModel, LinePlotModel, RooflinePlotModel

PLOTEXT_MARKER = "braille"
PLOTEXT_THEME = "pro"


def draw_line_plot(
    this_plt: Any,
    plot: LinePlotModel,
    metrics: list[tuple[RunConfiguration, dict[str, str | UFloat]]],
) -> None:
    """Draw a line plot from data using the provided plotext backend."""
    data = get_line_plot_data(plot, metrics)

    this_plt.clear_figure()
    for name, (x, y, _x_err, _y_err) in data.items():
        this_plt.plot(x, y, marker=PLOTEXT_MARKER, label=name)
    this_plt.theme(PLOTEXT_THEME)
    this_plt.xlabel(plot.x)
    this_plt.ylabel(plot.y)
    this_plt.ylim(0)
    if plot.x_log:
        this_plt.xscale("log")
    if plot.y_log:
        this_plt.yscale("log")
    this_plt.title(plot.title)


def draw_bar_chart(
    this_plt: Any,
    plot: BarChartModel,
    metrics: list[tuple[RunConfiguration, dict[str, str | UFloat]]],
) -> None:
    """Draw a line plot from data using the provided plotext backend."""
    data = get_bar_chart_data(plot, metrics)

    this_plt.clear_figure()
    this_plt.bar(
        data.keys(),
        [metric for metric, _, _ in data.values()],
        orientation="horizontal",
        width=3 / 5,
    )
    this_plt.theme(PLOTEXT_THEME)
    this_plt.ylabel(plot.y)
    this_plt.title(plot.title)
    if plot.y_log:
        this_plt.yscale("log")


def draw_roofline_plot(
    this_plt: Any,
    plot: RooflinePlotModel,
    metrics: list[tuple[RunConfiguration, dict[str, str | UFloat]]],
) -> None:
    """Draw a roofline plot from data using the provided plotext backend."""
    (roofline, data) = get_roofline_plot_data(plot, metrics)

    this_plt.clear_figure()
    for label, (x, y) in roofline.memory_bound_ceilings.items():
        this_plt.plot(x, y, label=label, marker=PLOTEXT_MARKER)
    for label, (x, y) in roofline.compute_bound_ceilings.items():
        this_plt.plot(x, y, label=label, marker=PLOTEXT_MARKER)
    for name, (x_point, y_point, x_err, y_err) in data.items():
        this_plt.error(
            [x_point],
            [y_point],
            xerr=[x_err / 2] * 2 if x_err is not None else None,
            yerr=[y_err / 2] * 2 if y_err is not None else None,
            label=name,
        )
    this_plt.theme(PLOTEXT_THEME)
    this_plt.xlabel("FLOPs/Byte")
    this_plt.ylabel("GFLOPs/sec")
    this_plt.xscale("log")
    this_plt.yscale("log")
    this_plt.title(plot.title)
