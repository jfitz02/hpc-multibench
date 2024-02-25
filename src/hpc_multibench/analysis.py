#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A set of functions to analyse the results of a test bench run."""

import matplotlib.pyplot as plt


def line_plot(
    data: dict[str, list[tuple[float, float]]], x_label: str, y_label: str
) -> None:
    """Draw a line plot of a data series."""
    for name, result in data.items():
        print(name, result)
        plt.plot(*zip(*result, strict=True), marker="x", label=name)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title("Benchmark analysis")
    plt.legend()
    plt.show()
