#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A set of objects modelling the schema for the ERT roofline JSON file."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict
from typing_extensions import Self


class MetricsModel(BaseModel):
    """The data schema for metrics in the ERT JSON schema."""

    data: list[tuple[str, float]]
    metadata: dict[str, Any]


class EmpiricalModel(BaseModel):
    """The data schema for the empirical key in the ERT JSON schema."""

    metadata: dict[str, Any]
    gflops: MetricsModel
    gbytes: MetricsModel


class ErtJsonModel(BaseModel):
    """The data schema for the ERT JSON schema."""

    model_config = ConfigDict(strict=True)

    empirical: EmpiricalModel
    spec: dict[str, Any]


@dataclass
class RooflineDataModel:
    """The extracted relevant data from the ERT JSON schema."""

    gflops_per_sec: dict[str, float]
    gbytes_per_sec: dict[str, float]

    @classmethod
    def from_json(cls, ert_json: Path) -> Self:
        """Extract the relevant roofline data from an ERT JSON file."""
        json_data = ert_json.read_text("utf-8")
        parsed_data = ErtJsonModel.model_validate_json(json_data)
        return cls(
            gflops_per_sec=dict(parsed_data.empirical.gflops.data),
            gbytes_per_sec=dict(parsed_data.empirical.gbytes.data),
        )

    @property
    def memory_bound_ceilings(self) -> dict[str, list[tuple[float, float]]]:
        """Get a labelled set of memory bound ceiling lines."""
        memory_bound_ceilings: dict[str, list[tuple[float, float]]] = {}
        for ceiling_name, m in self.gbytes_per_sec.items():
            data_series: list[tuple[float, float]] = []
            y_values = [1, *list(self.gflops_per_sec.values())]
            for y in y_values:
                x = y / m
                data_series.append((x, y))
            ceiling_label = f"{ceiling_name} = {m} GB/s"
            memory_bound_ceilings[ceiling_label] = data_series
        return memory_bound_ceilings

    @property
    def compute_bound_ceilings(self) -> dict[str, list[tuple[float, float]]]:
        """."""
        compute_bound_ceilings: dict[str, list[tuple[float, float]]] = {}
        for ceiling_name, y in self.gflops_per_sec.items():
            x_min_ceiling = y / max(self.gbytes_per_sec.values())
            x_max_ceiling = y / min(self.gbytes_per_sec.values())
            data_series: list[tuple[float, float]] = [
                (x_min_ceiling, y),
                (x_max_ceiling * 20, y),
            ]
            ceiling_label = f"{y} {ceiling_name}"
            compute_bound_ceilings[ceiling_label] = data_series
        return compute_bound_ceilings
