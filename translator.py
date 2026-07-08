#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CORE TRANSLATION LOGIC
------------------------
Shared by both translate_srt.py (CLI) and main.py (FastAPI).
Engine: anythingtranslate.com Hinglish translator
Batching: character-count based, with automatic per-line fallback.
"""

import re
import time
import requests
from typing import List, Tuple, Optional


class AnythingTranslateHinglish:
    def __init__(self):
        self.api_url = "https://anythingtranslate.com/wp-admin/admin-ajax.php"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://anythingtranslate.com',
            'Referer': 'https://anythingtranslate.com/translators/hinglish-translator/',
            'X-Requested-With': 'XMLHttpRequest'
        })
        self.nonce = self._get_nonce()
        self.post_id = "44729"

    def _get_nonce(self) -> str:
        try:
            r = self.session.get(
                "https://anythingtranslate.com/translators/hinglish-translator/",
                timeout=20
            )
            if r.status_code == 200:
                m = re.search(r'translator_nonce["\']?\s*:\s*["\']([^"\']+)["\']', r.text)
                if m:
                    return m.group(1)
                m = re.search(r'<input[^>]*name="translator_nonce"[^>]*value="([^"]+)"', r.text)
                if m:
                    return m.group(1)
        except Exception as e:
            print(f"⚠️  Nonce fetch failed: {e}")
        return "e12398a074"  # fallback, may be expired

    def translate_raw(self, text: str) -> Optional[str]:
        try:
            data = {
                'action': 'do_translation',
                'translator_nonce': self.nonce,
                'post_id': self.post_id,
                'to_translate': text,
                'translation_model': 'newest',
                'is_language_swapped': '0'
            }
            r = self.session.post(self.api_url, data=data, timeout=90)
            if r.status_code == 200:
                result = r.json()
                if result.get('success'):
                    return result.get('data') or None
                print(f"   ❌ API error: {result.get('data')}")
                return None
            print(f"   ❌ HTTP {r.status_code}")
            return None
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
            return None


# ------------------------------------------------------------------
def is_srt_index_line(line: str) -> bool:
    return line.strip().isdigit()


def is_srt_time_line(line: str) -> bool:
    return bool(re.match(
        r"^\d{2}:\d{2}:\d{2}[,.]\d{3}\s-->\s\d{2}:\d{2}:\d{2}[,.]\d{3}", line.strip()
    ))


def build_batches(lines: List[str], translatable_idx: List[int],
                   batch_chars: int) -> List[List[Tuple[int, str]]]:
    batches = []
    cur: List[Tuple[int, str]] = []
    cur_len = 0

    for idx in translatable_idx:
        text = lines[idx].strip()
        add_len = len(text) + 1

        if cur and cur_len + add_len > batch_chars:
            batches.append(cur)
            cur = []
            cur_len = 0

        cur.append((idx, text))
        cur_len += add_len

    if cur:
        batches.append(cur)

    return batches


def translate_srt_content(content: str, translator: AnythingTranslateHinglish,
                           batch_chars: int = 450, delay: float = 0.5) -> Tuple[str, dict]:

    lines = content.splitlines()
    translated = lines[:]

    translatable_idx = []
    for i, line in enumerate(lines):
        s = line.strip()
        if not s:
            continue
        if is_srt_index_line(s):
            continue
        if is_srt_time_line(s):
            continue
        translatable_idx.append(i)

    batches = build_batches(lines, translatable_idx, batch_chars)

    stats = {
        'total_batches': len(batches),
        'batch_success': 0,
        'batch_fallback': 0,
        'line_fail': 0,
    }

    print(f"📊 {len(translatable_idx)} translatable lines -> {len(batches)} batches "
          f"(~{batch_chars} chars each)")

    for b_num, batch in enumerate(batches, 1):
        batch_text = "\n".join(t for _, t in batch)
        print(f"🔄 Batch {b_num}/{len(batches)} — {len(batch)} lines, {len(batch_text)} chars")

        result_text = translator.translate_raw(batch_text)
        parts = result_text.split("\n") if result_text else []

        if result_text and len(parts) == len(batch):
            for (idx, _), new_line in zip(batch, parts):
                translated[idx] = new_line
            stats['batch_success'] += 1
        else:
            print(f"   ⚠️  Mismatch — falling back to per-line translation")
            stats['batch_fallback'] += 1
            for idx, text in batch:
                one = translator.translate_raw(text)
                if one:
                    translated[idx] = one
                else:
                    stats['line_fail'] += 1
                time.sleep(delay)

        time.sleep(delay)

    return "\n".join(translated) + "\n", stats
