#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A class for test configurations on batch compute."""

from pathlib import Path
from re import search as re_search
from subprocess import PIPE  # nosec
from subprocess import run as subprocess_run  # nosec
from tempfile import NamedTemporaryFile
from typing import Any

SHELL_SHEBANG = "#!/bin/sh\n"
SLURM_JOB_ID_REGEX = r"Submitted batch job (\d+)"
SLURM_UNQUEUED_SUBSTRING = "Invalid job id specified"


class RunConfiguration:
    """A builder class for a test run on batch compute."""

    def __init__(self, run_command: str, output_file: Path):
        """Initialise the run configuration file as a empty bash file."""
        self.output_file: Path = output_file
        self.sbatch_config: dict[str, str] = {}
        self.module_loads: list[str] = []
        self.environment_variables: dict[str, str] = {}
        self.directory: Path | None = None
        self.build_commands: list[str] = []
        self.run_command: str = run_command
        self.args: str | None = None
        self.instantiation: Any | None = None

    @property
    def sbatch_contents(self) -> str:
        """Construct the sbatch configuration for the run."""
        sbatch_file = SHELL_SHEBANG

        for key, value in self.sbatch_config.items():
            if key == "output":
                # TODO: The output file will always override this key!
                # This should probably be a logging statement...
                print("WARNING: Output file configuration overriden!")
                continue
            sbatch_file += f"#SBATCH --{key}={value}\n"
        sbatch_file += f"#SBATCH --output={self.output_file}\n"

        if len(self.module_loads) > 0:
            sbatch_file += "module purge\n"
            sbatch_file += f"module load {' '.join(self.module_loads)}\n"

        for key, value in self.environment_variables.items():
            sbatch_file += f"export {key}={value}\n"

        sbatch_file += "\necho '===== CONFIGURATION ====='\n"
        sbatch_file += "echo '=== CPU ARCHITECTURE ==='\n"
        sbatch_file += "lscpu\n"
        sbatch_file += "echo '=== SLURM CONFIG ==='\n"
        sbatch_file += "scontrol show job $SLURM_JOB_ID\n"
        if self.instantiation is not None:
            sbatch_file += "echo '=== RUN INSTANTIATION ==='\n"
            sbatch_file += f"echo '{self.instantiation!s}'\n"
        sbatch_file += "echo\n"

        sbatch_file += "\necho '===== BUILD ====='\n"
        if self.directory is not None:
            sbatch_file += f"cd {self.directory}\n"
        sbatch_file += "\n".join(self.build_commands) + "\n"

        sbatch_file += "\necho '===== RUN ====='\n"
        sbatch_file += f"time {self.run_command} {self.args}\n"

        return sbatch_file

    def run(self) -> int | None:
        """Run the specified run configuration."""
        # Ensure the output directory exists before it is used
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        # Create and run the temporary sbatch file via slurm
        with NamedTemporaryFile(
            suffix=".sbatch", dir=Path("./"), mode="w+"
        ) as sbatch_tmp:
            sbatch_tmp.write(self.sbatch_contents)
            sbatch_tmp.flush()
            result = subprocess_run(  # nosec
                ["sbatch", Path(sbatch_tmp.name)],  # noqa: S603, S607
                check=True,
                stdout=PIPE,
            )
            job_id_search = re_search(SLURM_JOB_ID_REGEX, result.stdout.decode("utf-8"))
            if job_id_search is None:
                return None
            return int(job_id_search.group(1))

    def collect(self, slurm_id: int) -> str | None:
        """Collect the output from a completed job with a given slurm id."""
        # Check the job is completed in the queue
        result = subprocess_run(  # nosec
            ["squeue", "-j", str(slurm_id)],  # noqa: S603, S607
            check=True,
            stdout=PIPE,
        )
        if SLURM_UNQUEUED_SUBSTRING in result.stdout.decode("utf-8"):
            return None
        # Return the contents of the specified output file
        output_file = (
            self.output_file.parent / f"{self.output_file.name[:-8]}__{slurm_id}.out"
        )
        if not output_file.exists():
            return None
        return output_file.read_text(encoding="utf-8")

    def __repr__(self) -> str:
        """Get the sbatch configuration file defining the run."""
        return self.sbatch_contents
