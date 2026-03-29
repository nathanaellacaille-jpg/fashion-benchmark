# db.py
# Dependencies: supabase-py>=2.0, python-dotenv>=1.0
# Python tested: 3.11+
#
# All operations raise RuntimeError on failure so callers get an explicit
# message rather than a silent None or raw Supabase exception.

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv(dotenv_path="F:/fashion-benchmark/keys.env")

_client: Client | None = None


def _get_client() -> Client:
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        if not url or not key:
            raise RuntimeError(
                "Missing credentials: SUPABASE_URL and SUPABASE_ANON_KEY "
                "must be set in .env"
            )
        _client = create_client(url, key)
    return _client


def insert_prediction(data: dict) -> str:
    """Insert a row into predictions. Returns the new uuid as str."""
    try:
        res = _get_client().table("predictions").insert(data).execute()
    except Exception as e:
        raise RuntimeError(f"insert_prediction failed: {e}") from e
    rows = res.data
    if not rows:
        raise RuntimeError("insert_prediction: no row returned after insert")
    return rows[0]["id"]


def insert_resolution(prediction_id: str, outcome: bool, raw_data: dict,
                      t1_value: float = None, t2_value: float = None,
                      computed_metric: float = None, notes: str = None) -> str:
    """Insert a row into resolutions. Returns the new uuid as str."""
    payload = {
        "prediction_id": prediction_id,
        "outcome": outcome,
        "raw_data_snapshot": raw_data,
    }
    if t1_value is not None:
        payload["t1_value"] = t1_value
    if t2_value is not None:
        payload["t2_value"] = t2_value
    if computed_metric is not None:
        payload["computed_metric"] = computed_metric
    if notes is not None:
        payload["notes"] = notes
    try:
        res = _get_client().table("resolutions").insert(payload).execute()
    except Exception as e:
        raise RuntimeError(f"insert_resolution failed: {e}") from e
    rows = res.data
    if not rows:
        raise RuntimeError("insert_resolution: no row returned after insert")
    return rows[0]["id"]


def insert_score(prediction_id: str, brier: float, log_score: float,
                 bsl_brier: float) -> str:
    """Insert a row into scores. Returns the new uuid as str."""
    brier_skill = 1.0 - (brier / bsl_brier) if bsl_brier else None
    payload = {
        "prediction_id": prediction_id,
        "brier_score": brier,
        "log_score": log_score,
        "baseline_naive_brier": bsl_brier,
        "brier_skill_score": brier_skill,
    }
    try:
        res = _get_client().table("scores").insert(payload).execute()
    except Exception as e:
        raise RuntimeError(f"insert_score failed: {e}") from e
    rows = res.data
    if not rows:
        raise RuntimeError("insert_score: no row returned after insert")
    return rows[0]["id"]


def get_prediction(id: str) -> dict:
    """Return a single prediction row as dict, or raise if not found."""
    try:
        res = _get_client().table("predictions").select("*").eq("id", id).execute()
    except Exception as e:
        raise RuntimeError(f"get_prediction failed: {e}") from e
    rows = res.data
    if not rows:
        raise RuntimeError(f"get_prediction: no prediction found for id={id}")
    return rows[0]


def list_open_predictions() -> list:
    """Return all predictions that have no resolution yet."""
    try:
        # Left-join via Supabase: fetch prediction ids that appear in resolutions
        resolved = _get_client().table("resolutions").select("prediction_id").execute()
    except Exception as e:
        raise RuntimeError(f"list_open_predictions failed (resolutions query): {e}") from e

    resolved_ids = [r["prediction_id"] for r in resolved.data]

    try:
        query = _get_client().table("predictions").select("*")
        if resolved_ids:
            query = query.not_.in_("id", resolved_ids)
        res = query.execute()
    except Exception as e:
        raise RuntimeError(f"list_open_predictions failed (predictions query): {e}") from e

    return res.data
