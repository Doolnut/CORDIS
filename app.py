import streamlit as st
import os
from src.data.loader import create_connection, build_summary_tables, DataDirectoryError

st.set_page_config(
    page_title="CORDIS Explorer",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.html("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&family=DM+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  /* Design tokens */
  :root {
    --navy:         #8aafd4;
    --navy-light:   #a8c4e0;
    --navy-dim:     #1e2b3d;
    --camel:        #c4a882;
    --camel-dim:    #2e2618;
    --positive:     #7aad82;
    --positive-dim: #1a2e1d;
    --warning:      #c4a055;
    --warning-dim:  #2e2410;
    --negative:     #c47a70;
    --negative-dim: #2e1a18;
    --border:       #342f29;
    --text-2:       #a89f93;
    --text-3:       #6b6258;
    --surface-raised: #242019;
  }

  /* Fonts */
  html, body, [class*="css"], .stApp, .stMarkdown, p, li, label,
  .stButton button, .stTextInput input, .stSelectbox, .stMultiSelect,
  .stNumberInput input, .stDataFrame, [data-testid="stMetricValue"],
  [data-testid="stMetricLabel"] {
    font-family: 'DM Sans', system-ui, sans-serif !important;
  }
  /* Protect icon fonts from the override above */
  .material-icons, .material-icons-outlined,
  .material-symbols-outlined, .material-symbols-rounded {
    font-family: 'Material Icons', 'Material Symbols Outlined', 'Material Symbols Rounded' !important;
  }
  h1, h2, h3,
  [data-testid="stHeadingWithActionElements"] h1,
  [data-testid="stHeadingWithActionElements"] h2,
  [data-testid="stHeadingWithActionElements"] h3 {
    font-family: 'Cormorant Garamond', Georgia, serif !important;
    font-weight: 300 !important;
    letter-spacing: -0.01em;
  }
  .stTextArea textarea {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
    line-height: 1.8 !important;
  }

  /* Metric cards */
  [data-testid="stMetric"] {
    background: var(--surface-raised);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 12px 16px;
  }
  [data-testid="stMetricLabel"] {
    font-size: 11px !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em !important;
    text-transform: uppercase;
    color: var(--text-3) !important;
  }
  [data-testid="stMetricValue"] {
    font-size: 26px !important;
    font-weight: 400 !important;
    line-height: 1.1 !important;
  }

  /* Tab bar */
  .stTabs [data-baseweb="tab-list"] {
    border-bottom: 1px solid var(--border) !important;
    gap: 0 !important;
  }
  .stTabs [data-baseweb="tab"] {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 10px 20px !important;
    color: var(--text-3) !important;
    border-bottom: 2px solid transparent !important;
  }
  .stTabs [aria-selected="true"] {
    color: #ede7de !important;
    border-bottom-color: var(--navy) !important;
  }

  /* Sidebar header */
  .stSidebar h2, .stSidebar h3 {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 600 !important;
  }

  /* Buttons */
  .stButton > button {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    border-radius: 5px !important;
    border: 1px solid var(--border) !important;
    transition: all 0.15s !important;
  }
  .stButton > button[kind="primary"] {
    background: var(--navy) !important;
    border-color: var(--navy) !important;
    color: #131110 !important;
  }
  .stButton > button[kind="primary"]:hover {
    background: var(--navy-light) !important;
    border-color: var(--navy-light) !important;
  }

  /* Inputs */
  .stTextInput input, .stNumberInput input, .stTextArea textarea {
    border-radius: 5px !important;
    border: 1px solid var(--border) !important;
    font-size: 13px !important;
  }
  .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
    border-color: var(--navy) !important;
    box-shadow: 0 0 0 1px var(--navy) !important;
  }

  /* Caption / help text */
  .stCaption, [data-testid="stCaptionContainer"] {
    font-size: 11px !important;
    color: var(--text-3) !important;
  }
</style>
""")

st.title("CORDIS Explorer")
st.caption("Queensland Trade & Investment · EU Research Partnership Finder")

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
            with st.status("Loading CORDIS data...", expanded=True) as data_status:
                st.write("Reading CSV files...")
                conn = create_connection(data_path)
                st.write("Building summary tables (this takes around 20 seconds)...")
                build_summary_tables(conn)
                st.session_state["conn"] = conn
                st.session_state["data_path"] = data_path
                data_status.update(label="Data loaded.", state="complete", expanded=False)
        except DataDirectoryError as e:
            st.sidebar.error(str(e))
            st.stop()

if "conn" not in st.session_state:
    st.info("Configure the data folder path in the sidebar and click **Load Data**.")
    st.stop()

conn = st.session_state["conn"]

if "selected_org_id" not in st.session_state:
    st.session_state["selected_org_id"] = None
if "selected_project_id" not in st.session_state:
    st.session_state["selected_project_id"] = None

st.sidebar.divider()

from src.ui.filters import render_filters
with st.sidebar:
    filters = render_filters(conn)

# --- View router ---
from src.ui.detail import render_org_detail, render_project_detail

if st.session_state.get("selected_project_id"):
    render_project_detail(conn, st.session_state["selected_project_id"])

elif st.session_state.get("selected_org_id"):
    render_org_detail(conn, st.session_state["selected_org_id"])

else:
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
        st.caption("Tables: project, organization, euro_sci_voc, topics, legal_basis, policy_priorities, web_link, pillars")
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
                st.dataframe(result_df, width="stretch", hide_index=True)
                st.download_button(
                    "Export query results as CSV",
                    data=df_to_csv_bytes(result_df),
                    file_name="cordis_query_results.csv",
                    mime="text/csv",
                )
            except Exception as e:
                st.error(f"Query error: {e}")
