#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A set of objects modelling the schema for the ERT roofline JSON file."""

from dataclasses import dataclass
from typing_extensions import Self
from typing import Any
from pathlib import Path

from pydantic import BaseModel, ConfigDict


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

    gflops_per_sec: dict[str, float]
    flops_per_byte: dict[str, float]

    @classmethod
    def from_json(cls, ert_json: Path) -> Self:
        """Extract the relevant roofline data from an ERT JSON file."""
        json_data = ert_json.read_text("utf-8")
        parsed_data = ErtJsonModel.model_validate_json(json_data)
        return cls(
            gflops_per_sec={
                key: value for (key, value) in parsed_data.empirical.gflops.data
            },
            flops_per_byte={
                key: value for (key, value) in parsed_data.empirical.gbytes.data
            },
        )
