# Changelog

## 69.99-public.1 — September 24, 2026

Added optional ordered evidence-quality review without changing the fixed public 10×1¢ contract or allowing review results to promote a model.

The complete active public tree is prepared from a reviewed allowlist. Original private uploads and previous public ZIPs remain unchanged. New support is independently runnable with the main entrypoint, planner and metadata removed; ZIP publication is atomic, capture is bounded, and capsule-only failure is explicit. Input symlinks/non-regular files and manifest identity/path contradictions are rejected. The redundant `scripts/verify_release.py` route is retired; use the canonical main `--verify` action.

Prior history is retained in Git, not reclassified as current verification. Stable public names, licenses, namespaces and Windows action names are preserved.

Copyright © 2026 Gateway Information Group LLC. All rights reserved.
