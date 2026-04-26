import streamlit as st
import pandas as pd
import plotly.express as px
import duckdb
from src.data.queries import query_organizations


def parse_geolocation(df: pd.DataFrame) -> pd.DataFrame:
    def split_geo(val):
        if pd.isna(val) or not str(val).strip():
            return pd.NA, pd.NA
        cleaned = str(val).replace('"', '').strip()
        parts = cleaned.split(",")
        if len(parts) != 2:
            return pd.NA, pd.NA
        try:
            return float(parts[0]), float(parts[1])
        except ValueError:
            return pd.NA, pd.NA

    df = df.copy()
    coords = df["geolocation"].apply(split_geo)
    df["lat"] = coords.apply(lambda x: x[0])
    df["lon"] = coords.apply(lambda x: x[1])
    return df


def build_map(df: pd.DataFrame):
    df = df.dropna(subset=["lat", "lon"])
    fig = px.scatter_geo(
        df,
        lat="lat",
        lon="lon",
        color="country",
        size="project_count",
        hover_name="name",
        hover_data={"country": True, "project_count": True, "lat": False, "lon": False},
        custom_data=["organisationid"],
        title="Organisation Locations",
        projection="natural earth",
    )
    fig.update_geos(
        showcoastlines=True, coastlinecolor="Gray",
        showland=True, landcolor="LightGray",
        showocean=True, oceancolor="LightBlue",
        showlakes=True, lakecolor="LightBlue",
        showframe=False,
    )
    fig.update_layout(height=600)
    return fig


def render_map(conn: duckdb.DuckDBPyConnection, filters: dict) -> None:
    with st.spinner("Building map..."):
        df = query_organizations(conn, filters)

    if df.empty:
        st.info("No data for current filters.")
        return

    df = parse_geolocation(df)
    valid = df.dropna(subset=["lat", "lon"])
    st.caption(
        f"Showing {len(valid):,} of {len(df):,} organisations with geolocation data. "
        "Click a point to inspect an organisation."
    )
    fig = build_map(df)
    event = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="map_chart")
    if event.selection.points:
        org_id = event.selection.points[0]["customdata"][0]
        st.session_state["selected_org_id"] = org_id
        st.session_state["selected_project_id"] = None
