"""Train the FNO surrogate on in-distribution problems (CPU, a few minutes)."""

import json
import time
from pathlib import Path

import numpy as np
import torch

from cprcheck.data import IN_DIST, batch
from cprcheck.fno import FNO2d, T_SCALE, features
from cprcheck.solver import solve

OUT = Path(__file__).resolve().parent.parent / "results"


def main(n_train: int = 1000, epochs: int = 150, seed: int = 0) -> None:
    torch.manual_seed(seed)
    probs = batch(IN_DIST, n_train, seed=1)
    X = features(probs)
    Y = torch.from_numpy(np.stack([solve(p) for p in probs]).astype(np.float32)) / T_SCALE
    model = FNO2d()
    opt = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, epochs)
    t0 = time.time()
    for ep in range(epochs):
        perm = torch.randperm(n_train)
        tot = 0.0
        for i in range(0, n_train, 32):
            j = perm[i : i + 32]
            pred = model(X[j])
            loss = (torch.linalg.vector_norm(pred - Y[j], dim=(1, 2)) / torch.linalg.vector_norm(Y[j], dim=(1, 2))).mean()
            opt.zero_grad()
            loss.backward()
            opt.step()
            tot += loss.item() * len(j)
        sched.step()
        if ep % 10 == 0 or ep == epochs - 1:
            print(f"epoch {ep:3d} train rel-L2 {tot / n_train:.4f}  {time.time() - t0:.0f}s", flush=True)
    OUT.mkdir(exist_ok=True)
    torch.save(model.state_dict(), OUT / "fno.pt")
    (OUT / "train_log.json").write_text(json.dumps({"n_train": n_train, "epochs": epochs, "seed": seed, "final_train_rel_l2": tot / n_train, "seconds": time.time() - t0}, indent=2))


if __name__ == "__main__":
    main()
