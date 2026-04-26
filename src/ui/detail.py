import streamlit as st
import duckdb
import pandas as pd
from src.data.queries import get_org_detail, get_project_detail


def _fmt_euros(val) -> str:
    return f"€{val:,.0f}" if pd.notna(val) and val > 0 else "N/A"


def _clear():
    st.session_state["selected_org_id"] = None
    st.session_state["selected_project_id"] = None


def render_org_detail(conn: duckdb.DuckDBPyConnection, org_id: str) -> None:
    org_df, projects_df = get_org_detail(conn, org_id)

    if org_df.empty:
        st.warning("Organisation not found.")
        return

    org = org_df.iloc[0]

    col_title, col_clear = st.columns([6, 1])
    col_title.subheader(org["name"] or "Unknown Organisation")
    if col_clear.button("Clear", key="clear_org"):
        _clear()
        st.rerun()

    c1, c2, c3 = st.columns(3)
    c1.metric("Projects", int(org["project_count"]))
    c2.metric("Total EC Funding", _fmt_euros(org["total_ec_contribution"]))
    c3.metric("Country", org["country"] or "N/A")

    with st.expander("Organisation info"):
        for label, val in [
            ("Short name", org.get("short_name")),
            ("Type", org.get("activity_type")),
            ("SME", org.get("sme")),
            ("City", org.get("city")),
            ("Postcode", org.get("postcode")),
            ("Street", org.get("street")),
        ]:
            if val and str(val).strip():
                st.write(f"**{label}:** {val}")
        url = org.get("url")
        if url and str(url).strip():
            st.write(f"**Website:** [{url}]({url})")
        contact = org.get("contact")
        if contact and str(contact).strip():
            st.write(f"**Contact:** [{contact}]({contact})")

    st.markdown("#### Projects")

    if projects_df.empty:
        st.info("No projects found.")
        return

    display = projects_df[
        ["acronym", "title", "status", "start_date", "end_date", "framework", "role", "ec_contribution"]
    ].copy()
    display["ec_contribution"] = display["ec_contribution"].apply(_fmt_euros)
    display.columns = ["Acronym", "Title", "Status", "Start", "End", "Framework", "Role", "EC Contribution"]

    st.caption("Click a row to view project details.")
    event = st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="project_table",
    )
    if event.selection.rows:
        idx = event.selection.rows[0]
        st.session_state["selected_project_id"] = projects_df.iloc[idx]["project_id"]
        st.rerun()


def render_project_detail(conn: duckdb.DuckDBPyConnection, project_id: str) -> None:
    project_df, orgs_df = get_project_detail(conn, project_id)

    if project_df.empty:
        st.warning("Project not found.")
        return

    p = project_df.iloc[0]

    col_back, col_title, col_clear = st.columns([1, 5, 1])
    if col_back.button("Back to org", key="back_to_org"):
        st.session_state["selected_project_id"] = None
        st.rerun()
    col_title.subheader(f"{p['acronym']} — {p['title']}")
    if col_clear.button("Clear", key="clear_proj"):
        _clear()
        st.rerun()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Status", p["status"] or "N/A")
    c2.metric("Framework", p["framework"] or "N/A")
    c3.metric("EC Max Contribution", _fmt_euros(p["ec_max_contribution"]))
    c4.metric("Total Cost", _fmt_euros(p["total_cost"]))

    start = str(p.get("start_date", ""))[:10]
    end = str(p.get("end_date", ""))[:10]
    st.write(f"**Period:** {start} to {end}")

    if p.get("funding_scheme"):
        st.write(f"**Funding scheme:** {p['funding_scheme']}")
    if p.get("keywords"):
        st.write(f"**Keywords:** {p['keywords']}")
    if p.get("topics"):
        st.write(f"**Topics:** {p['topics']}")

    if p.get("objective"):
        with st.expander("Objective", expanded=True):
            st.write(p["objective"])

    st.markdown("#### Partner organisations")

    if orgs_df.empty:
        st.info("No organisations found.")
        return

    display = orgs_df[["name", "country", "type", "role", "city", "ec_contribution", "url"]].copy()
    display["ec_contribution"] = display["ec_contribution"].apply(_fmt_euros)
    display.columns = ["Organisation", "Country", "Type", "Role", "City", "EC Contribution", "Website"]

    st.caption("Click a row to inspect that organisation.")
    event = st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="partner_table",
        column_config={"Website": st.column_config.LinkColumn("Website")},
    )
    if event.selection.rows:
        idx = event.selection.rows[0]
        st.session_state["selected_org_id"] = orgs_df.iloc[idx]["organisationid"]
        st.session_state["selected_project_id"] = None
        st.rerun()
