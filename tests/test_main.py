#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for the main methods."""

import pytest

from pyproject_template.main import get_greeting, main


def test_get_greeting() -> None:
    """Test getting the greeting string."""
    assert get_greeting().startswith("Hello")


@pytest.mark.integration()
def test_main() -> None:
    """Test the main method."""
    main()
    assert True
