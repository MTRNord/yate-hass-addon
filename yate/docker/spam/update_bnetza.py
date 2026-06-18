#!/usr/bin/env python3
"""
Download and parse BNetzA Maßnahmenliste PDFs to build a local spam blocklist.
Saves extracted German phone numbers to OUTPUT_PATH as JSON.
Run at container startup to keep the list fresh.
"""

import io
import json
import os
import re
import sys
from datetime import datetime

import requests
from pdfminer.high_level import extract_text

OUTPUT_PATH = '/data/spam/bnetza_numbers.json'
BASE_URL = (
    'https://www.bundesnetzagentur.de/SharedDocs/Downloads/DE/'
    'Sachgebiete/Telekommunikation/Verbraucher/Rufnummernmissbrauch/'
    'Massnahmenlisten/'
)
USER_AGENT = (
    'Mozilla/5.0 (X11; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0'
)

# German phone numbers in national format (leading 0)
PHONE_RE = re.compile(r'\b0\d{6,14}\b')
# Ranges like "015201358219 bis 015201358399"
RANGE_RE = re.compile(r'\b(0\d{6,14})\s+bis\s+(0\d{6,14})\b')


def fetch_pdf(url: str) -> bytes:
    resp = requests.get(
        url,
        headers={'User-Agent': USER_AGENT},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.content


def extract_numbers(text: str) -> set[str]:
    numbers: set[str] = set()

    # Expand numeric ranges before single-number pass
    for m in RANGE_RE.finditer(text):
        start, end = int(m.group(1)), int(m.group(2))
        if 0 < end - start < 10_000:
            for n in range(start, end + 1):
                numbers.add(str(n))
        else:
            numbers.add(m.group(1))
            numbers.add(m.group(2))
    text = RANGE_RE.sub(' ', text)

    for m in PHONE_RE.finditer(text):
        numbers.add(m.group(0))

    return numbers


def main() -> None:
    current_year = datetime.now().year
    all_numbers: set[str] = set()

    for year in (current_year, current_year - 1):
        # BNetzA uses "Maßnahmenliste" (ß = %C3%9F) — try both encodings
        filenames = [
            f'Ma%C3%9Fnahmenliste{year}.pdf',
            f'Massnahmenliste{year}.pdf',
        ]
        for filename in filenames:
            url = BASE_URL + filename
            try:
                print(f'Fetching {url}')
                pdf_bytes = fetch_pdf(url)
                text = extract_text(io.BytesIO(pdf_bytes))
                numbers = extract_numbers(text)
                print(f'  {year}: {len(numbers)} numbers extracted')
                all_numbers.update(numbers)
                break
            except Exception as exc:
                print(f'  Failed ({exc})', file=sys.stderr)

    if not all_numbers:
        print('WARNING: No numbers extracted from any PDF', file=sys.stderr)
        sys.exit(1)

    print(f'Total unique numbers: {len(all_numbers)}')

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(
            {
                'updated': datetime.now().isoformat(),
                'count': len(all_numbers),
                'numbers': sorted(all_numbers),
            },
            f,
        )
    print(f'Saved to {OUTPUT_PATH}')


if __name__ == '__main__':
    main()
