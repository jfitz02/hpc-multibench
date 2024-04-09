#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# mypy: disable-error-code="misc"
"""Unit tests for the main methods."""


import pytest


@pytest.mark.integration()
def test_always_true() -> None:
    """Test always passing."""
    assert True
