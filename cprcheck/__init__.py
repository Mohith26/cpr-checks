"""Executable checks for criteria 5.2 and 5.3 of the Continuous Physics Reasoning framework."""

from cprcheck.solver import HeatProblem, solve, energy_balance, local_residual
from cprcheck.checks import run_checks

__all__ = ["HeatProblem", "solve", "energy_balance", "local_residual", "run_checks"]
