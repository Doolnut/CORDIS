import streamlit as st
import pandas as pd
import duckdb
from src.data.queries import query_organizations

COLUMN_RENAME = {
    "name": "Organisation",
    "shortName": "Short Name",
    "activityType": "Type",
    "SME": "SME",
    "city": "City",
    "country": "Country",
    "project_count": "Projects",
    "total_ec_contribution": "EC Contribution (EUR)",
    "organizationURL": "Website",
}


def format_org_table(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["total_ec_contribution"] = df["total_ec_contribution"].apply(
        lambda x: f"{x:,.0f}" if pd.notna(x) and x > 0 else ""
    )
    return df.rename(columns=COLUMN_RENAME)


def render_results_table(conn: duckdb.DuckDBPyConnection, filters: dict) -> pd.DataFrame:
    with st.spinner("Querying..."):
        df = query_organizations(conn, filters)

    st.subheader(f"Results: {len(df):,} organisations")

    if df.empty:
        st.info("No organisations match the current filters.")
        return df

    display_cols = [
        "name", "activityType", "SME", "city", "country",
        "project_count", "total_ec_contribution", "organizationURL",
    ]
    available = [c for c in display_cols if c in df.columns]
    formatted = format_org_table(df[available])

    st.caption("Click a row to inspect an organisation.")
    event = st.dataframe(
        formatted,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="org_table",
        column_config={
            "Website": st.column_config.LinkColumn("Website"),
        },
    )
    if event.selection.rows:
        idx = event.selection.rows[0]
        st.session_state["selected_org_id"] = df.iloc[idx]["organisationid"]
        st.session_state["selected_project_id"] = None

    return df
