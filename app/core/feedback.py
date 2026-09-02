"""
Feedback-driven self-learning layer for scam detection.

Mechanisms:
1. FP Cache — stores corrected messages. Exact/near-match hits skip LLM entirely.
2. Few-shot Augmentation — injects relevant past corrections into the LLM prompt.
3. Pattern Extraction — learns rules like "bank shortcodes are legitimate".
"""

import json
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

FEEDBACK_DIR = Path(__file__).parent.parent.parent / "data"
FEEDBACK_FILE = FEEDBACK_DIR / "feedback.json"

# Similarity threshold for cache matching
SIMILARITY_THRESHOLD = 0.85
# Max few-shot examples to inject into prompt
MAX_FEWSHOT_EXAMPLES = 4


# ── Feedback Store ─────────────────────────────────────────────────────────────

def _load_feedback() -> dict:
    if FEEDBACK_FILE.exists():
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"corrections": [], "patterns": [], "stats": {"total": 0, "fp": 0, "fn": 0}}


def _save_feedback(data: dict):
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_correction(
    message: str,
    correction_type: str,  # "fp" or "fn"
    original_prediction: bool,
    actual_label: bool,
    category: str = "",
    notes: str = "",
) -> dict:
    """
    Store a human correction. FP = model said scam but it was legit.
    FN = model said legit but it was scam.
    """
    feedback = _load_feedback()

    entry = {
        "id": f"corr_{int(time.time()*1000)}",
        "message": message,
        "correction_type": correction_type,
        "original_prediction": original_prediction,
        "actual_label": actual_label,
        "category": category,
        "notes": notes,
        "timestamp": datetime.utcnow().isoformat(),
    }

    feedback["corrections"].append(entry)
    feedback["stats"]["total"] += 1
    if correction_type == "fp":
        feedback["stats"]["fp"] += 1
    elif correction_type == "fn":
        feedback["stats"]["fn"] += 1

    _save_feedback(feedback)
    _extract_patterns(feedback)

    logger.info(
        f"Correction stored: {correction_type.upper()}",
        extra={"message_preview": message[:60], "category": category},
    )
    return entry


# ── Similarity Matching ────────────────────────────────────────────────────────

def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def find_cached_correction(message: str) -> Optional[dict]:
    """
    Check if this message (or a very similar one) has been corrected before.
    Returns the correction entry if found, None otherwise.
    """
    feedback = _load_feedback()
    best_match = None
    best_score = 0.0

    for corr in feedback["corrections"]:
        score = _similarity(message, corr["message"])
        if score >= SIMILARITY_THRESHOLD and score > best_score:
            best_score = score
            best_match = corr

    if best_match:
        logger.info(
            f"FP cache hit (similarity={best_score:.2f})",
            extra={"cached_id": best_match["id"]},
        )
    return best_match


# ── Few-shot Example Builder ──────────────────────────────────────────────────

def get_fewshot_examples(message: str, correction_type: str = "fp") -> List[dict]:
    """
    Find the most relevant past corrections to inject into the LLM prompt.
    Returns up to MAX_FEWSHOT_EXAMPLES entries with message + corrected label.
    """
    feedback = _load_feedback()

    if not feedback["corrections"]:
        return []

    # Score each correction by relevance to current message
    scored = []
    for corr in feedback["corrections"]:
        if corr["correction_type"] != correction_type:
            continue
        sim = _similarity(message, corr["message"])
        scored.append((sim, corr))

    # Sort by similarity, take top N
    scored.sort(key=lambda x: -x[0])
    examples = []
    for sim, corr in scored[:MAX_FEWSHOT_EXAMPLES]:
        label = "legitimate" if corr["actual_label"] else "scam"
        examples.append({
            "message": corr["message"],
            "correct_label": label,
            "category": corr.get("category", ""),
            "reason": corr.get("notes", "Human corrected this classification"),
        })

    return examples


def build_fewshot_prompt_section(examples: List[dict]) -> str:
    """Build a prompt section with few-shot correction examples."""
    if not examples:
        return ""

    lines = [
        "\nIMPORTANT CORRECTIONS FROM HUMAN REVIEWERS:",
        "(The system previously misclassified these messages. Learn from these corrections.)",
        "",
    ]

    for i, ex in enumerate(examples, 1):
        lines.append(f"Example {i}:")
        lines.append(f'  Message: "{ex["message"][:150]}"')
        lines.append(f"  Correct label: {ex['correct_label']}")
        if ex.get("category"):
            lines.append(f"  Category: {ex['category']}")
        if ex.get("reason"):
            lines.append(f"  Why: {ex['reason']}")
        lines.append("")

    return "\n".join(lines)


# ── Pattern Extraction ─────────────────────────────────────────────────────────

def _extract_patterns(feedback: dict):
    """
    Extract recurring patterns from corrections.
    E.g., "bank shortcodes are legitimate", "OTP notifications are legitimate".
    """
    patterns = []
    corrections = feedback["corrections"]

    # Group FP corrections by category
    fp_by_category = {}
    for c in corrections:
        if c["correction_type"] == "fp":
            cat = c.get("category", "unknown")
            if cat not in fp_by_category:
                fp_by_category[cat] = []
            fp_by_category[cat].append(c)

    # Extract category-level patterns (3+ FPs in same category = pattern)
    for cat, fps in fp_by_category.items():
        if len(fps) >= 3:
            # Check if there's a common theme
            patterns.append({
                "type": "category_override",
                "category": cat,
                "action": "reduce_scam_score",
                "reason": f"{len(fps)} false positives in '{cat}' category — likely legitimate",
                "example_count": len(fps),
            })

    # Extract keyword patterns from FP messages
    fp_keywords = {}
    for c in corrections:
        if c["correction_type"] == "fp":
            words = c["message"].lower().split()
            for w in words:
                if len(w) > 4:  # Skip short words
                    fp_keywords[w] = fp_keywords.get(w, 0) + 1

    # Keywords appearing in 3+ FP messages = likely false trigger
    for word, count in fp_keywords.items():
        if count >= 3:
            patterns.append({
                "type": "keyword_override",
                "keyword": word,
                "action": "reduce_scam_score",
                "reason": f"'{word}' appears in {count} false positives — not a reliable scam indicator",
                "example_count": count,
            })

    feedback["patterns"] = patterns
    _save_feedback(feedback)


def get_patterns() -> List[dict]:
    """Get all extracted patterns."""
    feedback = _load_feedback()
    return feedback.get("patterns", [])


# ── Stats ──────────────────────────────────────────────────────────────────────

def get_feedback_stats() -> dict:
    """Get feedback statistics."""
    feedback = _load_feedback()
    stats = feedback.get("stats", {})
    corrections = feedback.get("corrections", [])

    # Per-category breakdown
    cat_stats = {}
    for c in corrections:
        cat = c.get("category", "unknown")
        if cat not in cat_stats:
            cat_stats[cat] = {"fp": 0, "fn": 0}
        cat_stats[cat][c["correction_type"]] += 1

    return {
        "total_corrections": stats.get("total", 0),
        "false_positives_corrected": stats.get("fp", 0),
        "false_negatives_corrected": stats.get("fn", 0),
        "patterns_extracted": len(feedback.get("patterns", [])),
        "per_category": cat_stats,
        "recent_corrections": [
            {
                "id": c["id"],
                "type": c["correction_type"],
                "message_preview": c["message"][:80],
                "category": c.get("category", ""),
                "timestamp": c.get("timestamp", ""),
            }
            for c in corrections[-10:]  # Last 10
        ],
    }


def get_all_corrections() -> List[dict]:
    """Get all stored corrections."""
    feedback = _load_feedback()
    return feedback.get("corrections", [])
