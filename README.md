# HPC Multibench

> A Swiss army knife for comparing programs on HPC resources.

`hpc-multibench` is a Python tool to run, aggregate, and analyse metrics about
HPC batch compute jobs via Slurm from a convenient YAML format.

## Example usage

The following sections describe how to use the HPC MultiBench tool from the
command line.

### Interactively reviewing sample results

First, populate the `results/` directory with the run outputs to review. For
example for the `parallelism` test plan in the `hpccg-rs-kudu-results` submodule:

```bash
rm -rf results && mkdir results/
rsync -av generated_results/hpccg-rs-kudu-results/ results/ --exclude=.git/
poetry run python3 -m hpc_multibench -y results/_test_plans/parallelism.yaml interactive
```

This will open a terminal-user interface allowing interactive visualisation of
results. This is rendered inside the terminal, and as such does not require
X-forwarding to be set up to present data and plot graphs.

### Dispatching runs

```bash
```

### Reviewing runs non-interactively

```bash
```

## System requirements

Due to the libraries for parsing the YAML schema, Python >=3.10 is required.

Since this tool uses Slurm to dispatch, the system must have Slurm installed
in order to use the `record` functionality to dispatch runs. However, it can
be used on systems without Slurm to view and analyse existing run files, using
the `report` functionality.
