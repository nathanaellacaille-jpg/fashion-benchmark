# seed_p4.py
# Dependencies: supabase-py>=2.0, python-dotenv>=1.0
# Python tested: 3.11+
#
# Inserts prediction P4 as the first test record in Supabase.
# Reads resolution_p4.json for ground-truth values.
# seal_hash = SHA-256(statement + deadline) — computed before insert,
# then re-computed with the returned id and stored as the final hash
# (statement + id + deadline) for strong uniqueness per the spec.

import hashlib
import json
import sys
from datetime import date

from db import insert_prediction, insert_resolution, insert_score
from scoring import compute_brier_score, compute_log_score

# -- Load resolution data --------------------------------------------------
with open("F:/fashion-benchmark/resolution_p4.json", encoding="utf-8") as f:
    res_data = json.load(f)

STATEMENT = res_data["statement"]
DEADLINE  = "2026-03-31"
PROB      = 0.70  # hypothetical forecast probability for scoring test
OUTCOME   = res_data["outcome"] == "TRUE"  # False

# -- Prediction payload ----------------------------------------------------
# Preliminary seal hash (statement + deadline); will be replaced after insert
def _seal(statement: str, prediction_id: str, deadline: str) -> str:
    raw = f"{statement}|{prediction_id}|{deadline}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

# Placeholder hash to satisfy UNIQUE NOT NULL before we know the id
import uuid
placeholder_id = str(uuid.uuid4())
seal = _seal(STATEMENT, placeholder_id, DEADLINE)

prediction_payload = {
    "statement":           STATEMENT,
    "attribute":           "search volume",
    "category":            "chaussures femme",
    "market":              "GB",
    "source":              "google_trends",
    "query_term":          res_data["query_term"],
    "threshold_operator":  ">",
    "threshold_value":     res_data["threshold"],
    "threshold_unit":      "ratio_yoy",
    "deadline":            DEADLINE,
    "probability":         PROB,
    "submitted_by":        "protocol_test",
    "seal_hash":           seal,
    "resolution_criteria": (
        "YoY growth of Google Trends index for 'ballerina flat' in GB, "
        "T1 2026 vs T1 2025 (months 1-3), must exceed +40%."
    ),
}

# -- Insert sequence -------------------------------------------------------
print("Inserting prediction...")
pred_id = insert_prediction(prediction_payload)
print(f"  prediction id : {pred_id}")

# Update seal_hash with the real id (requires an update call)
final_seal = _seal(STATEMENT, pred_id, DEADLINE)
from db import _get_client
try:
    _get_client().table("predictions").update({"seal_hash": final_seal}).eq("id", pred_id).execute()
    print(f"  seal_hash     : {final_seal}")
except Exception as e:
    print(f"  [WARN] Could not update seal_hash: {e}")

print("\nInserting resolution...")
snap = res_data["data_snapshot"]
res_id = insert_resolution(
    prediction_id   = pred_id,
    outcome         = OUTCOME,
    raw_data        = snap,
    t1_value        = res_data["t1_2025_mean"],
    t2_value        = res_data["t1_2026_mean"],
    computed_metric = res_data["yoy_growth"],
    notes           = snap.get("note"),
)
print(f"  resolution id : {res_id}")

# -- Scoring ---------------------------------------------------------------
outcome_int = int(OUTCOME)
brier  = compute_brier_score(PROB, outcome_int)
log_sc = compute_log_score(PROB, outcome_int)

# Baseline naive Brier: forecaster always predicts 0.5
bsl_brier = compute_brier_score(0.5, outcome_int)

print("\nInserting score...")
score_id = insert_score(pred_id, brier, log_sc, bsl_brier)
print(f"  score id      : {score_id}")

# -- Summary ---------------------------------------------------------------
brier_skill = 1.0 - (brier / bsl_brier) if bsl_brier else None
print(f"""
========================================
  P4 SEED SUMMARY
========================================
  prediction_id     : {pred_id}
  statement         : {STATEMENT[:60]}...
  probability       : {PROB}
  outcome           : {OUTCOME} (FALSE)
  ---
  brier_score       : {brier:.4f}
  log_score         : {log_sc:.4f}
  baseline_brier    : {bsl_brier:.4f}
  brier_skill_score : {brier_skill:.4f}
========================================
""")
