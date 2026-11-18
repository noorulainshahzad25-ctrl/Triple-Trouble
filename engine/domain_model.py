"""Small supervised domain classifier for triage when extraction fails.

Train with: python -m engine.domain_model PACK.txt LABELS.json MODEL.json
Labels are arrays of domains in file order. Training uses leave-one-message-out
micro-F1 to select a feature set. The model never contributes claims to the solver.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

from .ingest import segment


def features(raw, mode):
    text = re.sub(r"(?im)^(?:date:|message\s+\d).*?$", " ", raw.casefold())
    words = re.findall(r"[^\W\d_]+", text)
    # Function words carry little topical information across unrelated senders.
    stop = set(
        "a an as at be by can for from have here i in is it me of on or our per the this to we will with your email whatsapp rs".split()
    )
    words = [w for w in words if w not in stop]
    terms = set(words)
    if mode == "subword":
        for w in words:
            framed = "^" + w + "$"
            terms.update("~" + framed[i : i + 3] for i in range(len(framed) - 2))
    return {hashlib.blake2s(t.encode(), digest_size=6).hexdigest() for t in terms}


def fit(samples, mode):
    docs = [(features(raw, mode), labels) for raw, labels in samples]
    df = Counter(term for terms, _ in docs for term in terms)
    idf = {t: 1 + math.log((1 + len(docs)) / (1 + n)) for t, n in df.items()}
    centroids = defaultdict(Counter)
    for terms, labels in docs:
        norm = math.sqrt(sum(idf[t] ** 2 for t in terms)) or 1
        for label in labels:
            for t in terms:
                centroids[label][t] += idf[t] / norm
    weights = {}
    for label, vec in centroids.items():
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1
        weights[label] = {t: round(v * idf[t] / norm, 6) for t, v in vec.items()}
    return {"mode": mode, "weights": weights}


def predict(raw, model):
    terms = features(raw, model["mode"])
    scores = {
        label: sum(vec.get(t, 0) for t in sorted(terms))
        for label, vec in model["weights"].items()
    }
    peak = max(scores.values(), default=0)
    return sorted(
        label
        for label, s in scores.items()
        if peak > 0 and s >= peak * model["threshold"]
    )


def train(samples):
    best = None
    for mode in ("word", "subword"):
        folds = [fit(samples[:i] + samples[i + 1 :], mode) for i in range(len(samples))]
        for threshold in (0.5, 0.75, 0.95):
            tp = fp = fn = 0
            for (raw, labels), model in zip(samples, folds):
                actual = set(predict(raw, dict(model, threshold=threshold)))
                tp += len(actual & set(labels))
                fp += len(actual - set(labels))
                fn += len(set(labels) - actual)
            score = 2 * tp / max(1, 2 * tp + fp + fn)
            if best is None or score > best[0]:
                best = score, mode, threshold
    score, mode, threshold = best
    return dict(
        fit(samples, mode),
        threshold=threshold,
        training_examples=len(samples),
        selection_micro_f1=round(score, 4),
    )


def triage(raw):
    model = json.loads(
        Path(__file__).with_name("domain_model.json").read_text(encoding="utf-8")
    )
    return predict(raw, model)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("pack", "labels", "output"):
        parser.add_argument(arg, type=Path)
    args = parser.parse_args()
    rows = segment(args.pack)
    labels = json.loads(args.labels.read_text(encoding="utf-8"))
    if len(rows) != len(labels) or len(rows) < 2:
        parser.error("Supply one label array per message and at least two messages.")
    samples = [(row["raw"], label) for row, label in zip(rows, labels)]
    args.output.write_text(
        json.dumps(train(samples), sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
