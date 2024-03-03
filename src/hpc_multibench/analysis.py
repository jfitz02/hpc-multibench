#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A set of functions to analyse the results of a test bench run."""

from enum import Enum, auto

from hpc_multibench.roofline_model import RooflineDataModel
from hpc_multibench.run_configuration import RunConfiguration
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
        import pandas as pd
        import seaborn as sns

        sns.set_theme()


def get_line_plot_data(
    plot: LinePlotModel,
    run_metrics: list[tuple[RunConfiguration, dict[str, str | float]]],
    run_uncertainties: list[tuple[RunConfiguration, dict[str, float | None]]],
) -> dict[str, tuple[list[float], list[float], list[float] | None, list[float] | None]]:
    """Get the data needed to plot a specified line plot for a set of runs."""
    # Reshape the metrics data from multiple runs into groups of points
    data: dict[str, list[tuple[float, float, float | None, float | None]]] = {}
    for (run_configuration, metrics), (_, uncertainties) in zip(
        run_metrics, run_uncertainties, strict=True
    ):
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

        if series_name not in data:
            data[series_name] = []
        data[series_name].append(
            (
                float(metrics[plot.x]),
                float(metrics[plot.y]),
                uncertainties[plot.x],
                uncertainties[plot.y],
            )
        )

    # Further reshape the data into convenient data series
    reshaped_data: dict[
        str, tuple[list[float], list[float], list[float] | None, list[float] | None]
    ] = {}
    for name, results in data.items():
        x, y, x_err, y_err = zip(*sorted(results), strict=True)
        reshaped_data[name] = (  # type: ignore[assignment]
            x,
            y,
            x_err if any(x_err) else None,
            y_err if any(y_err) else None,
        )
    return reshaped_data


def draw_line_plot(
    plot: LinePlotModel,
    run_metrics: list[tuple[RunConfiguration, dict[str, str | float]]],
    run_uncertainties: list[tuple[RunConfiguration, dict[str, float | None]]],
) -> None:
    """Draw a specified line plot for a set of run outputs."""
    data = get_line_plot_data(plot, run_metrics, run_uncertainties)

    if PLOT_STYLE == PlotStyle.PLOTEXT:
        plt.clear_figure()
        # NOTE: Plotext cannot render error bars!
        for name, (x, y, _, _) in data.items():
            plt.plot(x, y, marker=PLOTEXT_MARKER, label=name)
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
    run_metrics: list[tuple[RunConfiguration, dict[str, str | float]]],
) -> dict[tuple[str, ...], float]:
    """Get the data needed to plot a specified bar chart for a set of runs."""
    data: dict[tuple[str, ...], float] = {}  # {("a", "b"): 1.0, ("a", "c"): 2.0}

    # Extract the outputs into the data format needed for the line plot
    for run_configuration, metrics in run_metrics:
        split_names: list[str] = [
            f"{split_metric}={metrics[split_metric]}"
            for split_metric in plot.split_metrics
            if split_metric not in plot.fix_metrics
        ]
        fix_names: list[str] = [
            f"{metric}={value}" for metric, value in plot.fix_metrics.items()
        ]
        series_name = (run_configuration.name, *fix_names, *split_names)
        if any(
            metrics[metric] != str(value) for metric, value in plot.fix_metrics.items()
        ):
            continue

        data[series_name] = float(metrics[plot.y])
    return data


def draw_bar_chart(
    plot: BarChartModel,
    run_metrics: list[tuple[RunConfiguration, dict[str, str | float]]],
) -> None:
    """Draw a specified bar chart for a set of run outputs."""
    data = get_bar_chart_data(plot, run_metrics)

    if PLOT_STYLE == PlotStyle.SEABORN:
        dataframe = pd.DataFrame(
            {
                "Run Configuration": [",\n".join(key) for key in data],
                plot.y: list(data.values()),
                "Run Type": [key[0] for key in data],
            }
        )
        sns.barplot(
            data=dataframe.sort_values(plot.y),
            x="Run Configuration",
            y=plot.y,
            hue="Run Type",
        )
        plt.xticks(rotation=45, ha="right")
        plt.gcf().subplots_adjust(bottom=0.25)
    elif PLOT_STYLE == PlotStyle.PLOTEXT:
        plt.clear_figure()
        shaped_data: list[tuple[str, float]] = sorted(
            [(", ".join(name), metric) for name, metric in data.items()],
            key=lambda x: x[1],
        )
        plt.bar(*zip(*shaped_data, strict=True), orientation="horizontal", width=3 / 5)
        plt.ylabel(plot.y)
        plt.theme(PLOTEXT_THEME)
    else:
        newline_shaped_data: list[tuple[str, float]] = sorted(
            [(",\n".join(name), metric) for name, metric in data.items()],
            key=lambda x: x[1],
        )
        plt.bar(*zip(*newline_shaped_data, strict=True))
        plt.ylabel(plot.y)
        plt.xticks(rotation=45, ha="right")
        plt.gcf().subplots_adjust(bottom=0.25)

    plt.title(plot.title)
    plt.show()


def get_roofline_plot_data(
    plot: RooflinePlotModel,
    _run_metrics: list[tuple[RunConfiguration, dict[str, str | float]]],
) -> tuple[RooflineDataModel, dict[str, tuple[float, float]]]:
    """Get the data needed to plot a specified roofline plot."""
    roofline_data = RooflineDataModel.from_json(plot.ert_json)
    return (roofline_data, {})


def draw_roofline_plot(
    plot: RooflinePlotModel,
    run_metrics: list[tuple[RunConfiguration, dict[str, str | float]]],
) -> None:
    """Draw a specified roofline plots for a set of run outputs."""
    data = get_roofline_plot_data(plot, run_metrics)

    if PLOT_STYLE == PlotStyle.PLOTEXT:
        plt.clear_figure()
        for label, memory_bound_data in data[0].memory_bound_ceilings.items():
            plt.plot(
                *zip(*memory_bound_data, strict=True),
                label=label,
                marker=PLOTEXT_MARKER,
            )
        for label, compute_bound_data in data[0].compute_bound_ceilings.items():
            plt.plot(
                *zip(*compute_bound_data, strict=True),
                label=label,
                marker=PLOTEXT_MARKER,
            )
        plt.theme(PLOTEXT_THEME)
    else:
        for label, memory_bound_data in data[0].memory_bound_ceilings.items():
            plt.plot(*zip(*memory_bound_data, strict=True), label=label)
        for label, compute_bound_data in data[0].compute_bound_ceilings.items():
            plt.plot(*zip(*compute_bound_data, strict=True), label=label)
        plt.legend()
        # for ax in plt.gcf().axes:
        #     labelLines(ax.get_lines())

    plt.xlabel("FLOPs/Byte")
    plt.ylabel("GFLOPs/sec")
    plt.xscale("log")
    plt.yscale("log")
    plt.title(plot.title)
    plt.show()
