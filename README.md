# HPC Multibench

> A Swiss army knife for comparing programs on HPC resources.

`hpc-multibench` is a Python tool to run, aggregate, and analyse metrics about
HPC batch compute jobs via Slurm from a convenient YAML format.

## Example usage

The following sections describe how to use the HPC MultiBench tool from the
command line.

### Installation

To install the tool, clone and navigate to the repository, then use poetry to
create a virtual environment as follows:

```bash
git clone https://github.com/EdmundGoodman/hpc-multibench
cd hpc-multibench
poetry install --without docs,test,dev
```

### Interactively reviewing sample results

Using the `parallelism` test plan in the `hpccg-rs-kudu-results` submodule as
an example, we can interactively view the data as follows:

```bash
poetry run hpc-multibench \
    -y generated_results/hpccg-rs-kudu-results/_test_plans/parallelism.yaml \
    -o generated_results/hpccg-rs-kudu-results/ \
    interactive
```

This will open a terminal-user interface allowing interactive visualisation of
results. This is rendered inside the terminal, and as such does not require
X-forwarding to be set up to present data and plot graphs.

We can see the required `-y` flag being used to select the YAML file for the
test plan, and the option `-o` flag to point to the directory containing the
sample data. The `interactive` subcommand then runs the program in interactice
mode.

### Dispatching runs

On a system with Slurm installed, runs can be dispatched as follows:

```bash
poetry run hpc-multibench \
    -y generated_results/hpccg-rs-kudu-results/_test_plans/parallelism.yaml \
    record
```

Since the `-o` flag is not specified here, it will default to writing out the
files to a directory called `results/` at the root of the repository.

### Reviewing runs non-interactively

Run results can also be viewed non-interactively as follows:

```bash
poetry run hpc-multibench \
    -y generated_results/hpccg-rs-kudu-results/_test_plans/parallelism.yaml \
    -o generated_results/hpccg-rs-kudu-results/ \
    report
```

This will open a sequence of matplotlib windows and write out any export data
as specified within the YAML file.

## System requirements

Due to the libraries for parsing the YAML schema, a Python installation of
version greater than 3.10 is required.

Since this tool uses Slurm to dispatch, the system must have Slurm installed
in order to use the `record` functionality to dispatch runs. However, it can
be used on systems without Slurm to view and analyse existing run files, using
the `report` functionality.
