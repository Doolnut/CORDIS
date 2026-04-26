import streamlit as st
import duckdb
from src.data.queries import get_filter_options

ACTIVITY_TYPE_LABELS = {
    "PRC": "Private company (PRC)",
    "HES": "Higher education (HES)",
    "REC": "Research organisation (REC)",
    "PUB": "Public body (PUB)",
    "OTH": "Other (OTH)",
}


def build_filters_dict(
    search: str | None,
    activity_types: list[str],
    countries: list[str],
    sme_only: bool,
    project_status: list[str],
    frameworks: list[str],
    policy_priorities: list[str],
    top_n: int | None,
) -> dict:
    return {
        "search": search or None,
        "activity_types": activity_types or None,
        "countries": countries or None,
        "sme_only": sme_only,
        "project_status": project_status or None,
        "frameworks": frameworks or None,
        "policy_priorities": policy_priorities or None,
        "top_n": top_n,
    }


def render_filters(conn: duckdb.DuckDBPyConnection) -> dict:
    opts = get_filter_options(conn)

    st.subheader("Search & Filter")

    search = st.text_input(
        "Research area / keyword",
        placeholder="e.g. quantum computing, clean hydrogen, biotech",
        help="Searches project keywords, objectives, and scientific vocabulary",
    )

    activity_types = st.multiselect(
        "Organisation type",
        options=list(ACTIVITY_TYPE_LABELS.keys()),
        format_func=lambda x: ACTIVITY_TYPE_LABELS.get(x, x),
        default=[],
    )

    countries = st.multiselect(
        "Country",
        options=opts["countries"],
        default=[],
    )

    sme_only = st.checkbox("SME only (small/medium enterprises)")

    project_status = st.multiselect(
        "Project status",
        options=opts["statuses"],
        default=[],
    )

    frameworks = st.multiselect(
        "Framework programme",
        options=opts["frameworks"],
        default=[],
    )

    policy_priorities = st.multiselect(
        "Policy priority tags",
        options=opts["policy_priorities"],
        default=[],
    )

    st.divider()
    top_n = st.number_input(
        "Max results (by project count)",
        min_value=10,
        max_value=10000,
        value=500,
        step=50,
        help="Limits all tabs to the top N organisations ranked by number of projects.",
    )

    return build_filters_dict(
        search, activity_types, countries, sme_only,
        project_status, frameworks, policy_priorities,
        int(top_n),
    )
