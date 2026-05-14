from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd


def generate_synthetic_transactions(n: int = 5000, out_path: str | None = None) -> pd.DataFrame:
    """Generate a synthetic transactions DataFrame with a skewed fraud label.

    Columns: occurred_at, amount, merchant, channel, label
    """
    rng = np.random.default_rng(seed=42)
    merchants = [f"merchant_{i}" for i in range(50)]
    channels = ["card", "transfer", "cash", "online"]

    rows = []
    now = datetime.now(timezone.utc)
    for i in range(n):
        occurred = now - timedelta(seconds=int(rng.integers(0, 86400 * 90)))
        amount = float(abs(rng.normal(50, 120)))
        merchant = rng.choice(merchants)
        channel = rng.choice(channels)

        # create a small fraction of frauds influenced by amount and merchant
        prob = 0.002 + (amount > 1000) * 0.02 + (merchant.endswith("7")) * 0.01
        label = 1 if rng.random() < prob else 0

        rows.append((occurred.isoformat(), amount, merchant, channel, int(label)))

    df = pd.DataFrame(rows, columns=["occurred_at", "amount", "merchant", "channel", "label"])

    if out_path:
        out_p = Path(out_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_p, index=False)

    return df

