#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A set of functions using matplotlib to plot the results of a test bench run."""

import matplotlib.pyplot as plt
import seaborn as sns

from hpc_multibench.plot.plot_data import (
    get_bar_chart_data,
    get_line_plot_data,
    get_roofline_plot_data,
)
from hpc_multibench.run_configuration import RunConfiguration
from hpc_multibench.uncertainties import UFloat
from hpc_multibench.yaml_model import BarChartModel, LinePlotModel, RooflinePlotModel

sns.set_theme()


def draw_line_plot(
    plot: LinePlotModel,
    metrics: list[tuple[RunConfiguration, dict[str, str | UFloat]]],
) -> None:
    """Draw a specified line plot for a set of run outputs."""
    data = get_line_plot_data(plot, metrics)

    for name, (x, y, x_err, y_err) in data.items():
        plt.errorbar(
            x,
            y,
            xerr=x_err,
            yerr=y_err,
            marker="x",
            ecolor="black",
            label=name,
        )
    plt.legend()
    plt.xlabel(plot.x)
    plt.ylabel(plot.y)
    plt.title(plot.title)
    plt.ylim(0)
    plt.show()


def draw_bar_chart(
    plot: BarChartModel,
    metrics: list[tuple[RunConfiguration, dict[str, str | UFloat]]],
) -> None:
    """Draw a specified bar chart for a set of run outputs."""
    data = get_bar_chart_data(plot, metrics)

    # For matplotlib `plt.rcParams["axes.prop_cycle"].by_key()["color"]`
    palette = sns.color_palette()
    plt.barh(
        list(data.keys()),
        [metric for metric, _, _ in data.values()],
        xerr=[uncertainty for _, uncertainty, _ in data.values()],
        color=[palette[hue] for _, _, hue in data.values()],
        ecolor="black",
    )
    plt.xlabel(plot.y)
    plt.gcf().subplots_adjust(left=0.25)
    plt.title(plot.title)
    plt.show()


def draw_roofline_plot(
    plot: RooflinePlotModel,
    metrics: list[tuple[RunConfiguration, dict[str, str | UFloat]]],
) -> None:
    """Draw a specified roofline plots for a set of run outputs."""
    (roofline, data) = get_roofline_plot_data(plot, metrics)

    for label, (x, y) in roofline.memory_bound_ceilings.items():
        plt.plot(x, y, label=label)
    for label, (x, y) in roofline.compute_bound_ceilings.items():
        plt.plot(x, y, label=label)
    # from labellines import labelLines
    # for ax in plt.gcf().axes:
    #     labelLines(ax.get_lines())
    for name, (x_point, y_point, x_err, y_err) in data.items():
        plt.errorbar(
            x_point,
            y_point,
            xerr=x_err,
            yerr=y_err,
            marker="o",
            ecolor="black",
            label=name,
        )
    plt.legend()
    plt.xlabel("FLOPs/Byte")
    plt.ylabel("GFLOPs/sec")
    plt.xscale("log")
    plt.yscale("log")
    plt.title(plot.title)
    plt.show()
