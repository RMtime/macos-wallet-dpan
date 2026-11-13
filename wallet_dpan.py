#!/usr/bin/env python3
"""Inspect local macOS Wallet metadata for Apple Pay DPAN suffixes.

Offline, read-only, standard-library-only. Does not access Secure Element keys.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3
import sys


DEFAULT_DB = Path.home() / "Library/Passes/passes23.sqlite"
DEFAULT_CARDS = Path.home() / "Library/Passes/Cards"


class WalletError(Exception):
    """Expected database, schema, or filesystem error."""


@dataclass(frozen=True)
class WalletCard:
    name: str
    fpan_suffix: str
    dpan_suffix: str | None
    pass_pid: int


def _suffix(value: object) -> str | None:
    """Accept short suffixes only; never treat a full PAN as a suffix."""
    if isinstance(value, (bytes, bytearray, memoryview)) or value is None:
        return None
    digits = str(value).strip()
    if not digits.isascii() or not digits.isdigit() or not 1 <= len(digits) <= 5:
        return None
    return digits.zfill(4)


def _local_names(cards_dir: Path) -> dict[str, set[str]]:
    """Map FPAN last-four to potential labels; ambiguity is handled later."""
    results: dict[str, set[str]] = {}
    if not cards_dir.is_dir():
        return results

    for path in cards_dir.rglob("pass.json"):
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if not isinstance(document, dict):
            continue
        suffix = _suffix(document.get("primaryAccountSuffix"))
        if suffix is None:
            continue
        parts = []
        for key in ("description", "organizationName"):
            value = document.get(key)
            if isinstance(value, str):
                value = " ".join(value.split()).strip()
                if value and value not in parts:
                    parts.append(value)
        if parts:
            results.setdefault(suffix[-4:], set()).add(" / ".join(parts))
    return results


def read_cards(db_path: Path, cards_dir: Path) -> list[WalletCard]:
    """Read only suffix fields from Wallet's local SQLite database."""
    if not db_path.is_file():
        raise WalletError(f"Wallet database not found: {db_path}")

    try:
        connection = sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True)
        try:
            connection.execute("PRAGMA query_only=ON")
            required = {
                "pass": {"pid", "primary_account_suffix"},
                "payment_application": {"pass_pid", "fpan_suffix", "dpan_suffix"},
            }
            for table, columns in required.items():
                actual = {
                    row[1] for row in connection.execute(
                        f'PRAGMA table_info("{table}")'
                    )
                }
                if not columns.issubset(actual):
                    raise WalletError(
                        f"Unsupported Wallet schema: {table} is missing "
                        + ", ".join(sorted(columns - actual))
                    )

            rows = connection.execute("""
                SELECT p.pid, p.primary_account_suffix,
                       pa.fpan_suffix, pa.dpan_suffix
                FROM pass AS p
                LEFT JOIN payment_application AS pa ON pa.pass_pid = p.pid
                WHERE p.primary_account_suffix IS NOT NULL
                   OR pa.fpan_suffix IS NOT NULL
                ORDER BY p.pid
            """).fetchall()
        finally:
            connection.close()
    except sqlite3.Error as exc:
        raise WalletError(f"Could not read Wallet database: {exc}") from exc

    candidates: list[tuple[int, str, str | None]] = []
    for pid, pass_suffix, app_suffix, dpan in rows:
        fpan = _suffix(pass_suffix) or _suffix(app_suffix)
        if fpan is None:
            continue
        candidates.append((pid, fpan[-4:], _suffix(dpan)))

    names = _local_names(cards_dir)
    occurrences = Counter(fpan for _, fpan, _ in candidates)
    cards: list[WalletCard] = []
    for pid, fpan, dpan in candidates:
        possible_names = names.get(fpan, set())
        # Never assign a name by last-four when the match is ambiguous.
        name = (
            next(iter(possible_names))
            if len(possible_names) == 1 and occurrences[fpan] == 1
            else "Unidentified payment card"
        )
        cards.append(WalletCard(name, fpan, dpan, pid))
    return cards


def list_cards(cards: list[WalletCard]) -> None:
    for index, card in enumerate(cards, 1):
        available = "stored" if card.dpan_suffix else "not stored"
        print(
            f"{index:>2}. {card.name}  "
            f"(card ending {card.fpan_suffix}; DPAN suffix {available})"
        )


def show_suffix(card: WalletCard) -> int:
    if card.dpan_suffix is None:
        print("No device account suffix is stored for this payment application.")
        print("This tool cannot generate a DPAN or complete bank verification.")
        return 1
    print(f"Device Account Number (DPAN) last four: {card.dpan_suffix[-4:]}")
    print("Treat these digits as bank verification data; do not share them.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Find a locally stored Apple Pay DPAN suffix on macOS."
    )
    parser.add_argument("--list", action="store_true", help="List cards without showing DPAN digits")
    parser.add_argument("--index", type=int, metavar="N", help="Select 1-based card index")
    parser.add_argument("--reveal", action="store_true", help="Reveal DPAN suffix for --index")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help=argparse.SUPPRESS)
    parser.add_argument("--cards-dir", type=Path, default=DEFAULT_CARDS, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if args.reveal and args.index is None:
        parser.error("--reveal requires --index N")

    try:
        cards = read_cards(args.db.expanduser(), args.cards_dir.expanduser())
    except WalletError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if not cards:
        print("No payment card metadata found in this Wallet database.")
        return 1

    list_cards(cards)
    if args.list:
        return 0

    if args.index is not None:
        selection = args.index
        if not args.reveal:
            print("Add --reveal to show this card's DPAN suffix.")
            return 0
    else:
        if not sys.stdin.isatty():
            print("In non-interactive mode, use --index N --reveal.", file=sys.stderr)
            return 2
        try:
            selection = int(input("Select card number (0 to cancel): "))
        except (EOFError, KeyboardInterrupt, ValueError):
            print("\nCancelled.")
            return 1
        if selection == 0:
            return 0
        try:
            answer = input("Reveal its DPAN suffix locally? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.")
            return 1
        if answer not in ("y", "yes"):
            print("Cancelled.")
            return 0

    if not 1 <= selection <= len(cards):
        print("Invalid card index.", file=sys.stderr)
        return 2
    return show_suffix(cards[selection - 1])


if __name__ == "__main__":
    raise SystemExit(main())
