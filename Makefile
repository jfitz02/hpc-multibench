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

.PHONY: whitelist
whitelist:
	@echo "Creating vulture whitelist:"
	@echo "# noqa" > pyproject_template/whitelist.py
	@echo "# type: ignore" >> pyproject_template/whitelist.py
	@poetry run vulture pyproject_template tests --make-whitelist \
		>> pyproject_template/whitelist.py


### Testing ###
.PHONY: test_unit
test_unit: .venv/
	@echo "Running unit tests:"
	@poetry run coverage run -m pytest -s -m "not (integration)" &&\
 		poetry run coverage report -m

.PHONY: test_integration
test_integration: .venv/
	@echo "Running test_integration tests:"
	@poetry run coverage run -m pytest -s -m integration &&\
 		poetry run coverage report -m

.PHONY: test
test: .venv/
	@echo "Running tests:"
	@poetry run coverage run -m pytest -s &&\
 		poetry run coverage report -m

.PHONY: verify
verify: check test
