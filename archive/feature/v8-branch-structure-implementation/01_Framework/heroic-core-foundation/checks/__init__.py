"""Pluggable Layer 0 checks for Heroic Core Foundation.

NOTE: this package is currently NOT imported by foundation.py or cli.py —
both implement their own inline copy of this logic (scan_epistemic_hygiene /
validate_geltungskategorien in foundation.py). The two implementations have
already drifted (different regex patterns). Treat this package as dead code
until it is actually wired in; do not assume editing it affects the CLI.
"""
from .geltung import check_geltung
from .hygiene import check_hygiene

__all__ = ["check_geltung", "check_hygiene"]
