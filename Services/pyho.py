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


import unittest

class TestFeedbackFunctions(unittest.TestCase):

    def test_sentiment_score(self):
        self.assertEqual(sentiment_score("good"), 1.0)
        self.assertEqual(sentiment_score("bad"), -1.0)
        self.assertEqual(sentiment_score("good bad"), 0.0)
        self.assertEqual(sentiment_score("good good"), 1.0)
        self.assertEqual(sentiment_score("bad bad"), -1.0)
        self.assertEqual(sentiment_score("This is good."), 1.0)
        self.assertEqual(sentiment_score("This is bad!"), -1.0)
        self.assertEqual(sentiment_score(""), 0.0)
        self.assertEqual(sentiment_score("neutral"), 0.0)

    def test_generate_feedback(self):
        feedbacks = generate_feedback(5)
        self.assertEqual(len(feedbacks), 5)
        for feedback in feedbacks:
            self.assertTrue(isinstance(feedback.id, int))
            self.assertTrue(isinstance(feedback.text, str))
            self.assertTrue(isinstance(feedback.score, float))
            self.assertTrue(-1.0 <= feedback.score <= 1.0)

    def test_summarize(self):
        # Test case 1: Empty list
        feedbacks1 = []
        summary1 = summarize(feedbacks1)
        self.assertEqual(summary1["count"], 0)
        self.assertEqual(summary1["average_score"], 0.0)
        self.assertEqual(summary1["positive"], 0)
        self.assertEqual(summary1["negative"], 0)
        self.assertEqual(summary1["neutral"], 0)

        # Test case 2: List with positive, negative and neutral feedbacks
        feedbacks2 = [
            Feedback(id=1, text="good", score=1.0),
            Feedback(id=2, text="bad", score=-1.0),
            Feedback(id=3, text="neutral", score=0.0)
        ]
        summary2 = summarize(feedbacks2)
        self.assertEqual(summary2["count"], 3)
        self.assertEqual(summary2["average_score"], 0.0)
        self.assertEqual(summary2["positive"], 1)
        self.assertEqual(summary2["negative"], 1)
        self.assertEqual(summary2["neutral"], 1)

    def test_feedback_to_dict(self):
        feedback = Feedback(id=1, text="test", score=0.5)
        feedback_dict = feedback.to_dict()
        self.assertEqual(feedback_dict["id"], 1)
        self.assertEqual(feedback_dict["text"], "test")
        self.assertEqual(feedback_dict["score"], 0.5)


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)