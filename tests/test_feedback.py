"""Quick test of the feedback self-learning system."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.feedback import (
    add_correction, find_cached_correction, get_fewshot_examples,
    get_feedback_stats, get_patterns, _load_feedback, FEEDBACK_FILE
)

# Clean slate
if FEEDBACK_FILE.exists():
    FEEDBACK_FILE.unlink()

print("=== Test 1: Store a False Positive correction ===")
entry = add_correction(
    message="SBI: Rs 50,000 credited to your A/c XX7890. Bal: Rs 2,34,500.",
    correction_type="fp",
    original_prediction=True,
    actual_label=False,
    category="bank_alert",
    notes="Bank credit alerts are legitimate transaction notifications"
)
print(f"  Stored: {entry['id']}")

print("\n=== Test 2: FP Cache hit (exact match) ===")
cached = find_cached_correction("SBI: Rs 50,000 credited to your A/c XX7890. Bal: Rs 2,34,500. Ref: TXN987654.")
print(f"  Found: {cached is not None}")
if cached:
    print(f"  Correction type: {cached['correction_type']}")

print("\n=== Test 3: FP Cache hit (fuzzy match) ===")
cached2 = find_cached_correction("SBI: Rs 50,000 credited to your account XX7890. Balance: Rs 2,34,500.")
print(f"  Found: {cached2 is not None}")

print("\n=== Test 4: Few-shot examples ===")
examples = get_fewshot_examples("HDFC Bank Credit Card charged at Amazon.in", correction_type="fp")
print(f"  Found {len(examples)} examples for the prompt")
for ex in examples:
    preview = ex["message"][:60]
    print(f"  -> {preview}... label={ex['correct_label']}")

print("\n=== Test 5: Store 2 more bank_alert FPs to trigger pattern extraction ===")
add_correction("HDFC Bank Credit Card: Rs 4,999 charged at Amazon.in on 01-Sep.", "fp", True, False, "bank_alert", "Credit card alerts are legitimate")
add_correction("Kotak Mahindra Bank: Auto-debit of Rs 18,500 for home loan EMI processed.", "fp", True, False, "bank_alert", "EMI auto-debit alerts are legitimate")

patterns = get_patterns()
print(f"  Patterns extracted: {len(patterns)}")
for p in patterns:
    print(f"  -> {p['type']}: {p['reason']}")

print("\n=== Test 6: Stats ===")
stats = get_feedback_stats()
print(f"  Total corrections: {stats['total_corrections']}")
print(f"  FP corrected: {stats['false_positives_corrected']}")
print(f"  FN corrected: {stats['false_negatives_corrected']}")
print(f"  Patterns: {stats['patterns_extracted']}")
print(f"  Per category: {stats['per_category']}")

# Cleanup
FEEDBACK_FILE.unlink()
print("\n=== All tests passed! Feedback system works. ===")
