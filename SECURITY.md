# Security policy

This project accesses sensitive *local* macOS Wallet metadata. It must be run only on devices and payment cards you are authorized to inspect.

## Data handling

- No telemetry, networking, or third-party packages.
- SQLite connection is opened with `mode=ro` and `PRAGMA query_only=ON`.
- The program selects suffix columns only. It never requests a full PAN, cryptogram, secure element key, CVV, or OTP.
- DPAN suffixes are displayed only after explicit selection or the `--reveal` option. **A four-digit suffix may still be used by banks as a verification factor.**

## Reporting security issues

Do not post real payment suffixes, `pass.json`, SQLite databases, terminal screenshots showing card data, or account details in public issues. Describe a finding using synthetic data and reproduction steps. If your report requires confidential evidence, contact the maintainer privately via their GitHub profile before sending anything.

## Scope

This is a diagnostic metadata viewer, **not** an activation or verification bypass. Unsupported Apple Wallet schemas may fail. The source is provided without warranty.
