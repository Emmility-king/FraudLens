from __future__ import annotations

import os
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.model_selection import train_test_split


MODEL_DIR = Path(__file__).resolve().parents[2] / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


class SimpleMLP(nn.Module):
    def __init__(self, input_dim: int, hidden: int = 64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden // 2),
            nn.ReLU(),
            nn.Linear(hidden // 2, 1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


def _prepare_df(df: pd.DataFrame) -> tuple[np.ndarray, dict]:
    # simple feature engineering: amount, merchant hash, channel one-hot
    dfc = df.copy()
    dfc["amount"] = dfc["amount"].astype(float)
    merchants = sorted(dfc["merchant"].unique())
    merchant_map = {m: i for i, m in enumerate(merchants)}
    dfc["merchant_id"] = dfc["merchant"].map(merchant_map).fillna(0).astype(int)

    channels = sorted(dfc["channel"].unique())
    channel_map = {c: i for i, c in enumerate(channels)}
    dfc["channel_id"] = dfc["channel"].map(channel_map).fillna(0).astype(int)

    # build numeric matrix
    X = np.column_stack([
        dfc["amount"].to_numpy(dtype=float),
        dfc["merchant_id"].to_numpy(dtype=float),
        dfc["channel_id"].to_numpy(dtype=float),
    ])
    meta = {"merchant_map": merchant_map, "channel_map": channel_map}
    return X, meta


def train_model_from_df(df: pd.DataFrame, save_name: str = "model.pt", epochs: int = 8) -> dict[str, Any]:
    X, meta = _prepare_df(df)
    y = df["label"].to_numpy(dtype=int)

    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.15, random_state=42, stratify=y)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = SimpleMLP(input_dim=X.shape[1])
    model.to(device)

    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.BCELoss()

    for epoch in range(epochs):
        model.train()
        xb = torch.from_numpy(X_train).float().to(device)
        yb = torch.from_numpy(y_train).float().to(device)
        pred = model(xb)
        loss = loss_fn(pred, yb)
        opt.zero_grad()
        loss.backward()
        opt.step()

    # save model and metadata
    path = MODEL_DIR / save_name
    torch.save(model.state_dict(), path)
    with open(MODEL_DIR / (save_name + ".meta"), "wb") as f:
        pickle.dump(meta, f)

    return {"model_path": str(path), "meta_path": str(MODEL_DIR / (save_name + ".meta"))}


def load_model(save_name: str = "model.pt") -> tuple[nn.Module, dict]:
    path = MODEL_DIR / save_name
    meta_path = MODEL_DIR / (save_name + ".meta")
    if not path.exists() or not meta_path.exists():
        raise FileNotFoundError("Model or metadata not found. Train a model first.")
    # infer input dim from meta (merchant/channel counts)
    with open(meta_path, "rb") as f:
        meta = pickle.load(f)
    # pick a safe input dim (amount + merchant_id + channel_id)
    model = SimpleMLP(input_dim=3)
    model.load_state_dict(torch.load(path, map_location="cpu"))
    model.eval()
    return model, meta


def predict_df(df: pd.DataFrame, save_name: str = "model.pt") -> list[float]:
    model, meta = load_model(save_name)
    # reproduce simple transforms
    dfc = df.copy()
    dfc["amount"] = dfc["amount"].astype(float)
    dfc["merchant_id"] = dfc["merchant"].map(meta.get("merchant_map", {})).fillna(0).astype(float)
    dfc["channel_id"] = dfc["channel"].map(meta.get("channel_map", {})).fillna(0).astype(float)

    X = np.column_stack([dfc["amount"].to_numpy(dtype=float), dfc["merchant_id"].to_numpy(dtype=float), dfc["channel_id"].to_numpy(dtype=float)])
    xb = torch.from_numpy(X).float()
    with torch.no_grad():
        scores = model(xb).numpy().tolist()
    return scores

