### Variables ###
# https://clarkgrubb.com/makefile-style-guide
MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.DEFAULT_GOAL := install

### Installation ###
.PHONY: install
install:
	@echo "Initialising project:"
	@poetry install
	@poetry run pre-commit install

### Static analysis ###
.PHONY: check
check: .venv/
	@echo "Running pre-commit hooks:"
	@poetry run pre-commit run --all-files
