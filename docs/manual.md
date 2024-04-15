---
hide:
  - navigation
---

# Manual

When the `hpc-multibench` tool and its subcommands are invoked with the `-h` or
`--help` flags, the following help pages are displayed.

## Top-level help page

```
usage: __main__.py [-h] -y YAML_PATH [-o OUTPUTS_DIRECTORY] {record,interactive,report} ...

A Swiss army knife for comparing programs on HPC resources.

positional arguments:
  {record,interactive,report}
    record              record data from running the test benches
    interactive         show the interactive TUI
    report              report analysis about completed test bench runs

options:
  -h, --help            show this help message and exit
  -y YAML_PATH, --yaml-path YAML_PATH
                        the path to the configuration YAML file
  -o OUTPUTS_DIRECTORY, --outputs-directory OUTPUTS_DIRECTORY
                        the path to the configuration YAML file
```

## `record` subcommand help page

```
usage: __main__.py record [-h] [-d] [-w] [-nc]

options:
  -h, --help         show this help message and exit
  -d, --dry-run      print but don't submit the generated sbatch files
  -w, --wait         wait for the submitted jobs to finish to exit
  -nc, --no-clobber  don't delete any previous run results of the test benches
```

## `report` subcommand help page

```
usage: __main__.py report [-h]

options:
  -h, --help  show this help message and exit
```

## `interactive` subcommand help page

```
usage: __main__.py interactive [-h] [-nc]

options:
  -h, --help         show this help message and exit
  -nc, --no-clobber  don't delete any previous run results of the test benches
```
