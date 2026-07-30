import json
import os
from packages.evals.metrics import evaluate_run_record

def run_evaluation_suite(dataset_path: str):
    if not os.path.exists(dataset_path):
        print(f"Dataset path {dataset_path} not found.")
        return

    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    results = []
    for item in dataset:
        metrics = evaluate_run_record(item)
        results.append({"id": item.get("id"), "metrics": metrics})

    print("=== Evaluation Benchmark Results ===")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    run_evaluation_suite("packages/evals/sample_dataset.json")
