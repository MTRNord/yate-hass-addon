#!/usr/bin/env python3
"""
Yate extmodule spam checker.

Communicates with Yate via stdin/stdout using the extmodule pipe protocol.
Intercepts call.route messages and rejects calls from known spam numbers.

Check order:
  1. Local BNetzA blocklist (fast, no network)
  2. shouldianswer.com live scrape (German community spam ratings)

Numbers that come back as "negative" on shouldianswer or appear in the
BNetzA enforcement list are rejected with error/forbidden.
"""

import json
import os
import re
import sys
import urllib.parse

import requests
from bs4 import BeautifulSoup

BNETZA_LIST_PATH = '/data/spam/bnetza_numbers.json'
USER_AGENT = (
    'Mozilla/5.0 (X11; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0'
)

blocked_numbers: set[str] = set()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def log(msg: str) -> None:
    sys.stderr.write(f'[spam_checker] {msg}\n')
    sys.stderr.flush()


def send(line: str) -> None:
    sys.stdout.write(line + '\n')
    sys.stdout.flush()


# ---------------------------------------------------------------------------
# Number normalisation
# ---------------------------------------------------------------------------

def normalize(number: str) -> str:
    """Normalise to German national format (leading 0, digits only)."""
    if not number:
        return ''
    number = re.sub(r'[\s\-\(\)]', '', number)
    if number.startswith('+49'):
        return '0' + number[3:]
    if number.startswith('0049'):
        return '0' + number[4:]
    return number


def to_e164(number: str) -> str:
    """Convert German national format to E.164 with + prefix for URL use."""
    if number.startswith('0') and not number.startswith('00'):
        return '+49' + number[1:]
    return number


# ---------------------------------------------------------------------------
# Blocklist loading
# ---------------------------------------------------------------------------

def load_bnetza() -> None:
    global blocked_numbers
    if not os.path.exists(BNETZA_LIST_PATH):
        log(f'No BNetzA list at {BNETZA_LIST_PATH} — local blocklist disabled')
        return
    with open(BNETZA_LIST_PATH) as f:
        data = json.load(f)
    blocked_numbers = set(data.get('numbers', []))
    updated = data.get('updated', 'unknown')
    log(f'Loaded {len(blocked_numbers)} BNetzA numbers (updated: {updated})')


# ---------------------------------------------------------------------------
# shouldianswer.com live check
# ---------------------------------------------------------------------------

def check_shouldianswer(number: str) -> str:
    """
    Returns one of: 'negative', 'positive', 'neutral', 'unknown'.
    Uses a Firefox User-Agent to avoid simple bot detection.
    """
    e164 = to_e164(number)
    url = 'https://www.shouldianswer.com/search?q=' + urllib.parse.quote(e164)
    try:
        resp = requests.get(
            url,
            headers={'User-Agent': USER_AGENT},
            timeout=5,
            allow_redirects=True,
        )
        if resp.status_code != 200:
            log(f'shouldianswer HTTP {resp.status_code} for {number}')
            return 'unknown'
        soup = BeautifulSoup(resp.text, 'html.parser')
        score_div = soup.select_one('.mainInfoHeader .scoreContainer .score')
        if not score_div:
            return 'unknown'
        classes = score_div.get('class', [])
        return classes[1] if len(classes) > 1 else 'unknown'
    except Exception as exc:
        log(f'shouldianswer check failed for {number}: {exc}')
        return 'unknown'


# ---------------------------------------------------------------------------
# Spam decision
# ---------------------------------------------------------------------------

def is_spam(caller: str) -> bool:
    normalized = normalize(caller)
    if not normalized or not normalized.startswith('0'):
        # Not a German number — skip both checks
        return False

    if normalized in blocked_numbers:
        log(f'BNetzA blocklist hit: {normalized}')
        return True

    rating = check_shouldianswer(normalized)
    log(f'shouldianswer: {normalized} → {rating}')
    return rating == 'negative'


# ---------------------------------------------------------------------------
# Yate extmodule protocol
# ---------------------------------------------------------------------------

def parse_params(parts: list[str]) -> dict[str, str]:
    params: dict[str, str] = {}
    for p in parts:
        if '=' in p:
            k, _, v = p.partition('=')
            params[urllib.parse.unquote(k)] = urllib.parse.unquote(v)
    return params


def handle_line(line: str) -> None:
    if not line.startswith('%%>message:'):
        return

    # %%>message:<id>:<time>:<name>:<retvalue>[:<key>=<value>]*
    parts = line.split(':')
    if len(parts) < 5:
        return

    msg_id = parts[1]
    msg_name = parts[3]
    retvalue = parts[4]
    params = parse_params(parts[5:])

    if msg_name != 'call.route':
        # Pass through anything we don't care about
        send(f'%%<message:{msg_id}:false:{msg_name}:{retvalue}')
        return

    caller = params.get('caller', '')
    called = params.get('called', '')
    log(f'call.route: caller={caller} called={called}')

    if caller and is_spam(caller):
        log(f'Rejecting spam call from {caller}')
        send(f'%%<message:{msg_id}:true:{msg_name}:error/forbidden')
    else:
        # Not spam — don't claim the message, let other handlers route normally
        send(f'%%<message:{msg_id}:false:{msg_name}:')


def main() -> None:
    load_bnetza()
    # Install handler for call.route at priority 10 (runs before default routing)
    # Priority 5 = runs before regexroute (which defaults to priority 10)
    send('%%>install:5:call.route')

    for raw in sys.stdin:
        line = raw.rstrip('\n\r')
        if line:
            handle_line(line)


if __name__ == '__main__':
    main()
