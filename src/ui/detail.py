import streamlit as st
import duckdb
import pandas as pd
from src.data.queries import get_org_detail, get_project_detail


def _fmt_euros(val) -> str:
    return f"€{val:,.0f}" if pd.notna(val) and val > 0 else "N/A"


def _cell(text: str) -> None:
    st.markdown(
        f"<span style='font-size:13px;color:#ede7de;line-height:2'>{text}</span>",
        unsafe_allow_html=True,
    )


def _clear():
    st.session_state["selected_org_id"] = None
    st.session_state["selected_project_id"] = None


def render_org_detail(conn: duckdb.DuckDBPyConnection, org_id: str) -> None:
    org_df, projects_df = get_org_detail(conn, org_id)

    if org_df.empty:
        st.warning("Organisation not found.")
        return

    org = org_df.iloc[0]

    if st.button("← Back to results", key="clear_org"):
        _clear()
        st.rerun()
    st.subheader(org["name"] or "Unknown Organisation")

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

    _HDR = ["Acronym", "Title", "Status", "Framework", "Role", "EC Contribution"]
    _W = [1, 5, 1, 1, 1, 2]

    hcols = st.columns(_W)
    for col, label in zip(hcols, _HDR):
        col.markdown(
            f"<p style='font-size:11px;font-weight:600;letter-spacing:0.04em;"
            f"text-transform:uppercase;color:#6b6258;margin:0 0 4px 0'>{label}</p>",
            unsafe_allow_html=True,
        )

    for i, row in projects_df.iterrows():
        rcols = st.columns(_W)
        if rcols[0].button(row["acronym"] or "—", key=f"proj_{i}", use_container_width=True):
            st.session_state["selected_project_id"] = row["project_id"]
            st.rerun()
        with rcols[1]: _cell(row.get("title") or "")
        with rcols[2]: _cell(row.get("status") or "")
        with rcols[3]: _cell(row.get("framework") or "")
        with rcols[4]: _cell(row.get("role") or "")
        with rcols[5]: _cell(_fmt_euros(row.get("ec_contribution")))


def render_project_detail(conn: duckdb.DuckDBPyConnection, project_id: str) -> None:
    project_df, orgs_df = get_project_detail(conn, project_id)

    if project_df.empty:
        st.warning("Project not found.")
        return

    p = project_df.iloc[0]

    col_back, col_close = st.columns([1, 1])
    if col_back.button("← Back to organisation", key="back_to_org"):
        st.session_state["selected_project_id"] = None
        st.rerun()
    if col_close.button("← Back to results", key="clear_proj"):
        _clear()
        st.rerun()
    st.subheader(f"{p['acronym']} — {p['title']}")

    c1, c2 = st.columns(2)
    c1.metric("Status", p["status"] or "N/A")
    c2.metric("Framework", p["framework"] or "N/A")
    c3, c4 = st.columns(2)
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

    _HDR = ["Organisation", "Country", "Type", "Role", "EC Contribution"]
    _W = [4, 1, 1, 1, 2]

    hcols = st.columns(_W)
    for col, label in zip(hcols, _HDR):
        col.markdown(
            f"<p style='font-size:11px;font-weight:600;letter-spacing:0.04em;"
            f"text-transform:uppercase;color:#6b6258;margin:0 0 4px 0'>{label}</p>",
            unsafe_allow_html=True,
        )

    for i, row in orgs_df.iterrows():
        rcols = st.columns(_W)
        if rcols[0].button(row["name"] or "(unnamed)", key=f"partner_{i}", use_container_width=True):
            st.session_state["selected_org_id"] = row["organisationid"]
            st.session_state["selected_project_id"] = None
            st.rerun()
        with rcols[1]: _cell(row.get("country") or "")
        with rcols[2]: _cell(row.get("type") or "")
        with rcols[3]: _cell(row.get("role") or "")
        with rcols[4]: _cell(_fmt_euros(row.get("ec_contribution")))
