import pandas as pd


def test_format_org_table_renames_columns():
    from src.ui.tables import format_org_table
    df = pd.DataFrame({
        "name": ["Acme"], "activityType": ["PRC"], "city": ["Berlin"],
        "country": ["DE"], "project_count": [5],
        "total_ec_contribution": [500000.0], "organizationURL": ["http://a.com"],
        "contactForm": [""], "SME": ["false"],
    })
    result = format_org_table(df)
    assert "Organisation" in result.columns
    assert "Projects" in result.columns
    assert "EC Contribution (EUR)" in result.columns
