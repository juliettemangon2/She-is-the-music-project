import os
import json
import datetime
from typing import Any, Dict, Optional

# ─── Load grouped rules from JSON ─────────────────────────────────────────────
_RULES_PATH = os.path.join(os.path.dirname(__file__), "copyright_rules.json")
with open(_RULES_PATH, "r", encoding="utf-8") as _f:
    RULE_ENTRIES = json.load(_f)


def estimate_copyright_status(
    spotify_track: Optional[Dict[str, Any]],
    release_year: int,
    author_death_year: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Estimates copyright status and expiry based on grouped country rules.

    Args:
        spotify_track: Raw Spotify track JSON (for available_markets/restrictions).
        release_year: Year of first publication.
        author_death_year: (Unused with current JSON, kept for future extension).

    Returns:
        {
          "copyright_status": "Protected"|"Public Domain",
          "estimated_expiry_year": int,
          "rule_summary": { country: {expiry_year, status, rule, source} },
          "legal_source": { country: source },
          "available_markets": [...],
          "restrictions": {...} or None
        }
    """
    current_year = datetime.datetime.now().year
    summary: Dict[str, Dict[str, Any]] = {}
    overall_protected = False
    earliest_expiry = float("inf")

    for entry in RULE_ENTRIES:
        duration = entry["duration_years"]
        rule_text = entry["rule"]
        source_url = entry["source"]
        for country in entry["countries"]:
            expiry = release_year + duration
            status = "Public Domain" if expiry <= current_year else "Protected"
            if status == "Protected":
                overall_protected = True

            summary[country] = {
                "expiry_year": expiry,
                "status": status,
                "rule": rule_text,
                "source": source_url,
            }
            if expiry < earliest_expiry:
                earliest_expiry = expiry

    return {
        "copyright_status": "Protected" if overall_protected else "Public Domain",
        "estimated_expiry_year": int(earliest_expiry),
        "rule_summary": summary,
        "legal_source": {c: info["source"] for c, info in summary.items()},
        "available_markets": spotify_track.get("available_markets") if spotify_track else None,
        "restrictions": spotify_track.get("restrictions") if spotify_track else None,
    }


# ─── Simple CLI for testing ───────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    import json as _json

    if len(sys.argv) < 2:
        print("Usage: python copyright_utils.py <release_year> [<market1> <market2> ...]")
        sys.exit(1)

    release_year = int(sys.argv[1])
    mock_track = {
        "available_markets": sys.argv[2:] if len(sys.argv) > 2 else [],
        "restrictions": None
    }

    result = estimate_copyright_status(mock_track, release_year)
    print(_json.dumps(result, indent=2))
