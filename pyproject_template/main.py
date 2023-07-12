#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Docstring for an example tool."""


def get_greeting() -> str:
    """Get a string greeting."""
    return "Hello world!"


def main() -> None:  # pragma: no cover
    """Say hello."""
    print(get_greeting())
