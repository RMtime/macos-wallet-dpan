# macos-wallet-dpan

**Resolve the Apple Pay verification deadlock on macOS—when a bank asks for the Device Account Number (DPAN) suffix that Wallet does not show until verification.**

> **Experimental.** This tool can display a DPAN suffix **only when it is already stored in accessible local macOS Wallet metadata**. It does not activate a card, create a payment token, bypass issuer verification, or guarantee support for pending cards.

## Why?

Some banks ask for the last four digits of an Apple Pay *Device Account Number* during phone verification. macOS may hide the card details until verification has completed: a circular dependency. This tool looks for a previously provisioned DPAN suffix in the local Wallet SQLite database.

The **DPAN suffix** is not the physical or virtual bank card's **FPAN suffix**. Never substitute one for the other without your bank's instructions.

## Requirements

- macOS with a locally provisioned Apple Pay card
- Python 3.9+ (standard library only)
- Access to `~/Library/Passes/passes23.sqlite` on your own Mac

Tested against a reported schema containing `pass` and `payment_application` tables; not yet broadly verified across macOS versions.

## Use

Download `wallet_dpan.py` from this repository, then run:

```bash
python3 wallet_dpan.py --list
python3 wallet_dpan.py
```

The first command shows indexed cards and whether a suffix is stored, **without displaying DPAN digits**. The second offers an interactive choice and asks before revealing the suffix. For explicit non-interactive use:

```bash
python3 wallet_dpan.py --index 1 --reveal
```

**Do not paste actual DPAN/FPAN suffixes, full wallet database files, or terminal output revealing payment data into public issues.**

## How it works

- Opens `passes23.sqlite` with SQLite `mode=ro` and `PRAGMA query_only=ON`.
- Joins `pass.pid` to `payment_application.pass_pid`.
- Reads only `primary_account_suffix`, `fpan_suffix`, and `dpan_suffix`, not full card numbers, payment cryptograms, or keys.
- Optionally labels cards using local `pass.json` descriptions and FPAN last four, but leaves ambiguous matches unidentified.
- Performs no network calls and writes no Wallet files.

The `--db` and `--cards-dir` options exist for fixture-based tests, not for handling databases obtained from other people.

## Limitations

- If the DPAN suffix is not locally stored, the tool cannot recover it.
- The Wallet schema is private and may change; unsupported versions produce errors.
- A matching FPAN suffix is not a unique card identifier. Confirm the selected card carefully.
- A stored DPAN suffix does **not** establish that a card is activated or that your bank will accept it.
- Using a DPAN suffix for issuer verification must follow the bank's official process.

## Privacy and security

Offline and read-only. The DPAN suffix can be used by a bank for identity verification, so treat even four digits as sensitive. Never run modified copies from untrusted sources. See [SECURITY.md](SECURITY.md).

## Chinese documentation

[简体中文 README](README.zh-CN.md)

## Disclaimer

Independent community tool; not affiliated with, endorsed by, or supported by Apple, Mastercard, Visa, or any issuing bank. Use on your own device and at your own risk.
