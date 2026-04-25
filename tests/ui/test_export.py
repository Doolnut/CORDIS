import pandas as pd


def test_df_to_csv_bytes():
    from src.ui.export import df_to_csv_bytes
    df = pd.DataFrame({"name": ["Acme"], "country": ["DE"]})
    result = df_to_csv_bytes(df)
    assert isinstance(result, bytes)
    assert b"Acme" in result
