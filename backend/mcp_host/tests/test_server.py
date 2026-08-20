import json

from mcp_host.server import get_internal_pricing_policy, mock_resource


def test_get_internal_pricing_policy_returns_valid_json():
    raw = get_internal_pricing_policy()
    data = json.loads(raw)

    assert data["currency"] == "USD"
    assert "billing_cycle" in data
    assert "tiers" in data
    assert len(data["tiers"]) == 3

    tier_names = [t["name"] for t in data["tiers"]]
    assert "Starter" in tier_names
    assert "Growth" in tier_names
    assert "Enterprise" in tier_names

    starter = next(t for t in data["tiers"] if t["name"] == "Starter")
    assert starter["price_per_month"] == 499
    assert starter["seats_included"] == 5
    assert len(starter["features"]) > 0

    growth = next(t for t in data["tiers"] if t["name"] == "Growth")
    assert growth["price_per_month"] == 1499
    assert growth["seats_included"] == 20

    enterprise = next(t for t in data["tiers"] if t["name"] == "Enterprise")
    assert enterprise["price_per_month"] == "custom"
    assert enterprise["seats_included"] == "unlimited"


def test_mock_resource_returns_empty_string():
    assert mock_resource() == ""
