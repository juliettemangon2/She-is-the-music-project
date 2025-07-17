from typing import List, Dict, Any

def assess_risks(
    metadata: Dict[str, Any],
    rights_summary: Dict[str, Any],
    derivatives: Dict[str, Any]
) -> List[str]:
    """
    Returns a list of risk flags based on metadata, copyright summary,
    and derivative works presence.

    Args:
        metadata: Track metadata dictionary.
        rights_summary: Output from resolve_rights (contains copyright_summary).
        derivatives: Output from derivative_mapper.

    Returns:
        List of risk warning strings.
    """
    risks = []

    copyright_summary = rights_summary.get("copyright_summary", {})
    expiry_year = copyright_summary.get("estimated_expiry_year")

    if expiry_year:
        if expiry_year - 2024 <= 5:
            risks.append(f"Copyright expires soon: {expiry_year}")

    publishers = rights_summary.get("publishers", [])
    if not publishers:
        risks.append("No publisher data available")

    songwriters = rights_summary.get("songwriters", [])
    if not songwriters:
        risks.append("No songwriter data available")

    if all(not derivatives.get(k) for k in ["samples", "covers", "remixes", "interpolations"]):
        risks.append("No derivatives found (samples, covers, remixes, interpolations)")

    return risks

if __name__ == "__main__":
    # Example test
    mock_metadata = {"title": "Test Song"}
    mock_rights_summary = {
        "copyright_summary": {
            "estimated_expiry_year": 2028,
            "rule_summary": {}
        },
        "publishers": [],
        "songwriters": []
    }
    mock_derivatives = {"samples": [], "covers": [], "remixes": [], "interpolations": []}

    risks = assess_risks(mock_metadata, mock_rights_summary, mock_derivatives)
    for risk in risks:
        print("RISK:", risk)
