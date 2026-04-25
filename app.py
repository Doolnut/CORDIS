import streamlit as st
import os
from src.data.loader import create_connection, DataDirectoryError

st.set_page_config(
    page_title="CORDIS Explorer",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("CORDIS Explorer")
st.caption("Queensland Trade & Investment — EU Research Partnership Finder")

with st.sidebar:
    st.header("Data Configuration")
    default_data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data")
    data_path = st.text_input(
        "Path to CORDIS data folder",
        value=st.session_state.get("data_path", default_data_path),
        help="Folder containing project.csv, organization.csv, etc.",
    )
    load_btn = st.button("Load Data", type="primary")

if load_btn or "conn" not in st.session_state:
    if data_path:
        try:
            with st.spinner("Loading CORDIS data..."):
                st.session_state["conn"] = create_connection(data_path)
                st.session_state["data_path"] = data_path
            st.sidebar.success("Data loaded.")
        except DataDirectoryError as e:
            st.sidebar.error(str(e))
            st.stop()

if "conn" not in st.session_state:
    st.info("Configure the data folder path in the sidebar and click **Load Data**.")
    st.stop()

conn = st.session_state["conn"]
st.sidebar.divider()

# --- Filters (Task 5) ---
from src.ui.filters import render_filters
with st.sidebar:
    filters = render_filters(conn)

# --- Tabs (Tasks 6-10) ---
from src.ui.tables import render_results_table
from src.ui.export import df_to_csv_bytes

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Organisations", "Bar Chart", "Map", "Network", "SQL Query"]
)

with tab1:
    results_df = render_results_table(conn, filters)
    if not results_df.empty:
        st.download_button(
            "Export results as CSV",
            data=df_to_csv_bytes(results_df),
            file_name="cordis_organisations.csv",
            mime="text/csv",
        )

with tab2:
    from src.ui.charts import render_bar_chart
    render_bar_chart(conn, filters)

with tab3:
    from src.ui.map_view import render_map
    render_map(conn, filters)

with tab4:
    from src.ui.network import render_network
    render_network(conn, filters)

with tab5:
    from src.data.queries import run_raw_sql
    st.subheader("Raw SQL Query")
    st.caption("Tables: project, organization, euro_sci_voc, topics, legal_basis, policy_priorities, web_link")
    sql_input = st.text_area(
        "SQL",
        value=(
            "SELECT name, country, COUNT(DISTINCT projectID) AS projects\n"
            "FROM organization\n"
            "WHERE activityType = 'PRC'\n"
            "GROUP BY name, country\n"
            "ORDER BY projects DESC\n"
            "LIMIT 25"
        ),
        height=200,
    )
    if st.button("Run Query"):
        try:
            result_df = run_raw_sql(conn, sql_input)
            st.dataframe(result_df, use_container_width=True, hide_index=True)
            st.download_button(
                "Export query results as CSV",
                data=df_to_csv_bytes(result_df),
                file_name="cordis_query_results.csv",
                mime="text/csv",
            )
        except Exception as e:
            st.error(f"Query error: {e}")
