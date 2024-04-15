---
hide:
  - navigation
---

# HPC Multibench

> A Swiss army knife for comparing programs on HPC resources.

`hpc-multibench` is a Python tool to run, aggregate, and analyse metrics about
HPC batch compute jobs via Slurm from a convenient YAML format.

## Killer features

- [x] Define experiments from a convenient YAML file
- [x] Support for zero effort re-runs of experiments, with aggregation for
      uncertainty calculations and error bars
- [x] Simple metric extraction and graph plotting from run results, including
      line, bar and roofline plots
- [x] Rendered entirely in the terminal -- including graph plotting capabilities;
      no need to set up X-forwarding!

## System requirements

Due to the libraries for parsing the YAML schema, Python >=3.10 is required.

Since this tool uses Slurm to dispatch, the system must have Slurm installed
in order to use the `record` functionality to dispatch runs. However, it can
be used on systems without Slurm to view and analyse existing run files, using
the `report` functionality.
