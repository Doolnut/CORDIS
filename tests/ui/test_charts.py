import pandas as pd


def test_build_bar_chart_returns_figure():
    from src.ui.charts import build_top_companies_chart
    df = pd.DataFrame({
        "name": ["A", "B", "C"],
        "project_count": [10, 7, 4],
        "total_ec_contribution": [1000000, 700000, 400000],
        "country": ["DE", "FR", "IT"],
    })
    fig = build_top_companies_chart(df, metric="project_count")
    assert fig is not None
    assert hasattr(fig, "data")
