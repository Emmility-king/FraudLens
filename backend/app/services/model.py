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
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score
import csv

# Optional TensorBoard
try:
    from torch.utils.tensorboard import SummaryWriter

    _HAS_TB = True
except Exception:
    _HAS_TB = False


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


class Preprocessor:
    """Fit/transform simple preprocessing: scale `amount` and one-hot merchants/channels."""

    def __init__(self):
        self.amount_scaler: StandardScaler | None = None
        self.enc: OneHotEncoder | None = None
        self.feature_names: list[str] = []

    def fit(self, df: pd.DataFrame) -> "Preprocessor":
        dfc = df.copy()
        dfc["amount"] = dfc["amount"].astype(float)
        # fit scaler on amount
        self.amount_scaler = StandardScaler()
        self.amount_scaler.fit(dfc[["amount"]])

        # fit one-hot encoder on merchant+channel
        cat = dfc[["merchant", "channel"]].fillna("__na__")
        self.enc = OneHotEncoder(sparse=False, handle_unknown="ignore")
        self.enc.fit(cat)
        # names
        self.feature_names = ["amount"] + list(self.enc.get_feature_names_out(["merchant", "channel"]))
        return self

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        dfc = df.copy()
        dfc["amount"] = dfc["amount"].astype(float).fillna(0.0)
        amount_scaled = (
            self.amount_scaler.transform(dfc[["amount"]]) if self.amount_scaler is not None else dfc[["amount"]].to_numpy()
        )
        cat = dfc[["merchant", "channel"]].fillna("__na__")
        cat_ohe = self.enc.transform(cat) if self.enc is not None else np.zeros((len(dfc), 0))
        X = np.hstack([amount_scaled, cat_ohe])
        return X

    def save(self, path: Path) -> None:
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path: Path) -> "Preprocessor":
        with open(path, "rb") as f:
            return pickle.load(f)


def _prepare_df(df: pd.DataFrame) -> tuple[np.ndarray, dict]:
    # deprecated compatibility shim — use Preprocessor in new functions
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
    # fit preprocessor
    pre = Preprocessor()
    pre.fit(df)
    X = pre.transform(df)
    y = df["label"].to_numpy(dtype=int)

    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.15, random_state=42, stratify=y)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = SimpleMLP(input_dim=X.shape[1])
    model.to(device)

    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.BCELoss()

    # logging
    log_path = MODEL_DIR / (save_name + ".log.csv")
    tb = SummaryWriter(log_dir=str(MODEL_DIR / (save_name + ".tb"))) if _HAS_TB else None
    with open(log_path, "w", newline="") as lf:
        writer = csv.writer(lf)
        writer.writerow(["epoch", "train_loss", "val_loss", "precision", "recall", "f1", "roc_auc"])

        for epoch in range(1, epochs + 1):
            model.train()
            xb = torch.from_numpy(X_train).float().to(device)
            yb = torch.from_numpy(y_train).float().to(device)
            pred = model(xb)
            loss = loss_fn(pred, yb)
            opt.zero_grad()
            loss.backward()
            opt.step()

            # validation
            model.eval()
            with torch.no_grad():
                xv = torch.from_numpy(X_val).float().to(device)
                yv = torch.from_numpy(y_val).float().to(device)
                pv = model(xv)
                val_loss = float(loss_fn(pv, yv).item())
                pv_cpu = pv.cpu().numpy()
                yv_cpu = yv.cpu().numpy()

            # metrics
            precision, recall, f1, _ = precision_recall_fscore_support(yv_cpu, (pv_cpu > 0.5).astype(int), average="binary", zero_division=0)
            try:
                roc = float(roc_auc_score(yv_cpu, pv_cpu)) if len(np.unique(yv_cpu)) > 1 else float("nan")
            except Exception:
                roc = float("nan")

            writer.writerow([epoch, float(loss.item()), val_loss, precision, recall, f1, roc])
            lf.flush()
            if tb:
                tb.add_scalar("loss/train", float(loss.item()), epoch)
                tb.add_scalar("loss/val", val_loss, epoch)
                tb.add_scalar("metrics/precision", precision, epoch)
                tb.add_scalar("metrics/recall", recall, epoch)
                tb.add_scalar("metrics/f1", f1, epoch)
                if not np.isnan(roc):
                    tb.add_scalar("metrics/roc_auc", roc, epoch)

    # save model and metadata + preprocessor
    path = MODEL_DIR / save_name
    torch.save(model.state_dict(), path)
    with open(MODEL_DIR / (save_name + ".meta"), "wb") as f:
        pickle.dump({"input_dim": X.shape[1]}, f)
    pre.save(MODEL_DIR / (save_name + ".preproc"))

    if tb:
        tb.close()

    return {"model_path": str(path), "meta_path": str(MODEL_DIR / (save_name + ".meta")), "preproc": str(MODEL_DIR / (save_name + ".preproc")), "log": str(log_path)}


def load_model(save_name: str = "model.pt") -> tuple[nn.Module, dict]:
    path = MODEL_DIR / save_name
    meta_path = MODEL_DIR / (save_name + ".meta")
    preproc_path = MODEL_DIR / (save_name + ".preproc")
    if not path.exists() or not meta_path.exists() or not preproc_path.exists():
        raise FileNotFoundError("Model, metadata, or preprocessor not found. Train a model first.")
    # load meta
    with open(meta_path, "rb") as f:
        meta = pickle.load(f)
    model = SimpleMLP(input_dim=meta.get("input_dim", 3))
    model.load_state_dict(torch.load(path, map_location="cpu"))
    model.eval()
    pre = Preprocessor.load(preproc_path)
    return model, {"meta": meta, "preproc": pre}


def predict_df(df: pd.DataFrame, save_name: str = "model.pt") -> list[float]:
    model_res = load_model(save_name)
    model = model_res[0]
    pre = model_res[1]["preproc"]
    X = pre.transform(df)
    xb = torch.from_numpy(X).float()
    with torch.no_grad():
        scores = model(xb).numpy().tolist()
    return scores

