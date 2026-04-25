def test_build_filters_returns_dict():
    from src.ui.filters import build_filters_dict
    result = build_filters_dict(
        search="quantum",
        activity_types=["PRC"],
        countries=["DE", "FR"],
        sme_only=True,
        project_status=["SIGNED"],
        frameworks=["HORIZON"],
        policy_priorities=["ai"],
    )
    assert result["search"] == "quantum"
    assert result["activity_types"] == ["PRC"]
    assert result["sme_only"] is True
    assert "ai" in result["policy_priorities"]
