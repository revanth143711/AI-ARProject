# Asynchronous AR Reconciliation Workflow Engine

This project implements an asynchronous workflow engine for Accounts Receivable (AR) reconciliation. The system processes financial records through multiple stages and focuses on workflow orchestration, retries, and state management.

---

## Overview

The workflow is divided into four stages:

* Ingestion: Generates or loads ERP data
* Matching: Recomputes balances and identifies mismatches
* Validation: Detects anomalies using a simple model
* Decision: Routes records for manual review or auto approval

Each stage is independent and may fail. Failed stages are retried, and the workflow resumes from the last successful stage instead of restarting.

---

## Key Features

* Asynchronous processing using asyncio to handle multiple records concurrently
* Retry mechanism for handling failures at each stage
* Persistent workflow state stored in a JSON file
* Resume capability from the last successful stage
* Idempotent execution to prevent duplicate processing
* Modular structure with separate components for each stage

---

## Project Structure

```
ar-audit/
│
├── data/
│   └── erp_export.csv
│
├── reports/
│   ├── mismatches_rule_based.csv
│   └── anomalies_ml.csv
│
├── src/
│   ├── generate_ar.py
│   ├── reconcile.py
│   ├── anomalies.py
│   └── engine.py
│
├── workflow_state.json
├── requirements.txt
└── main.py
```

---

## Running the Project

1. Clone the repository
2. Install dependencies

```
pip install -r requirements.txt
```

3. Run the workflow

```
python main.py
```

---

## Workflow Behavior

Records are processed in parallel. Each stage may fail randomly and is retried a fixed number of times. After each stage, the state is saved. If the process is restarted, it resumes from the last completed stage for each record.

---

## Outputs

workflow_state.json contains the stage-wise progress of each record
mismatches_rule_based.csv contains rule-based mismatches
anomalies_ml.csv contains detected anomalies

---

## Conclusion

This project demonstrates a workflow system that handles failures, retries, and stateful execution across multiple stages while maintaining parallel processing and consistency.
