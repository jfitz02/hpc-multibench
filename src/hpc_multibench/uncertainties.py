#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# mypy: disable-error-code="no-any-unimported"
"""Export a set of functions for representing values with uncertainties."""

from uncertainties import ufloat
from uncertainties.core import UFloat

if __name__ == "__main__":
    value: UFloat = ufloat(5.0, 0.1)
    print(value)
