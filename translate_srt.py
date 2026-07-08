#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SRT HINGLISH TRANSLATOR - CLI (VPS EDITION)
---------------------------------------------
Terminal se seedha translate karne ke liye. API ke liye main.py use karo.

USAGE:
    python3 translate_srt.py input.srt output.srt
    python3 translate_srt.py input.srt output.srt --batch-chars 450 --delay 0.5
"""

import argparse
from translator import AnythingTranslateHinglish, translate_srt_content


def main():
    parser = argparse.ArgumentParser(description="SRT -> Hinglish translator (CLI)")
    parser.add_argument("input", help="Input .srt file")
    parser.add_argument("output", help="Output .srt file")
    parser.add_argument("--batch-chars", type=int, default=450,
                         help="Max characters per batch request (default: 450)")
    parser.add_argument("--delay", type=float, default=0.5,
                         help="Delay in seconds between requests (default: 0.5)")
    args = parser.parse_args()

    print(f"📖 Reading: {args.input}")
    with open(args.input, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    translator = AnythingTranslateHinglish()
    out, stats = translate_srt_content(
        content, translator, batch_chars=args.batch_chars, delay=args.delay
    )

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(out)

    print("\n" + "=" * 50)
    print("📊 FINAL REPORT")
    print("=" * 50)
    print(f"Total batches      : {stats['total_batches']}")
    print(f"✅ Clean matches    : {stats['batch_success']}")
    print(f"⚠️  Fallback batches : {stats['batch_fallback']}")
    print(f"❌ Failed lines     : {stats['line_fail']}")
    print(f"📁 Output saved to  : {args.output}")
    print("=" * 50)


if __name__ == "__main__":
    main()
