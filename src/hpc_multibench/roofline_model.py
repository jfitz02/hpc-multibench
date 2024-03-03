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
    def memory_bound_ceilings(self) -> dict[str, tuple[list[float], list[float]]]:
        """Get a labelled set of memory bound ceiling lines."""
        memory_bound_ceilings: dict[str, tuple[list[float], list[float]]] = {}
        for ceiling_name, m in self.gbytes_per_sec.items():
            y_values = [1, *list(self.gflops_per_sec.values())]
            x_values = [y / m for y in y_values]
            ceiling_label = f"{ceiling_name} = {m} GB/s"
            memory_bound_ceilings[ceiling_label] = (x_values, y_values)
        return memory_bound_ceilings

    @property
    def compute_bound_ceilings(self) -> dict[str, tuple[list[float], list[float]]]:
        """Get a labelled set of computer bound ceiling lines."""
        compute_bound_ceilings: dict[str, tuple[list[float], list[float]]] = {}
        for ceiling_name, y in self.gflops_per_sec.items():
            x_values = [
                y / max(self.gbytes_per_sec.values()),
                20 * (y / min(self.gbytes_per_sec.values())),
            ]
            y_values = [y, y]
            ceiling_label = f"{y} {ceiling_name}"
            compute_bound_ceilings[ceiling_label] = (x_values, y_values)
        return compute_bound_ceilings
