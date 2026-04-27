import streamlit as st
import pandas as pd
import duckdb
from src.data.queries import query_organizations

_COLS = [4, 1, 1, 1, 2]
_HEADERS = ["Organisation", "Type", "Country", "Projects", "EC Funding (EUR)"]
_PAGE_SIZE = 50


def _fmt_funding(val) -> str:
    return f"€{val:,.0f}" if pd.notna(val) and val > 0 else ""


def _cell(text: str) -> None:
    st.markdown(
        f"<span style='font-size:13px;color:#ede7de;line-height:2'>{text}</span>",
        unsafe_allow_html=True,
    )


def render_results_table(conn: duckdb.DuckDBPyConnection, filters: dict) -> pd.DataFrame:
    with st.spinner("Querying..."):
        df = query_organizations(conn, filters)

    st.subheader(f"Results: {len(df):,} organisations")

    if df.empty:
        st.info("No organisations match the current filters.")
        return df

    # Reset to page 0 when result count changes (filter applied)
    if st.session_state.get("_org_table_total") != len(df):
        st.session_state["org_table_page"] = 0
        st.session_state["_org_table_total"] = len(df)

    page = st.session_state.get("org_table_page", 0)
    total_pages = max(1, (len(df) + _PAGE_SIZE - 1) // _PAGE_SIZE)
    page = min(page, total_pages - 1)
    start = page * _PAGE_SIZE
    end = min(start + _PAGE_SIZE, len(df))
    page_df = df.iloc[start:end].reset_index(drop=True)

    # Header row
    hcols = st.columns(_COLS)
    for col, label in zip(hcols, _HEADERS):
        col.markdown(
            f"<p style='font-size:11px;font-weight:600;letter-spacing:0.04em;"
            f"text-transform:uppercase;color:#6b6258;margin:0 0 4px 0'>{label}</p>",
            unsafe_allow_html=True,
        )

    # Data rows — org name is a button; single click navigates to detail
    for i, row in page_df.iterrows():
        rcols = st.columns(_COLS)
        if rcols[0].button(
            row.get("name") or "(unnamed)",
            key=f"org_{start + i}",
            use_container_width=True,
        ):
            st.session_state["selected_org_id"] = df.iloc[start + i]["organisationid"]
            st.session_state["selected_project_id"] = None
            st.rerun()
        with rcols[1]: _cell(row.get("activityType") or "")
        with rcols[2]: _cell(row.get("country") or "")
        with rcols[3]: _cell(f"{int(row['project_count']):,}" if pd.notna(row.get("project_count")) else "")
        with rcols[4]: _cell(_fmt_funding(row.get("total_ec_contribution")))

    # Pagination controls
    if total_pages > 1:
        p1, p2, p3 = st.columns([1, 3, 1])
        if p1.button("← Prev", disabled=page == 0, key="org_prev"):
            st.session_state["org_table_page"] = page - 1
            st.rerun()
        p2.caption(f"Page {page + 1} of {total_pages}  ({start + 1}–{end} of {len(df):,})")
        if p3.button("Next →", disabled=page >= total_pages - 1, key="org_next"):
            st.session_state["org_table_page"] = page + 1
            st.rerun()

    return df
