---
hide:
  - navigation
---

# Introduction

`hpc-multibench` is a Python tool to define and run HPC batch compute jobs via Slurm from a convenient YAML format.

# Usage

```
usage: __main__.py [-h] -y YAML_PATH {record,interactive,report} ...

A tool to spawn and analyse HPC jobs.

positional arguments:
  {record,interactive,report}
    record              record data from running the test benches
    interactive         show the interactive TUI
    report              report analysis about completed test bench runs

options:
  -h, --help            show this help message and exit
  -y YAML_PATH, --yaml-path YAML_PATH
                        the path to the configuration YAML file
```

## `record` subcommand

```
usage: __main__.py record [-h] [-d] [-w] [-nc]

options:
  -h, --help         show this help message and exit
  -d, --dry-run      print but don't submit the generated sbatch files
  -w, --wait         wait for the submitted jobs to finish to exit
  -nc, --no-clobber  don't delete any previous run results of the test benches
```

## `report` subcommand

```
usage: __main__.py report [-h]

options:
  -h, --help  show this help message and exit
```

## `interactive` subcommand

```
usage: __main__.py interactive [-h] [-nc]

options:
  -h, --help         show this help message and exit
  -nc, --no-clobber  don't delete any previous run results of the test benches
```
