"""CLI command to run benchmark evaluation suite."""
import argparse
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.evaluation.runner import EvaluationRunner

def main():
    parser = argparse.ArgumentParser(description="Run QueryMind AI benchmark evaluation.")
    parser.add_argument("--limit", type=int, default=30, help="Number of benchmark questions to evaluate (default: 30)")
    args = parser.parse_args()

    print(f"Starting QueryMind AI evaluation on {args.limit} benchmark cases...")
    runner = EvaluationRunner()
    report = runner.run_benchmark(limit=args.limit)

    print("\n================ EVALUATION REPORT SUMMARY ================")
    print(f"Benchmark Cases Evaluated: {report['benchmark_cases_evaluated']}")
    print(f"Security Block Rate: {report['security_tests']['block_rate_pct']}% ({report['security_tests']['blocked']}/{report['security_tests']['total']})")
    print(f"Schema Router Recall: {report['schema_router_accuracy']['recall_at_predicted_pct']}%")
    print(f"Execution Success Rate: {report['sql_execution']['execution_rate_pct']}%")
    print(f"Average Pipeline Latency: {report['latency']['avg_latency_ms']} ms")
    print("===========================================================\n")

if __name__ == "__main__":
    main()
