"""Lossless boundaries for marked messages; blank paragraphs as a fallback."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

NUMBERED = r"(?im)^\s*(?:(?:message|msg)\s*#?\s*\d+\b|#\s*\d+\b|\d{1,3}[.)]\s+)"
WA = (
    r"(?m)^[\u200e\u200f]*\[?(?P<date>\d{1,4}[/.-]\d{1,2}[/.-]\d{1,4})"
    r",?\s+\d{1,2}:\d{2}(?::\d{2})?(?:\s?[AaPp][Mm])?\]?\s*(?:-\s*)?"
    r"(?P<sender>[^:\r\n]+):"
)
EMAIL = r"(?im)^From:\s*(?P<sender>[^\r\n]+)"


DIALOGUE = r"(?im)^[ \t]*(?P<speaker>[A-Za-z0-9_\-]{2,20})\s*:\s+"


def clean_rtf(text: str) -> str:
    """Extract plain text from RTF content if present."""
    if not text.lstrip().startswith("{\\rtf"):
        return text
    t = re.sub(
        r"\{\\\*?[a-zA-Z]+.*?(?=(?:\\pard|\\[a-z]+[0-9]*\s+[A-Za-z0-9]))",
        "",
        text,
        flags=re.DOTALL,
    )
    t = re.sub(r"\\(?:par|line)\b\s*", "\n", t)
    t = t.replace("\\\r\n", "\n").replace("\\\n", "\n")
    t = re.sub(r"\\[a-zA-Z]+-?\d*\s?", "", t)
    t = re.sub(r"[{}]", "", t)
    lines = [l.strip() for l in t.splitlines() if l.strip()]
    return "\n".join(l for l in lines if not l.startswith(";") and not l.endswith(";"))


def segment(path: Path):
    raw = clean_rtf(path.read_bytes().decode("utf-8"))
    scan = raw.removeprefix("\ufeff")
    # Keep nested numbered lists in email/WhatsApp bodies. Explicit "Message N"
    # wrappers outrank the headers contained within each wrapper.
    wrappers = r"(?im)^[ \t]*(?:message|msg)\s*#?\s*\d+\b"
    explicit = [m.start() for m in re.finditer(wrappers, scan)]
    headers = sorted({m.start() for pat in (WA, EMAIL) for m in re.finditer(pat, scan)})
    numbered = [m.start() for m in re.finditer(NUMBERED, scan)]
    dialogue = [m.start() for m in re.finditer(DIALOGUE, scan)]
    if explicit:
        starts = explicit
    elif (
        headers
        and numbered
        and numbered[0] < headers[0]
        and not scan[: numbered[0]].strip()
    ):
        starts = numbered
    elif headers or numbered:
        starts = headers or numbered
    elif dialogue:
        starts = dialogue
    else:
        starts = [m.end() for m in re.finditer(r"\r?\n[ \t]*\r?\n+", scan)]
    offset = len(raw) - len(scan)
    cuts = [0] + [i + offset for i in starts if scan[:i].strip()] + [len(raw)]
    messages = []
    for lo, hi in zip(cuts, cuts[1:]):
        text = raw[lo:hi]
        if not text.strip().strip("\ufeff"):
            continue
        normalized = re.sub(r"\s+", " ", text.lstrip("\ufeff").strip())
        content = re.sub(
            r"^(?:(?:message|msg)\s*#?\s*\d+\b|#\s*\d+\b|\d{1,3}[.)]\s+)[:. \t-]*",
            "",
            normalized,
            count=1,
            flags=re.I,
        )
        fingerprint = hashlib.sha256(content.encode()).hexdigest()
        wa = re.search(WA, text)
        speaker_match = re.match(r"(?i)^[ \t]*([A-Za-z0-9_\-]{2,20})\s*:\s*", text)
        sender = (
            wa
            or re.search(EMAIL, text)
            or ({"sender": speaker_match.group(1)} if speaker_match else None)
        )
        date = re.search(r"(?im)^Date:\s*([^\r\n]+)", text)
        messages.append(
            {
                "raw": text,
                "fingerprint": fingerprint,
                "sender": sender["sender"].strip() if sender else None,
                "date": wa["date"] if wa else date[1].strip() if date else None,
            }
        )
    return messages
