import streamlit as st
import pandas as pd
import plotly.express as px
import duckdb
from src.data.queries import top_companies_by_project_count

METRIC_LABELS = {
    "project_count": "Number of Projects",
    "total_ec_contribution": "Total EC Contribution (EUR)",
}


def build_top_companies_chart(df: pd.DataFrame, metric: str):
    df = df.dropna(subset=[metric]).nlargest(25, metric)
    fig = px.bar(
        df,
        x=metric,
        y="name",
        orientation="h",
        color="country",
        custom_data=["organisationid"],
        title=f"Top 25 Organisations by {METRIC_LABELS[metric]}",
        labels={"name": "Organisation", metric: METRIC_LABELS[metric]},
        height=700,
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    return fig


def render_bar_chart(conn: duckdb.DuckDBPyConnection, filters: dict) -> None:
    metric = st.radio(
        "Rank by",
        options=["project_count", "total_ec_contribution"],
        format_func=lambda x: METRIC_LABELS[x],
        horizontal=True,
    )
    with st.spinner("Building chart..."):
        df = top_companies_by_project_count(conn, filters, limit=25)

    if df.empty:
        st.info("No data for current filters.")
        return

    fig = build_top_companies_chart(df, metric)
    st.caption("Click a bar to inspect an organisation.")
    event = st.plotly_chart(fig, width="stretch", on_select="rerun", key="bar_chart")
    if event.selection.points:
        org_id = event.selection.points[0]["customdata"][0]
        st.session_state["selected_org_id"] = org_id
        st.session_state["selected_project_id"] = None
