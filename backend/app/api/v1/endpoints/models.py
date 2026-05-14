from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pathlib import Path
import csv

router = APIRouter()


@router.get("/logs/{model_name}")
async def get_model_logs(model_name: str):
    model_dir = Path(__file__).resolve().parents[3] / "models"
    log_file = model_dir / (model_name + ".log.csv")
    if not log_file.exists():
        raise HTTPException(status_code=404, detail="Log file not found")

    rows = []
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                # convert numeric fields
                for k, v in r.items():
                    try:
                        if v is None or v == "":
                            r[k] = None
                        else:
                            # try float
                            r[k] = float(v)
                    except Exception:
                        pass
                rows.append(r)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"model": model_name, "rows": rows}
