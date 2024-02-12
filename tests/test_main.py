#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for the main methods."""

import pytest

from hpc_multibench.main import main


@pytest.mark.integration()
def test_main() -> None:
    """Test the main method."""
    main()
    assert True
