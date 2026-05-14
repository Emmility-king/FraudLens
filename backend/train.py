"""Simple CLI to generate synthetic data and train the demo model.

Run from the `backend` folder:

    python train.py --out data/synth.csv --model-name demo.pt --epochs 6

"""
from __future__ import annotations

import argparse
from pathlib import Path

from app.services.synth import generate_synthetic_transactions
from app.services.model import train_model_from_df
import pandas as pd


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--rows", type=int, default=5000)
    p.add_argument("--out", type=str, default="data/synth.csv")
    p.add_argument("--model-name", type=str, default="demo.pt")
    p.add_argument("--epochs", type=int, default=6)
    args = p.parse_args(argv)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print("Generating synthetic data...")
    df = generate_synthetic_transactions(n=args.rows, out_path=str(out_path))
    print(f"Wrote {len(df)} rows to {out_path}")

    print("Training model...")
    res = train_model_from_df(df, save_name=args.model_name, epochs=args.epochs)
    print("Trained model:", res)


if __name__ == "__main__":
    main()
