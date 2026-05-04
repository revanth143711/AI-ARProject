import asyncio
import random
import json
import os

from generate_ar import generate_data
from reconcile import run_reconciliation
from anomalies import run_anomaly_detection


STAGES = ["ingestion", "matching", "validation", "decision"]
MAX_RETRIES = 3
STATE_FILE = "workflow_state.json"

SEM = asyncio.Semaphore(10)


if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        STATE = json.load(f)
else:
    STATE = {}


def save_state():
    with open(STATE_FILE, "w") as f:
        json.dump(STATE, f, indent=2)


def update_state(record_id, stage, status):
    if record_id not in STATE:
        STATE[record_id] = {}
    STATE[record_id][stage] = status


def last_stage(record_id):
    if record_id not in STATE:
        return None
    for s in reversed(STAGES):
        if STATE[record_id].get(s) == "success":
            return s
    return None


def is_done(record_id):
    return STATE.get(record_id, {}).get("decision") == "success"


async def execute(stage, record_id, anomalies):
    # simulate random failure
    if random.random() < 0.2:
        raise Exception("random failure")

    if stage == "decision":
        return "manual_review" if record_id in anomalies else "approved"

    return "ok"


async def process(record_id, anomalies):
    async with SEM:
        if is_done(record_id):
            return

        prev = last_stage(record_id)
        start = STAGES.index(prev) + 1 if prev else 0

        for stage in STAGES[start:]:
            for attempt in range(MAX_RETRIES):
                try:
                    result = await execute(stage, record_id, anomalies)
                    print(f"{record_id} → {stage} → {result}")

                    update_state(record_id, stage, "success")
                    break

                except Exception:
                    if attempt == MAX_RETRIES - 1:
                        update_state(record_id, stage, "failed")
                        return
                    await asyncio.sleep(0.2)


async def runTask():
    print("Generating data...")
    records = generate_data()
    ids = [r["Customer ID"] for r in records]

    print("Running matching...")
    run_reconciliation()

    print("Running validation...")
    anomalies = run_anomaly_detection()
    anomaly_ids = set(r["Customer ID"] for r in anomalies)

    tasks = [process(rid, anomaly_ids) for rid in ids]
    await asyncio.gather(*tasks)

    save_state()
    print("Done.")
