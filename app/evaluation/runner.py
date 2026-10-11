"""Automated evaluation runner for Schema Router, RAG, SQL validation, and Security."""
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from app.config import get_settings
from app.evaluation.benchmark import EVALUATION_BENCHMARK_CASES
from app.services.query_pipeline import QueryPipeline
from app.database.query_executor import QueryExecutor

logger = logging.getLogger("querymind.evaluation")
settings = get_settings()

class EvaluationRunner:
    """Executes multi-dimensional benchmark suite and computes exact metrics."""

    def __init__(self):
        self.pipeline = QueryPipeline()
        self.executor = QueryExecutor()

    def run_benchmark(self, limit: int = 50) -> Dict[str, Any]:
        """Runs evaluation over benchmark cases and aggregates performance."""
        cases = EVALUATION_BENCHMARK_CASES[:limit]
        results = []

        total_cases = len(cases)
        security_total = 0
        security_blocked = 0
        schema_routing_hits = 0
        safe_eval_total = 0
        sql_parse_success = 0
        execution_success = 0
        exact_match_success = 0

        latencies = []

        logger.info(f"Running evaluation benchmark on {total_cases} cases...")

        for c in cases:
            q_id = c["question_id"]
            q_text = c["question"]
            safety = c["safety_class"]
            gt_sql = c["ground_truth_sql"]
            expected_tables = set(c["relevant_tables"])

            # Execute pipeline
            start_t = time.perf_counter()
            pipe_out = self.pipeline.process_query(q_text)
            lat = round((time.perf_counter() - start_t) * 1000, 2)
            latencies.append(lat)

            # Security test cases
            if safety != "SAFE":
                security_total += 1
                is_blocked = (not pipe_out["success"]) or ("REJECTED" in pipe_out.get("status", ""))
                if is_blocked:
                    security_blocked += 1
                results.append({
                    "question_id": q_id,
                    "question": q_text,
                    "category": c["category"],
                    "safety_class": safety,
                    "passed": is_blocked,
                    "status": pipe_out.get("status"),
                    "latency_ms": lat
                })
                continue

            safe_eval_total += 1

            # Schema routing accuracy
            # Check predicted tables vs expected
            predicted_tables = set()
            for stage in pipe_out.get("diagnostics", {}).get("stages", []):
                if stage.get("stage") == "Schema Router (ML)":
                    predicted_tables = set(stage.get("predicted_tables", []))

            # Hit if at least one expected table is in predicted
            if not expected_tables or (expected_tables & predicted_tables):
                schema_routing_hits += 1

            # SQL & Execution
            if pipe_out.get("generated_sql"):
                sql_parse_success += 1

            is_exec_ok = pipe_out.get("success", False)
            if is_exec_ok:
                execution_success += 1

            # Result numerical comparison vs Ground Truth SQL
            result_match = False
            if gt_sql and is_exec_ok:
                gt_exec = self.executor.execute_query(gt_sql)
                if gt_exec["success"] and gt_exec["rows"] and pipe_out.get("rows"):
                    # Compare first row scalar or structure
                    gt_val = list(gt_exec["rows"][0].values())[0] if gt_exec["rows"][0] else None
                    gen_val = list(pipe_out["rows"][0].values())[0] if pipe_out["rows"][0] else None
                    if gt_val == gen_val:
                        result_match = True
                        exact_match_success += 1

            results.append({
                "question_id": q_id,
                "question": q_text,
                "category": c["category"],
                "generated_sql": pipe_out.get("generated_sql"),
                "execution_status": pipe_out.get("status"),
                "result_match": result_match,
                "latency_ms": lat
            })

        # Summary Metrics
        sec_block_rate = round((security_blocked / security_total * 100), 2) if security_total > 0 else 100.0
        router_recall = round((schema_routing_hits / safe_eval_total * 100), 2) if safe_eval_total > 0 else 0.0
        exec_rate = round((execution_success / safe_eval_total * 100), 2) if safe_eval_total > 0 else 0.0
        avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0

        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "benchmark_cases_evaluated": total_cases,
            "security_tests": {
                "total": security_total,
                "blocked": security_blocked,
                "block_rate_pct": sec_block_rate
            },
            "schema_router_accuracy": {
                "safe_cases": safe_eval_total,
                "hits": schema_routing_hits,
                "recall_at_predicted_pct": router_recall
            },
            "sql_execution": {
                "generated_count": sql_parse_success,
                "execution_success_count": execution_success,
                "execution_rate_pct": exec_rate,
                "exact_numerical_matches": exact_match_success
            },
            "latency": {
                "avg_latency_ms": avg_latency,
                "min_latency_ms": min(latencies) if latencies else 0,
                "max_latency_ms": max(latencies) if latencies else 0
            },
            "detailed_results": results
        }

        # Save to reports
        out_file = settings.REPORTS_DIR / f"eval_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        out_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
        logger.info(f"Evaluation report written to {out_file}")
        return report
