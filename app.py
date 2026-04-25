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
    st.info("Coming soon")
