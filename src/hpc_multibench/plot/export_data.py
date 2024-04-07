#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A set of functions to export the results of a test bench run."""

import pandas as pd

from hpc_multibench.plot.plot_data import split_metric_uncertainty
from hpc_multibench.run_configuration import RunConfiguration
from hpc_multibench.uncertainties import UFloat
from hpc_multibench.yaml_model import ExportModel


def export_data(
    plot: ExportModel,
    all_metrics: list[tuple[RunConfiguration, dict[str, str | UFloat]]],
) -> None:
    """Construct and export a pandas data frame from the metrics."""
    df_data: dict[str, list[float | str]] = {}
    for run_configuration, metrics in all_metrics:
        row_data: dict[str, float | str] = {"Run configuration": run_configuration.name}

        for metric in metrics:
            value, error = split_metric_uncertainty(metrics, metric)
            row_data[metric] = value
            if error is not None:
                row_data[f"{metric} error"] = error

        for column, cell in row_data.items():
            if column not in df_data:
                df_data[column] = []
            df_data[column].append(cell)

    export_df = pd.DataFrame(df_data)

    if plot.export_path is None:
        print(export_df.to_string())
    elif plot.export_format == "csv":
        export_df.to_csv(plot.export_path)
    else:
        raise NotImplementedError(
            f"Export format '{plot.export_format}' not supported!"
        )
