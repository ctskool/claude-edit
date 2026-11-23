"""Convert word timestamps to SRT.

Usage: python tools/words_srt.py <words.json> <out.srt> [--max-words 6] [--max-gap 0.6]
"""

import argparse
import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path


def nonnegative_seconds(value):
    try:
        seconds = Decimal(value)
    except InvalidOperation:
        raise argparse.ArgumentTypeError("must be a nonnegative number")
    if not seconds.is_finite() or seconds < 0:
        raise argparse.ArgumentTypeError("must be a finite nonnegative number")
    return seconds


def timestamp(seconds):
    milliseconds = int(
        (seconds * 1000).to_integral_value(rounding=ROUND_HALF_UP)
    )
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def build_cues(words, max_words, max_gap):
    cues = []
    pending = []

    for index, word in enumerate(words):
        pending.append(word)
        last_word = index == len(words) - 1
        boundary = (
            len(pending) >= max_words
            or word["text"].rstrip().endswith((".", "?", "!"))
        )
        if not last_word:
            gap = Decimal(words[index + 1]["start"]) - Decimal(word["end"])
            boundary = boundary or gap > max_gap

        if boundary or last_word:
            start = Decimal(pending[0]["start"])
            end = Decimal(pending[-1]["end"])
            if end <= start:
                end = start + Decimal("0.05")
            text = " ".join(item["text"] for item in pending)
            cues.append((start, end, text))
            pending = []

    for index in range(len(cues) - 1):
        start, end, text = cues[index]
        next_start = cues[index + 1][0]
        if end > next_start:
            cues[index] = (start, next_start, text)

    return cues


def main():
    parser = argparse.ArgumentParser(description="Convert word timestamps to SRT.")
    parser.add_argument("words_json", type=Path)
    parser.add_argument("out_srt", type=Path)
    parser.add_argument("--max-words", type=int, default=6)
    parser.add_argument("--max-gap", type=nonnegative_seconds, default=Decimal("0.6"))
    args = parser.parse_args()

    if args.max_words < 1:
        parser.error("--max-words must be at least 1")

    with args.words_json.open("r", encoding="utf-8") as source:
        words = json.load(source, parse_float=Decimal)

    cues = build_cues(words, args.max_words, args.max_gap)

    with args.out_srt.open("w", encoding="utf-8", newline="\n") as output:
        for number, (start, end, text) in enumerate(cues, start=1):
            output.write(
                f"{number}\n"
                f"{timestamp(start)} --> {timestamp(end)}\n"
                f"{text}\n\n"
            )

    print(f"{len(cues)} cues")


if __name__ == "__main__":
    main()
