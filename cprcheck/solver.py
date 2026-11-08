"""Finite-volume reference solver for 2D steady heat conduction.

Problem: -div(k grad T) = q on a square die of side L, discretized on an n x n
cell-centered grid, with the die edges held at ambient temperature (an idealized
peripheral heat sink). Temperatures are returned as the rise above ambient, in K.

Face conductivities use the harmonic mean of the two neighbouring cells, which is
the standard choice for discontinuous k and makes the scheme exactly conservative:
for the discrete solution, the heat leaving through the boundary equals the heat
generated, to round-off.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla


@dataclass(frozen=True)
class HeatProblem:
    """One steady conduction problem.

    q: volumetric heat generation per cell, W/m^3, shape (n, n)
    k: thermal conductivity per cell, W/(m K), shape (n, n)
    L: side length of the die, m
    """

    q: np.ndarray
    k: np.ndarray
    L: float = 0.01

    @property
    def n(self) -> int:
        return self.q.shape[0]

    @property
    def h(self) -> float:
        return self.L / self.n


def _face_conductances(k: np.ndarray):
    """Return conductance (W/K per unit depth) for interior x/y faces and boundary faces.

    On a uniform grid the face area per unit depth equals h and the centre distance
    equals h, so interior conductance is just the harmonic-mean k. A boundary face
    sits h/2 from the cell centre, so its conductance is 2k.
    """
    kx = 2.0 * k[:, :-1] * k[:, 1:] / (k[:, :-1] + k[:, 1:])  # between (i,j) and (i,j+1)
    ky = 2.0 * k[:-1, :] * k[1:, :] / (k[:-1, :] + k[1:, :])  # between (i,j) and (i+1,j)
    gb = np.zeros_like(k)
    gb[0, :] += 2.0 * k[0, :]
    gb[-1, :] += 2.0 * k[-1, :]
    gb[:, 0] += 2.0 * k[:, 0]
    gb[:, -1] += 2.0 * k[:, -1]
    return kx, ky, gb


def assemble(k: np.ndarray) -> sp.csr_matrix:
    """Assemble the conductance matrix A so that A @ T = q * h^2 (per unit depth)."""
    n = k.shape[0]
    kx, ky, gb = _face_conductances(k)
    idx = np.arange(n * n).reshape(n, n)
    diag = gb.copy()
    rows, cols, vals = [], [], []
    # x faces
    a, b = idx[:, :-1].ravel(), idx[:, 1:].ravel()
    g = kx.ravel()
    rows += [a, b]
    cols += [b, a]
    vals += [-g, -g]
    diag[:, :-1] += kx
    diag[:, 1:] += kx
    # y faces
    a, b = idx[:-1, :].ravel(), idx[1:, :].ravel()
    g = ky.ravel()
    rows += [a, b]
    cols += [b, a]
    vals += [-g, -g]
    diag[:-1, :] += ky
    diag[1:, :] += ky
    rows.append(idx.ravel())
    cols.append(idx.ravel())
    vals.append(diag.ravel())
    A = sp.coo_matrix(
        (np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(n * n, n * n)
    )
    return A.tocsr()


def solve(p: HeatProblem) -> np.ndarray:
    """Temperature rise above ambient (K), shape (n, n)."""
    A = assemble(p.k)
    rhs = (p.q * p.h**2).ravel()
    T = spla.spsolve(A.tocsc(), rhs)
    return T.reshape(p.n, p.n)


def generated_power(p: HeatProblem) -> float:
    """Total heat generated, W per metre of depth."""
    return float(np.sum(p.q) * p.h**2)


def boundary_outflow(p: HeatProblem, T: np.ndarray) -> float:
    """Heat leaving through the die edges for temperature field T, W per metre of depth."""
    _, _, gb = _face_conductances(p.k)
    return float(np.sum(gb * T))


def energy_balance(p: HeatProblem, T: np.ndarray) -> float:
    """Relative global energy imbalance |out - generated| / generated (0 for an exact solve)."""
    P = generated_power(p)
    return abs(boundary_outflow(p, T) - P) / P


def local_residual(p: HeatProblem, T: np.ndarray) -> float:
    """Relative L2 norm of the per-cell heat imbalance ||A T - q h^2|| / ||q h^2||."""
    A = assemble(p.k)
    rhs = (p.q * p.h**2).ravel()
    r = A @ T.ravel() - rhs
    return float(np.linalg.norm(r) / np.linalg.norm(rhs))
