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
    sci_voc_terms: list[str],
    activity_types: list[str],
    countries: list[str],
    sme_only: bool,
    project_status: list[str],
    frameworks: list[str],
    policy_priorities: list[str],
    legal_basis: list[str],
    pillar: list[str],
    top_n: int | None,
) -> dict:
    return {
        "search": search or None,
        "sci_voc_terms": sci_voc_terms or None,
        "activity_types": activity_types or None,
        "countries": countries or None,
        "sme_only": sme_only,
        "project_status": project_status or None,
        "frameworks": frameworks or None,
        "policy_priorities": policy_priorities or None,
        "legal_basis": legal_basis or None,
        "pillar": pillar or None,
        "top_n": top_n,
    }


def render_filters(conn: duckdb.DuckDBPyConnection) -> dict:
    opts = get_filter_options(conn)

    st.subheader("Search & Filter")

    top_n = st.number_input(
        "Max results (by project count)",
        min_value=10,
        max_value=10000,
        value=200,
        step=50,
        help="Limits all tabs to the top N organisations ranked by number of projects.",
    )

    st.divider()

    sci_voc_terms = st.multiselect(
        "EuroSciVoc topic",
        options=opts["sci_voc_terms"],
        default=[],
        placeholder="Type to search topics...",
        help="Filter by standardised research topic vocabulary. Select multiple to find orgs active in any of them.",
    )

    search = st.text_input(
        "Keyword search",
        placeholder="e.g. clean hydrogen, biotech",
        help="Searches project keywords and objectives (free text)",
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

    pillar = st.multiselect(
        "Horizon Europe pillar",
        options=opts["pillars"],
        default=[],
        help="Pillar I: Excellent Science · Pillar II: Global Challenges · Pillar III: Innovative Europe",
    )

    legal_basis = st.multiselect(
        "Legal basis (programme)",
        options=opts["legal_bases"],
        default=[],
        placeholder="e.g. European Research Council (ERC)",
        help="Filter by Horizon Europe programme. Top-level programmes only.",
    )

    return build_filters_dict(
        search, sci_voc_terms, activity_types, countries, sme_only,
        project_status, frameworks, policy_priorities, legal_basis, pillar,
        int(top_n),
    )
