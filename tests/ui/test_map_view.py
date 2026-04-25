import pytest
import pandas as pd


def test_parse_geolocation():
    from src.ui.map_view import parse_geolocation
    df = pd.DataFrame({
        "name": ["Acme", "No Geo"],
        "geolocation": ["52.52,13.40", None],
        "project_count": [5, 3],
        "country": ["DE", "FR"],
    })
    result = parse_geolocation(df)
    assert result.iloc[0]["lat"] == pytest.approx(52.52)
    assert result.iloc[0]["lon"] == pytest.approx(13.40)
    assert pd.isna(result.iloc[1]["lat"])


def test_build_map_returns_figure():
    from src.ui.map_view import parse_geolocation, build_map
    df = pd.DataFrame({
        "name": ["Acme"],
        "geolocation": ["52.52,13.40"],
        "project_count": [5],
        "country": ["DE"],
        "activityType": ["PRC"],
    })
    df = parse_geolocation(df)
    fig = build_map(df)
    assert fig is not None
