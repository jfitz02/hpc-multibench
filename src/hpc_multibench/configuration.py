#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A class for test configurations on batch compute."""

from getpass import getuser
from pathlib import Path
from re import search as re_search
from subprocess import PIPE  # nosec
from subprocess import run as subprocess_run  # nosec
from tempfile import NamedTemporaryFile
from time import sleep
from typing import Any

BASH_SHEBANG = "#!/bin/sh\n"
JOB_ID_REGEX = r"Submitted batch job (\d+)"


class RunConfiguration:
    """A builder/runner for a run configuration."""

    def __init__(self, name: str, run_command: str, output_file: Path):
        """Initialise the run configuration file as a empty bash file."""
        # TODO: Are name and output file both needed?
        self.name: str = name
        self.output_file: Path = output_file
        self.sbatch_config: dict[str, str] = {}
        self.module_loads: list[str] = []
        self.environment_variables: dict[str, str] = {}
        self.directory: Path | None = None
        self.build_commands: list[str] = []
        self.run_command: str = run_command
        self.args: str | None = None

    @property
    def sbatch_contents(self) -> str:
        """Construct the sbatch configuration for the run."""
        sbatch_file = BASH_SHEBANG

        for key, value in self.sbatch_config.items():
            sbatch_file += f"#SBATCH --{key}={value}\n"
        sbatch_file += f"#SBATCH --output={self.output_file}\n"
        if "output" in self.sbatch_config:
            # NOTE: The output file will always override this key!
            # This should probably be a logging statement...
            print("WARNING: Output file configuration overriden!")

        if len(self.module_loads) > 0:
            sbatch_file += "module purge\n"
            sbatch_file += f"module load {' '.join(self.module_loads)}\n"

        for key, value in self.environment_variables.items():
            sbatch_file += f"export {key}={value}\n"

        sbatch_file += "\necho '===== ENVIRONMENT ====='\n"
        sbatch_file += "echo '=== CPU ARCHITECTURE ==='\n"
        sbatch_file += "lscpu\n"
        sbatch_file += "echo '=== HOSTNAME ==='\n"
        sbatch_file += "hostname\n"
        sbatch_file += "echo '=== SLURM CONFIG ==='\n"
        sbatch_file += "scontrol show job $SLURM_JOB_ID\n"
        sbatch_file += "echo\n"

        sbatch_file += "\necho '===== BUILD ====='\n"
        if self.directory is not None:
            sbatch_file += f"cd {self.directory}\n"
        sbatch_file += "\n".join(self.build_commands) + "\n"

        sbatch_file += f"\necho '===== RUN {self.name} ====='\n"
        sbatch_file += f"time {self.run_command} {self.args}\n"

        return sbatch_file

    def __repr__(self) -> str:
        """Get the sbatch configuration file defining the run."""
        return self.sbatch_contents

    def run(self) -> int | None:
        """Run the specified run configuration."""
        # Ensure the output directory exists before it is used
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        # Create and run the temporary sbatch file
        with NamedTemporaryFile(
            prefix=self.name, suffix=".sbatch", dir=Path("./"), mode="w+"
        ) as sbatch_tmp:
            sbatch_tmp.write(self.sbatch_contents)
            sbatch_tmp.flush()
            result = subprocess_run(  # nosec
                ["sbatch", Path(sbatch_tmp.name)],  # noqa: S603, S607
                check=True,
                stdout=PIPE,
            )
            job_id_search = re_search(JOB_ID_REGEX, result.stdout.decode("utf-8"))
            if job_id_search is None:
                return None
            return int(job_id_search.group(1))

    @classmethod
    def get_output_file_name(
        cls, run_configuration_name: str, variables: dict[str, Any]
    ) -> str:
        """Construct an output file name for a run."""
        # TODO: Better representation of sbatch etc than stringifying
        variables_str = ",".join(
            f"{name}={str(value).replace('/','').replace(' ','_')}"
            for name, value in variables.items()
        )
        return f"{run_configuration_name}__{variables_str}__%j.out"


def wait_till_queue_empty(
    max_time_to_wait: int = 172_800, backoff: list[int] | None = None
) -> bool:
    """Wait until the Slurm queue is empty for the current user."""
    if backoff is None or len(backoff) < 1:
        backoff = [5, 10, 15, 30, 60]

    time_waited = 0
    backoff_index = 0
    print("Starting to wait for Slurm queue")
    while time_waited < max_time_to_wait:
        wait_time = backoff[backoff_index]
        sleep(wait_time)
        print(f"Waited {time_waited}s for Slurm queue to empty")
        time_waited += wait_time

        result = subprocess_run(  # nosec
            ["squeue", "-u", getuser()],  # noqa: S603, S607
            check=True,
            stdout=PIPE,
        )
        if result.stdout.decode("utf-8").count("\n") <= 1:
            return True

        if backoff_index < len(backoff) - 1:
            backoff_index += 1

    return False
