#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A set of functions to analyse the results of a test bench run."""

from enum import Enum, auto
from typing import cast

from hpc_multibench.roofline_model import RooflineDataModel
from hpc_multibench.run_configuration import RunConfiguration
from hpc_multibench.uncertainties import UFloat
from hpc_multibench.yaml_model import BarChartModel, LinePlotModel, RooflinePlotModel


class PlotStyle(Enum):
    """An enum for the styles of the plot backend."""

    SEABORN = auto()
    MATPLOTLIB = auto()
    PLOTEXT = auto()


PLOT_STYLE = PlotStyle.SEABORN
PLOTEXT_MARKER = "braille"
PLOTEXT_THEME = "pro"

if PLOT_STYLE == PlotStyle.PLOTEXT:
    import plotext as plt
else:
    import matplotlib.pyplot as plt

    # from labellines import labelLines

    if PLOT_STYLE == PlotStyle.SEABORN:
        import seaborn as sns

        sns.set_theme()


def split_metric_uncertainty(
    metrics: dict[str, str | UFloat], metric: str
) -> tuple[float, float | None]:
    """Get the uncertainty and value from a possible uncertain metric."""
    value = metrics[metric]
    if isinstance(value, UFloat):
        return (value.nominal_value, value.std_dev)
    # TODO: Add error message explaining which metric key can't be cast
    return (float(value), None)


def get_line_plot_data(
    plot: LinePlotModel,
    all_metrics: list[tuple[RunConfiguration, dict[str, str | UFloat]]],
) -> dict[str, tuple[list[float], list[float], list[float] | None, list[float] | None]]:
    """Get the data needed to plot a specified line plot for a set of runs."""
    # Reshape the metrics data from multiple runs into groups of points
    data: dict[str, list[tuple[float, float, float | None, float | None]]] = {}
    for run_configuration, metrics in all_metrics:
        split_names: list[str] = [
            f"{split_metric}={metrics[split_metric]}"
            for split_metric in plot.split_metrics
            if split_metric not in plot.fix_metrics
        ]
        fix_names: list[str] = [
            f"{metric}={value}" for metric, value in plot.fix_metrics.items()
        ]
        series_name = ", ".join([run_configuration.name, *fix_names, *split_names])

        if any(
            metrics[metric] != str(value) for metric, value in plot.fix_metrics.items()
        ):
            continue

        (x_value, x_err) = split_metric_uncertainty(metrics, plot.x)
        (y_value, y_err) = split_metric_uncertainty(metrics, plot.y)
        if series_name not in data:
            data[series_name] = []
        data[series_name].append((x_value, y_value, x_err, y_err))

    # Further reshape the data into convenient data series
    reshaped_data: dict[
        str, tuple[list[float], list[float], list[float] | None, list[float] | None]
    ] = {}
    for name, results in data.items():
        x, y, x_err, y_err = cast(  # type: ignore[assignment]
            tuple[list[float], list[float], list[float | None], list[float | None]],
            zip(*sorted(results), strict=True),
        )
        reshaped_data[name] = (  # type: ignore[assignment]
            x,
            y,
            x_err if any(x_err) else None,  # type: ignore[arg-type]
            y_err if any(y_err) else None,  # type: ignore[arg-type]
        )
    return reshaped_data


def draw_line_plot(
    plot: LinePlotModel,
    metrics: list[tuple[RunConfiguration, dict[str, str | UFloat]]],
) -> None:
    """Draw a specified line plot for a set of run outputs."""
    data = get_line_plot_data(plot, metrics)

    if PLOT_STYLE == PlotStyle.PLOTEXT:
        plt.clear_figure()
        for name, (x, y, _x_err, _y_err) in data.items():
            plt.plot(x, y, marker=PLOTEXT_MARKER, label=name)
            # plt.error(
            #     x,
            #     y,
            #     xerr=_x_err,
            #     yerr=_y_err,
            # )
        plt.theme(PLOTEXT_THEME)
    else:
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
    plt.show()


def get_bar_chart_data(
    plot: BarChartModel,
    all_metrics: list[tuple[RunConfiguration, dict[str, str | UFloat]]],
) -> dict[str, tuple[float, float | None, int]]:
    """Get the data needed to plot a specified bar chart for a set of runs."""
    data: dict[str, tuple[float, float | None, int]] = {}

    # Extract the outputs into the data format needed for the line plot
    hue_index_lookup: dict[str, int] = {}
    new_hue_index = 0
    for run_configuration, metrics in all_metrics:
        split_names: list[str] = [
            f"{split_metric}={metrics[split_metric]}"
            for split_metric in plot.split_metrics
            if split_metric not in plot.fix_metrics
        ]
        fix_names: list[str] = [
            f"{metric}={value}" for metric, value in plot.fix_metrics.items()
        ]
        series_name = ", ".join([run_configuration.name, *fix_names, *split_names])
        if any(
            metrics[metric] != str(value) for metric, value in plot.fix_metrics.items()
        ):
            continue

        if run_configuration.name not in hue_index_lookup:
            hue_index_lookup[run_configuration.name] = new_hue_index
            new_hue_index += 1

        (y_value, y_err) = split_metric_uncertainty(metrics, plot.y)
        data[series_name] = (
            y_value,
            y_err,
            hue_index_lookup[run_configuration.name],
        )
    return data


def draw_bar_chart(
    plot: BarChartModel,
    metrics: list[tuple[RunConfiguration, dict[str, str | UFloat]]],
) -> None:
    """Draw a specified bar chart for a set of run outputs."""
    data = get_bar_chart_data(plot, metrics)

    if PLOT_STYLE == PlotStyle.PLOTEXT:
        plt.clear_figure()
        # NOTE: Plotext cannot render error bars!
        plt.bar(
            data.keys(),
            [metric for metric, _, _ in data.values()],
            orientation="horizontal",
            width=3 / 5,
        )
        plt.ylabel(plot.y)
        plt.theme(PLOTEXT_THEME)
    else:
        palette = (
            sns.color_palette()
            if PLOT_STYLE == PlotStyle.SEABORN
            else plt.rcParams["axes.prop_cycle"].by_key()["color"]
        )
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


def get_roofline_plot_data(
    plot: RooflinePlotModel,
    all_metrics: list[tuple[RunConfiguration, dict[str, str | UFloat]]],
) -> tuple[
    RooflineDataModel, dict[str, tuple[float, float, float | None, float | None]]
]:
    """Get the data needed to plot a specified roofline plot."""
    roofline_data = RooflineDataModel.from_json(plot.ert_json)

    data: dict[str, tuple[float, float, float | None, float | None]] = {}
    for run_configuration, metrics in all_metrics:
        (x_value, x_err) = split_metric_uncertainty(metrics, plot.flops_per_byte)
        (y_value, y_err) = split_metric_uncertainty(metrics, plot.gflops_per_sec)
        data[run_configuration.name] = (x_value, y_value, x_err, y_err)

    return (roofline_data, data)


def draw_roofline_plot(
    plot: RooflinePlotModel,
    metrics: list[tuple[RunConfiguration, dict[str, str | UFloat]]],
) -> None:
    """Draw a specified roofline plots for a set of run outputs."""
    (roofline, data) = get_roofline_plot_data(plot, metrics)

    if PLOT_STYLE == PlotStyle.PLOTEXT:
        plt.clear_figure()
        for label, (x, y) in roofline.memory_bound_ceilings.items():
            plt.plot(x, y, label=label, marker=PLOTEXT_MARKER)
        for label, (x, y) in roofline.compute_bound_ceilings.items():
            plt.plot(x, y, label=label, marker=PLOTEXT_MARKER)
        for name, (x_point, y_point, x_err, y_err) in data.items():
            plt.error(
                [x_point],
                [y_point],
                xerr=[x_err / 2] * 2 if x_err is not None else None,
                yerr=[y_err / 2] * 2 if y_err is not None else None,
                label=name,
            )
        plt.theme(PLOTEXT_THEME)
    else:
        for label, (x, y) in roofline.memory_bound_ceilings.items():
            plt.plot(x, y, label=label)
        for label, (x, y) in roofline.compute_bound_ceilings.items():
            plt.plot(x, y, label=label)
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
