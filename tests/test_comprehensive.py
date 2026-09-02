"""
Comprehensive Evaluation Script for Honey-Pot Scam Detection System
===================================================================
Features:
  - Result caching (skips already-tested messages)
  - Rate-limit safe delays between LLM calls
  - Dry-run mode (--dry-run)
  - Per-category precision/recall/F1 breakdown
  - Markdown report generation
  - Budget tracker for API usage

Usage:
  python tests/test_comprehensive.py                  # Run all uncached
  python tests/test_comprehensive.py --dry-run        # Preview without API calls
  python tests/test_comprehensive.py --max 20         # Run up to 20 messages
  python tests/test_comprehensive.py --clear-cache    # Wipe cache and re-run
"""

import json
import time
import sys
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.detection import detect_scam


# ── Paths ──────────────────────────────────────────────────────────────────────
TESTS_DIR = Path(__file__).parent
DATASET_PATH = TESTS_DIR / "evaluation_dataset_v2.json"
CACHE_PATH = TESTS_DIR / "eval_cache.json"
REPORT_PATH = TESTS_DIR / "evaluation_report.md"

# Rate-limit settings
DEFAULT_DELAY = 2.5  # seconds between LLM calls (safe for 30 RPM)
MONTHLY_BUDGET = 1000


# ── Helpers ────────────────────────────────────────────────────────────────────

def load_dataset() -> list:
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["test_messages"]


def load_cache() -> dict:
    if CACHE_PATH.exists():
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache: dict):
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def evaluate_single(message_data: dict, cache: dict, dry_run: bool = False) -> dict:
    msg_id = message_data["id"]

    # Return cached result if available
    if msg_id in cache:
        return cache[msg_id]

    if dry_run:
        return {
            "id": msg_id,
            "label": message_data["label"],
            "category": message_data["category"],
            "message": message_data["message"],
            "predicted_scam": False,
            "confidence": 0.0,
            "response_time": 0.0,
            "error": None,
            "status": "dry_run",
        }

    message_text = message_data["message"]
    start = time.time()
    try:
        result = detect_scam(message_text)
        elapsed = time.time() - start
        detected = result.get("is_scam", False)
        confidence = result.get("confidence", 0.0)

        return {
            "id": msg_id,
            "label": message_data["label"],
            "category": message_data["category"],
            "message": message_text,
            "expected_detection": message_data["expected_detection"],
            "predicted_scam": detected,
            "confidence": confidence,
            "response_time": round(elapsed, 3),
            "error": None,
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "id": msg_id,
            "label": message_data["label"],
            "category": message_data["category"],
            "message": message_text,
            "expected_detection": message_data["expected_detection"],
            "predicted_scam": False,
            "confidence": 0.0,
            "response_time": round(elapsed, 3),
            "error": str(e),
        }


def build_confusion_matrix(results: list) -> dict:
    tp = tn = fp = fn = 0
    for r in results:
        actual = r["label"]
        predicted = r["predicted_scam"]
        if actual == "scam" and predicted:
            tp += 1
        elif actual == "legitimate" and not predicted:
            tn += 1
        elif actual == "legitimate" and predicted:
            fp += 1
        elif actual == "scam" and not predicted:
            fn += 1
    return {"TP": tp, "TN": tn, "FP": fp, "FN": fn}


def compute_metrics(cm: dict) -> dict:
    tp, tn, fp, fn = cm["TP"], cm["TN"], cm["FP"], cm["FN"]
    total = tp + tn + fp + fn
    pos = tp + fn
    neg = tn + fp
    pred_pos = tp + fp

    accuracy = (tp + tn) / total if total else 0
    precision = tp / pred_pos if pred_pos else 0
    recall = tp / pos if pos else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0
    fpr = fp / neg if neg else 0
    fnr = fn / pos if pos else 0

    return {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "false_positive_rate": round(fpr, 4),
        "false_negative_rate": round(fnr, 4),
        "total": total,
    }


def per_category_metrics(results: list) -> dict:
    by_cat = defaultdict(lambda: {"TP": 0, "TN": 0, "FP": 0, "FN": 0, "count": 0})
    for r in results:
        cat = r["category"]
        by_cat[cat]["count"] += 1
        actual = r["label"]
        predicted = r["predicted_scam"]
        if actual == "scam" and predicted:
            by_cat[cat]["TP"] += 1
        elif actual == "legitimate" and not predicted:
            by_cat[cat]["TN"] += 1
        elif actual == "legitimate" and predicted:
            by_cat[cat]["FP"] += 1
        elif actual == "scam" and not predicted:
            by_cat[cat]["FN"] += 1

    out = {}
    for cat, cm in sorted(by_cat.items()):
        m = compute_metrics(cm)
        m["count"] = cm["count"]
        out[cat] = m
    return out


# ── Report generator ──────────────────────────────────────────────────────────

def generate_report(
    results: list,
    global_metrics: dict,
    cat_metrics: dict,
    dry_run: bool,
    cache_used: int,
    new_run: int,
) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cm = build_confusion_matrix(results)
    errors = [r for r in results if r.get("error")]
    fps = [r for r in results if r["label"] == "legitimate" and r["predicted_scam"]]
    fns = [r for r in results if r["label"] == "scam" and not r["predicted_scam"]]
    avg_rt = (
        round(sum(r["response_time"] for r in results) / len(results), 3)
        if results
        else 0
    )
    cached_ids = [r["id"] for r in results if r.get("status") == "cached"]

    lines = [
        "# Honey-Pot — Evaluation Report",
        "",
        f"> Generated: {now}  ",
        f"> Messages: **{global_metrics['total']}** | Cached hits: {cache_used} | New calls: {new_run}",
        "",
        "---",
        "",
        "## Global Metrics",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Accuracy | **{global_metrics['accuracy']:.2%}** |",
        f"| Precision | **{global_metrics['precision']:.2%}** |",
        f"| Recall | **{global_metrics['recall']:.2%}** |",
        f"| F1 Score | **{global_metrics['f1_score']:.2%}** |",
        f"| False Positive Rate | **{global_metrics['false_positive_rate']:.2%}** |",
        f"| False Negative Rate | **{global_metrics['false_negative_rate']:.2%}** |",
        f"| Avg Response Time | {avg_rt}s |",
        "",
        "## Confusion Matrix",
        "",
        "```",
        "                Predicted",
        "                Scam  | Legit",
        "Actual Scam  :   {:>3}  |  {:<3}  (TP={:<3} FN={})".format(
            cm["TP"] + cm["FN"], 0, cm["TP"], cm["FN"]
        ),
        "Actual Legit :   {:>3}  |  {:<3}  (FP={:<3} TN={})".format(
            cm["FP"], cm["TN"], cm["FP"], cm["TN"]
        ),
        "```",
        "",
        "",
    ]

    # ── Per-category table ────────────────────────────────────────────────
    lines += [
        "## Per-Category Breakdown",
        "",
        "| Category | Count | Accuracy | Precision | Recall | F1 | FP | FN |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for cat, m in cat_metrics.items():
        fp_count = sum(1 for r in results if r["category"] == cat and r["label"] == "legitimate" and r["predicted_scam"])
        fn_count = sum(1 for r in results if r["category"] == cat and r["label"] == "scam" and not r["predicted_scam"])
        lines.append(
            f"| {cat} | {m['count']} | {m['accuracy']:.0%} | {m['precision']:.0%} | {m['recall']:.0%} | {m['f1_score']:.0%} | {fp_count} | {fn_count} |"
        )
    lines += [""]

    # ── False Positives ───────────────────────────────────────────────────
    if fps:
        lines += [
            "## False Positives (legitimate flagged as scam)",
            "",
            "| ID | Category | Message |",
            "|---|---|---|",
        ]
        for r in fps:
            preview = r["message"][:100].replace("|", "/")
            lines.append(f"| {r['id']} | {r['category']} | {preview}... |")
        lines += [""]

    # ── False Negatives ───────────────────────────────────────────────────
    if fns:
        lines += [
            "## False Negatives (scam missed)",
            "",
            "| ID | Category | Message |",
            "|---|---|---|",
        ]
        for r in fns:
            preview = r["message"][:100].replace("|", "/")
            lines.append(f"| {r['id']} | {r['category']} | {preview}... |")
        lines += [""]

    # ── Errors ────────────────────────────────────────────────────────────
    if errors:
        lines += [
            "## Errors",
            "",
            "| ID | Error |",
            "|---|---|",
        ]
        for r in errors:
            lines.append(f"| {r['id']} | {r.get('error','?')[:120]} |")
        lines += [""]

    lines += [
        "---",
        "",
        "*Report generated by `tests/test_comprehensive.py`*",
    ]
    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Honey-Pot comprehensive evaluation")
    parser.add_argument("--dry-run", action="store_true", help="Preview without API calls")
    parser.add_argument("--max", type=int, default=0, help="Max messages to evaluate (0 = all)")
    parser.add_argument("--clear-cache", action="store_true", help="Delete cache and re-run")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY, help="Seconds between calls")
    parser.add_argument("--no-cache", action="store_true", help="Ignore existing cache entirely")
    args = parser.parse_args()

    if args.clear_cache and CACHE_PATH.exists():
        CACHE_PATH.unlink()
        print("Cache cleared.")

    dataset = load_dataset()
    cache = {} if args.no_cache else load_cache()

    # Filter to uncached messages
    uncached = [m for m in dataset if m["id"] not in cache]
    total_to_run = min(len(uncached), args.max) if args.max > 0 else len(uncached)
    run_messages = uncached[:total_to_run]

    print(f"Dataset: {len(dataset)} messages total")
    print(f"Cached:  {len(dataset) - len(uncached)} | Uncached: {len(uncached)}")
    print(f"Will evaluate: {len(run_messages)} | Delay: {args.delay}s")
    if args.dry_run:
        print("MODE: DRY RUN (no API calls)")
    print("-" * 60)

    # Run evaluations
    for i, msg in enumerate(run_messages):
        prefix = "[DRY] " if args.dry_run else ""
        print(
            f"  [{i+1}/{len(run_messages)}] {prefix}{msg['id']} "
            f"({msg['category']}, {msg['label']})...",
            end=" ",
        )
        result = evaluate_single(msg, cache, dry_run=args.dry_run)
        cache[msg["id"]] = result
        if args.dry_run:
            print("skipped")
        else:
            status = "ERR" if result.get("error") else ("SCAM" if result["predicted_scam"] else "CLEAN")
            print(f"{status}  ({result['response_time']}s, conf={result['confidence']:.2f})")
            if i < len(run_messages) - 1:
                time.sleep(args.delay)

    # Save cache
    if not args.dry_run:
        save_cache(cache)

    # Build full result list (from cache)
    all_results = []
    for msg in dataset:
        if msg["id"] in cache:
            entry = cache[msg["id"]].copy()
            entry["status"] = "cached" if msg["id"] not in {m["id"] for m in run_messages} else "new"
            all_results.append(entry)
        else:
            # Not evaluated (in dry-run or max-limited)
            all_results.append({
                "id": msg["id"],
                "label": msg["label"],
                "category": msg["category"],
                "message": msg["message"],
                "predicted_scam": False,
                "confidence": 0.0,
                "response_time": 0.0,
                "error": None,
                "status": "skipped",
            })

    # Metrics (only on evaluated entries)
    evaluated = [r for r in all_results if r["status"] in ("new", "cached")]
    cm = build_confusion_matrix(evaluated)
    global_metrics = compute_metrics(cm)
    cat_metrics = per_category_metrics(evaluated)

    cache_hits = sum(1 for r in evaluated if r["status"] == "cached")
    new_calls = sum(1 for r in evaluated if r["status"] == "new")

    # Print summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"Accuracy:   {global_metrics['accuracy']:.2%}")
    print(f"Precision:  {global_metrics['precision']:.2%}")
    print(f"Recall:     {global_metrics['recall']:.2%}")
    print(f"F1 Score:   {global_metrics['f1_score']:.2%}")
    print(f"FP Rate:    {global_metrics['false_positive_rate']:.2%}")
    print(f"FN Rate:    {global_metrics['false_negative_rate']:.2%}")
    print(f"Confusion:  TP={cm['TP']} TN={cm['TN']} FP={cm['FP']} FN={cm['FN']}")

    # Generate markdown report
    report = generate_report(
        evaluated, global_metrics, cat_metrics,
        dry_run=args.dry_run, cache_used=cache_hits, new_run=new_calls,
    )
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nReport saved: {REPORT_PATH}")

    # Budget warning
    used = cache_hits + new_calls
    remaining = MONTHLY_BUDGET - used
    if remaining < 100:
        print(f"\nWARNING: Only ~{remaining} API calls remaining in daily budget!")
    else:
        print(f"\nAPI budget: ~{remaining} calls remaining today.")

    return global_metrics


if __name__ == "__main__":
    main()
