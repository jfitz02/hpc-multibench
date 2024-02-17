#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for the main methods."""


import pytest


@pytest.mark.integration()
def test_always_true() -> None:
    """Test always passing."""
    assert True
