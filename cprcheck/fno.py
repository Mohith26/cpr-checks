"""A small 2D Fourier Neural Operator surrogate (Li et al., 2021) for the conduction problem."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import torch
from torch import nn

from cprcheck.solver import HeatProblem

Q_SCALE = 1.0e9  # W/m^3
K_REF = 150.0  # W/(m K)
T_SCALE = 20.0  # K


class SpectralConv2d(nn.Module):
    def __init__(self, width: int, modes: int):
        super().__init__()
        self.modes = modes
        scale = 1.0 / (width * width)
        self.w1 = nn.Parameter(scale * torch.randn(width, width, modes, modes, dtype=torch.cfloat))
        self.w2 = nn.Parameter(scale * torch.randn(width, width, modes, modes, dtype=torch.cfloat))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, c, h, w = x.shape
        m = self.modes
        xf = torch.fft.rfft2(x)
        out = torch.zeros(b, c, h, w // 2 + 1, dtype=torch.cfloat, device=x.device)
        out[:, :, :m, :m] = torch.einsum("bixy,ioxy->boxy", xf[:, :, :m, :m], self.w1)
        out[:, :, -m:, :m] = torch.einsum("bixy,ioxy->boxy", xf[:, :, -m:, :m], self.w2)
        return torch.fft.irfft2(out, s=(h, w))


class FNO2d(nn.Module):
    def __init__(self, width: int = 32, modes: int = 12, layers: int = 4):
        super().__init__()
        self.lift = nn.Conv2d(4, width, 1)
        self.spectral = nn.ModuleList(SpectralConv2d(width, modes) for _ in range(layers))
        self.pointwise = nn.ModuleList(nn.Conv2d(width, width, 1) for _ in range(layers))
        self.proj = nn.Sequential(nn.Conv2d(width, 128, 1), nn.GELU(), nn.Conv2d(128, 1, 1))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.lift(x)
        for i, (s, p) in enumerate(zip(self.spectral, self.pointwise)):
            x = s(x) + p(x)
            if i < len(self.spectral) - 1:
                x = nn.functional.gelu(x)
        return self.proj(x)[:, 0]


def features(problems: Sequence[HeatProblem]) -> torch.Tensor:
    n = problems[0].n
    c = (np.arange(n) + 0.5) / n
    X, Y = np.meshgrid(c, c)
    feats = [
        np.stack([p.q / Q_SCALE, np.log(p.k / K_REF), X, Y]).astype(np.float32) for p in problems
    ]
    return torch.from_numpy(np.stack(feats))


def make_predict(model: FNO2d):
    model.eval()

    def predict(problems: Sequence[HeatProblem]) -> list[np.ndarray]:
        with torch.no_grad():
            out = model(features(problems)) * T_SCALE
        return [o.double().numpy() for o in out]

    return predict
