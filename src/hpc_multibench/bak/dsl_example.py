#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manually construct run configurations via the Python DSL interface.

```python
from hpc_multibench.configuration import RunConfiguration

def get_cpp_reference_impl() -> RunConfiguration:
    '''Build a run configuration for the reference implementation.'''
    run = RunConfiguration("./test_HPCCG")
    run.build_commands = ["make -j 8"]
    run.sbatch_config = {
        "nodes": "1",
        "ntasks-per-node": "1",
        "cpus-per-task": "1",
        "mem-per-cpu": "3700",  # max on avon?
    }
    run.module_loads = ["GCC/11.3.0"]
    run.directory = Path("../0_cpp_versions/0_ref")
    return run
```
"""
