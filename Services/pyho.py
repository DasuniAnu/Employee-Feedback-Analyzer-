from dataclasses import dataclass, asdict
from typing import List, Dict
import random
import json
import argparse
import sys

# pyho.py
# Random Python utility for generating and lightly analyzing "employee feedback" samples.
# Intended as a small, self-contained helper for testing.


POSITIVE_WORDS = [
    "good", "great", "excellent", "positive", "helpful", "productive",
    "supportive", "improved", "happy", "satisfied", "clear", "efficient"
]
NEGATIVE_WORDS = [
    "bad", "terrible", "poor", "negative", "unhelpful", "slow",
    "frustrating", "worse", "angry", "dissatisfied", "unclear", "inefficient"
]
NEUTRAL_PHRASES = [
    "needs attention", "more context", "follow-up required",
    "no change observed", "as expected", "for review"
]

SAMPLE_SUBJECTS = [
    "workload", "communication", "management", "tooling",
    "onboarding", "workflow", "documentation", "review process"
]


@dataclass
class Feedback:
    id: int
    text: str
    score: float  # -1.0 (very negative) .. 1.0 (very positive)

    def to_dict(self) -> Dict:
        return asdict(self)


def random_sentence() -> str:
    """Create a short random feedback sentence."""
    subject = random.choice(SAMPLE_SUBJECTS)
    template_type = random.choices(["pos", "neg", "neutral"], weights=(45, 35, 20), k=1)[0]
    if template_type == "pos":
        word = random.choice(POSITIVE_WORDS)
        return f"The {subject} is {word} and improving."
    elif template_type == "neg":
        word = random.choice(NEGATIVE_WORDS)
        return f"The {subject} has been {word} lately."
    else:
        phrase = random.choice(NEUTRAL_PHRASES)
        return f"The {subject} {phrase}."


def sentiment_score(text: str) -> float:
    """
    Very small heuristic sentiment scoring:
    +1 for each positive word, -1 for each negative word, normalized to [-1, 1].
    """
    tokens = [t.strip(".,!?:;").lower() for t in text.split()]
    pos = sum(1 for t in tokens if t in POSITIVE_WORDS)
    neg = sum(1 for t in tokens if t in NEGATIVE_WORDS)
    if pos == 0 and neg == 0:
        return 0.0
    raw = pos - neg
    # normalize by possible magnitude
    norm = raw / max(1, (pos + neg))
    return max(-1.0, min(1.0, norm))


def generate_feedback(n: int = 10) -> List[Feedback]:
    """Generate n random Feedback objects."""
    items: List[Feedback] = []
    for i in range(1, n + 1):
        text = random_sentence()
        score = sentiment_score(text)
        items.append(Feedback(id=i, text=text, score=score))
    return items


def summarize(feedbacks: List[Feedback]) -> Dict:
    """Return a brief summary of sentiment distribution."""
    if not feedbacks:
        return {"count": 0, "average_score": 0.0, "positive": 0, "negative": 0, "neutral": 0}
    avg = sum(f.score for f in feedbacks) / len(feedbacks)
    pos = sum(1 for f in feedbacks if f.score > 0)
    neg = sum(1 for f in feedbacks if f.score < 0)
    neu = len(feedbacks) - pos - neg
    return {
        "count": len(feedbacks),
        "average_score": round(avg, 3),
        "positive": pos,
        "negative": neg,
        "neutral": neu
    }


def save_to_json(feedbacks: List[Feedback], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump([fb.to_dict() for fb in feedbacks], f, indent=2, ensure_ascii=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate random feedback samples (pyho).")
    parser.add_argument("-n", "--count", type=int, default=10, help="Number of feedback items to generate")
    parser.add_argument("-o", "--out", type=str, help="Optional output JSON file")
    args = parser.parse_args(argv)

    items = generate_feedback(args.count)
    summary = summarize(items)

    print("Generated feedback:")
    for f in items:
        print(f"- [{f.id}] score={f.score:+.2f}  {f.text}")
    print("\nSummary:", summary)

    if args.out:
        save_to_json(items, args.out)
        print(f"Saved {len(items)} items to {args.out}")


if __name__ == "__main__":
    main(sys.argv[1:])