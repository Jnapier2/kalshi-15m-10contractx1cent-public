# Kalshi 10×1¢ Public Edition

An offline educational planner demonstrating scoped funding checks, evidence-quality review, contradiction handling, and duplicate-intent prevention. It has no credentials, network access, or order authority.

## Try the demonstration

Python 3.11 or newer is required. There are no third-party runtime packages, accounts, keys, installations, or network calls.

```console
python -I -S -B run_buy_planner.py --demo
python -I -S -B run_buy_planner.py --menu
python -I -S -B run_buy_planner.py --verify
python -I -S -B run_buy_planner.py examples/conflict_snapshot.json
python -I -S -B public_support.py --export
python -B -m unittest discover -s tests -v
```

Windows: `Kalshi10x1cPublic.bat` runs the demo; add `--menu` for grouped Explore and Support actions. `Kalshi10x1cPublic_Export.bat` calls the standalone support module, not the main application. Both use their own directory rather than the caller's working directory. They never install software, elevate privileges, or change security settings.

## What it demonstrates

The fixed public profile remains **10 whole contracts at 1¢ each**, or 10¢ principal before explicitly supplied synthetic entry fees. Checks cover scoped funding, complete and fresh evidence, price-grid support, final supplied-book crossing, existing exposure, route and scope contradictions, and duplicate intents.

An optional `analysis_evidence` object demonstrates ordered research checks: independent responses, complete history, evidence age, fee-complete lifecycle, and chronological holdout. Fewer than six supplied independent responses produces a neutral review. Incomplete or stale research blocks only that review, not an otherwise valid plan. `READY_FOR_REVIEW` is not statistical validation or permission to promote a model.

**Public-model distinction:** this title and teaching profile are intentionally preserved. They are not the private source's current trading-price configuration. This release demonstrates selected validation ideas from v69.99; it does not publish or claim full equivalence with its live engine, history refresh worker, learned ranking, or persistent state.

## Inputs and results

The default fixture includes the optional review object. All core quantities and ages are bounded integers; booleans must actually be booleans. Supplied market/status/fee ages above 30 seconds block planning. These are stated ages, not independently authenticated timestamps.

Inputs must be explicitly synthetic and use `SYNTHETIC-` identifiers. Unknown fields, conflicting scopes, duplicate JSON keys, non-finite values, malformed numbers, oversized inputs and non-regular input files are rejected. Do not provide private account exports. Snapshot values are assertions supplied by the caller; this tool cannot establish real exchange truth.

Results are `PLAN`, `HOLD`, `QUARANTINE`, `INVALID`. `PLAN` is educational output without execution authority. Duplicate protection compares deterministic IDs with supplied prior IDs and exposure evidence; it is not a durable order ledger or multi-process trading guarantee.

## Privacy and integrity

There is no credential loader, transport, request signer, account access, order submission, cancellation, fund movement or hidden live switch. Only reviewed public source, synthetic fixtures, tests and documentation are included; private source archives are not redistributed.

The canonical entrypoint requires isolated/no-site/no-bytecode Python. It verifies exact managed payload hashes and package identity before planner imports, and checks the independent support helper against a built-in digest. Downloaded bootstrap code and the Python runtime still require a trusted source. A manifest is not a publisher signature and does not defeat an attacker replacing all code and trust records.

Support exports contain **four generated safe records**, never inputs, logs, source, credentials or environment values. Files stay under `outputs/support/`. Critical integrity failures attempt an atomic capsule followed by a ZIP using already trusted support code. Unknown input or ordinary cancellation does not trigger Critical capture. `CAPSULE_ONLY`, unavailable and successful minimal capture remain distinct.

Exports use a same-machine lock, 32 KiB per-file/ZIP bound, one MiB free-space minimum and a 64-attempt persistent budget. They do not prune evidence or scan user folders. A preserved stale lock or exhausted budget blocks further capture; retain the existing evidence and use a clean verified public package. Byte/operation limits are not a hard deadline against stalled OS storage. Missing Python or an untrusted bootstrap can make capture unavailable. No fallback changes protections or executes a damaged helper.

## Release and evidence

Version `69.99-public.1`. Existing public title, repository URL, execution namespace, canonical main/Export BAT names, MIT license and third-party notices are retained. The active tree is replaced; historical commits, branches, tags, releases and cached copies are not erased or certified.

See [VALIDATION.md](VALIDATION.md), [PUBLIC_STERILIZATION_REPORT.md](PUBLIC_STERILIZATION_REPORT.md), [SECURITY.md](SECURITY.md), and [SBOM.cdx.json](SBOM.cdx.json). Local tests, GitHub-hosted CI, Norton status and live financial behavior are separate evidence. No profitability, antivirus clearance, or testing on the owner's computers is claimed.

## License

MIT; see [LICENSE](LICENSE). Copyright © 2026 Gateway Information Group LLC. All rights reserved.

Independent project; not affiliated with, endorsed by, or sponsored by Kalshi.
