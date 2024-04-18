#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A set of functions to get the data series to plot for test run results."""

from typing import cast

from hpc_multibench.roofline_model import RooflineDataModel
from hpc_multibench.run_configuration import RunConfiguration
from hpc_multibench.uncertainties import UFloat
from hpc_multibench.yaml_model import BarChartModel, LinePlotModel, RooflinePlotModel


def split_metric_uncertainty(
    metrics: dict[str, str | UFloat], metric: str
) -> tuple[float, float | None]:
    """Get the uncertainty and value from a possible uncertain metric."""
    value = metrics[metric]
    if isinstance(value, UFloat):
        return (value.nominal_value, value.std_dev)
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
        (y_value, y_err) = split_metric_uncertainty(metrics, plot.gflops_per_sec)
        (x_value_tmp, x_err_tmp) = split_metric_uncertainty(
            metrics, plot.mbytes_per_sec
        )
        x_value = y_value / (x_value_tmp / 1000)
        x_err = None if x_err_tmp is None or y_err is None else y_err + x_err_tmp
        data[run_configuration.name] = (x_value, y_value, x_err, y_err)

    return (roofline_data, data)
